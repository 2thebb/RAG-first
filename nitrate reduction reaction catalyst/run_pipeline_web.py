# -*- coding: utf-8 -*-
"""
Hybrid RAG + Web Search Pipeline
흐름: FAISS 검색 -> 초안 -> 자기피드백 -> 웹검색(RETRIEVE 쿼리 기반) -> 최종 답변
"""
import sys, json, re, time
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from duckduckgo_search import DDGS

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR        = Path("./openscholar_rag")
INDEX_DIR       = BASE_DIR / "index"
RESULTS_DIR     = BASE_DIR / "results"
INDEX_FILE      = INDEX_DIR / "faiss.index"
RETRIEVER_MODEL = "OpenSciLM/OpenScholar_Retriever"
OPENAI_API_KEY  = "YOUR_OPENAI_API_KEY"
MODEL           = "gpt-4.1"
TOP_K           = 15

client = OpenAI(api_key=OPENAI_API_KEY)

# ── 인덱스 로드 ────────────────────────────────────────────────────────
print("인덱스 로드 중...")
faiss_index     = faiss.read_index(str(INDEX_FILE))
retriever_model = SentenceTransformer(RETRIEVER_MODEL)
corpus          = json.load(open(INDEX_DIR / "corpus.json", encoding="utf-8"))
print(f"벡터: {faiss_index.ntotal}개 / 청크: {len(corpus)}개")

# ── FAISS 검색 ─────────────────────────────────────────────────────────
def retrieve(query, top_k=15):
    q_emb = retriever_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = faiss_index.search(q_emb.astype(np.float32), top_k * 10)
    pdf_results, abst_results, seen_ids = [], [], set()
    for score, idx in zip(scores[0], idxs[0]):
        item = corpus[idx].copy()
        item["score"] = float(score)
        pid = item["paperId"]
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        if item["source"] == "pdf":
            pdf_results.append(item)
        else:
            abst_results.append(item)
    pdf_take  = pdf_results[:top_k // 2]
    abst_take = abst_results[:top_k - len(pdf_take)]
    return sorted(pdf_take + abst_take, key=lambda x: x["score"], reverse=True)

def _format_passages(passages):
    return "\n\n".join(
        f"[{i+1}] Title: {p['title']}\n{p['text'][:600]}"
        for i, p in enumerate(passages)
    )

# ── 웹 검색 ────────────────────────────────────────────────────────────
def web_search(query, max_results=5):
    """DuckDuckGo로 최신 논문/자료 검색"""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(
                f"{query} site:scholar.google.com OR site:nature.com OR "
                f"site:science.org OR site:acs.org OR site:wiley.com OR "
                f"site:rsc.org OR site:arxiv.org electrochemistry catalyst",
                max_results=max_results
            ):
                results.append({
                    "title": r.get("title", ""),
                    "url":   r.get("href", ""),
                    "body":  r.get("body", "")[:400]
                })
        return results
    except Exception as e:
        print(f"  [Web Search Error] {e}")
        return []

def format_web_results(web_results, query):
    if not web_results:
        return f"[Web search for '{query}': no results]"
    formatted = f"[Web Search: '{query}']\n"
    for i, r in enumerate(web_results):
        formatted += f"  [{i+1}] {r['title']}\n      {r['url']}\n      {r['body']}\n\n"
    return formatted

# ── 시스템 프롬프트 ────────────────────────────────────────────────────
_SYSTEM_SYNTH = """You are a scientific literature synthesis assistant specializing
in materials science and energy research.
Given a research query and retrieved passages, synthesize a comprehensive,
citation-backed answer following these rules:
- Cite passages inline as [1], [2], etc., matching the provided list.
- Ground every claim in the retrieved evidence; do not fabricate facts.
- Use precise scientific terminology.
- Structure the response logically (mechanisms -> evidence -> implications)."""

_SYSTEM_FEEDBACK = """You are a rigorous scientific reviewer.
Analyze the draft response and identify specific improvements needed.
Focus on: missing mechanisms, weak citation support, incomplete coverage,
factual gaps, or unclear logic.
Output 2-3 numbered, actionable feedback items.
If a gap requires additional retrieval, append exactly:
  RETRIEVE: <concise search query>"""

_SYSTEM_FINAL = """You are a scientific literature synthesis assistant with access to both
retrieved academic literature (RAG) and supplementary web search results.
Revise the draft by:
1. Fully addressing each feedback point using RAG passages where available.
2. Incorporating relevant findings from web search results to fill gaps,
   clearly marking web-sourced information as [Web: title/source].
3. Preserving all valid citations from the draft.
4. Maintaining rigorous, precise scientific language throughout."""

# ── 메인 파이프라인 ────────────────────────────────────────────────────
RESEARCH_QUERY = """
You are an expert electrochemist and materials scientist specializing in \
electrocatalytic nitrogen chemistry. Answer the following structured query \
using only the provided retrieved literature. Your final output must \
synthesize across all three sections to produce actionable research \
recommendations.

[SECTION 1 — Reaction Landscape]
In the electrochemical nitrate reduction reaction (NO3RR), comprehensively \
map the product distribution and reaction pathways. Address:
  (a) All identified nitrogen-containing products (NH3, N2, NO2-, N2O, \
      NH2OH, etc.) and their faradaic efficiency ranges across catalyst classes,
  (b) Key reaction intermediates (*NO3, *NO2, *NO, *NH, *NH2) and the \
      mechanistic branching points that determine NH3 vs. N2 selectivity,
  (c) Electrolyte and potential-dependent factors that shift product distribution.

[SECTION 2 — Catalyst Benchmarking]
Survey the most extensively studied electrocatalyst systems for NO3RR-to-NH3. \
For each major class (Cu-based, Fe-based, Ru SACs, bimetallic alloys, \
transition metal oxides/nitrides), extract:
  (a) Best-reported NH3 yield rate, faradaic efficiency, and operating potential,
  (b) Proposed active sites and rate-limiting steps,
  (c) Known degradation mechanisms and stability limitations,
  (d) Electronic or geometric descriptors correlated with high performance.

[SECTION 3 — Machine Learning-Driven Catalyst Discovery]
Identify studies applying machine learning to NRR or NO3RR catalyst \
screening or optimization WITHOUT DFT-computed features as primary inputs. \
Specifically retrieve:
  (a) ML architectures and training data sources,
  (b) Feature engineering strategies based on tabulated elemental/experimental properties,
  (c) Experimental validations of ML predictions,
  (d) Reported limitations and dataset bottlenecks.

[SYNTHESIS TASK — Research Gap Analysis & Composition Recommendation]
Based exclusively on the evidence retrieved in Sections 1-3:
  1. Identify three under-explored catalyst compositions with promising potential.
  2. Explain the mechanistic rationale for each.
  3. Highlight unsolved selectivity challenges and whether ML has targeted them.
  4. Propose one high-priority experiment per gap.

Format final synthesis as:
  - Gap 1 | Candidate composition | Mechanistic rationale | Suggested experiment
  - Gap 2 | ...
  - Gap 3 | ...
"""

print(f"\n{'='*65}")
print("  HYBRID RAG + WEB SEARCH PIPELINE")
print('='*65)

# Step 1 — FAISS 검색
print("\n[1/5] FAISS 검색 중...")
passages = retrieve(RESEARCH_QUERY, top_k=TOP_K)
print(f"      {len(passages)}개 패시지 검색됨")

# Step 2 — 초안 생성
print("[2/5] 초안 생성 중...")
context = _format_passages(passages)
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_SYNTH},
        {"role": "user",   "content": f"Research Query:\n{RESEARCH_QUERY}\n\nRetrieved Passages:\n{context}\n\nSynthesize a comprehensive answer."},
    ],
    temperature=0.7,
    max_tokens=6000,
)
draft = resp.choices[0].message.content
print(f"      초안: {len(draft.split())} words")

# Step 3 — 자기 피드백
print("[3/5] 자기 피드백 생성 중...")
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_FEEDBACK},
        {"role": "user",   "content": f"Original Query:\n{RESEARCH_QUERY}\n\nDraft Response:\n{draft}\n\nAvailable Passages:\n{context}\n\nProvide specific feedback:"},
    ],
    temperature=0.3,
    max_tokens=800,
)
feedback = resp.choices[0].message.content
print(f"\n  Feedback:\n{feedback}\n")

# Step 4 — 피드백 기반 웹 검색
print("[4/5] 웹 검색으로 최신 정보 보완 중...")
retrieve_queries = re.findall(r"RETRIEVE:\s*(.+)", feedback, re.IGNORECASE)

# 쿼리가 없어도 핵심 주제로 기본 웹 검색 실행
if not retrieve_queries:
    retrieve_queries = [
        "NO3RR electrocatalyst NH3 selectivity mechanism 2024 2025",
        "machine learning nitrate reduction catalyst screening experimental 2024",
        "dual single atom catalyst NO3RR ammonia 2024 2025"
    ]
else:
    # RETRIEVE 쿼리에 연도 추가해서 최신 논문 우선 검색
    retrieve_queries = [q + " 2024 2025" for q in retrieve_queries]

all_web_context = ""
for q in retrieve_queries:
    print(f"  -> 웹 검색: '{q}'")
    web_results = web_search(q, max_results=5)
    web_context = format_web_results(web_results, q)
    all_web_context += web_context + "\n"
    print(f"     {len(web_results)}건 수집")

# Step 5 — 웹 결과 통합 최종 답변
print("[5/5] 웹 정보 통합하여 최종 답변 생성 중...")
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_FINAL},
        {"role": "user",   "content": (
            f"Original Query:\n{RESEARCH_QUERY}\n\n"
            f"Draft Response:\n{draft}\n\n"
            f"Feedback to Address:\n{feedback}\n\n"
            f"RAG Passages:\n{context}\n\n"
            f"Supplementary Web Search Results:\n{all_web_context}\n\n"
            "Provide the final, comprehensive revised response incorporating both sources:"
        )},
    ],
    temperature=0.7,
    max_tokens=10000,
)
final = resp.choices[0].message.content

print(f"\n{'='*65}")
print("  FINAL RESPONSE (RAG + Web)")
print('='*65)
print(final)

print(f"\n{'-'*65}")
print("  RAG REFERENCES")
print('-'*65)
for i, p in enumerate(passages):
    print(f"  [{i+1}] {p['title']} | score={p['score']:.3f} | {p['source']}")

print(f"\n{'-'*65}")
print("  WEB SEARCH QUERIES USED")
print('-'*65)
for q in retrieve_queries:
    print(f"  - {q}")

# 저장
out = {
    "query":          RESEARCH_QUERY,
    "draft":          draft,
    "feedback":       feedback,
    "web_queries":    retrieve_queries,
    "web_context":    all_web_context,
    "final_response": final,
    "references": [
        {"rank": i+1, "title": p["title"], "paperId": p["paperId"], "score": p["score"]}
        for i, p in enumerate(passages)
    ],
}
save_path = RESULTS_DIR / f"result_hybrid_{int(time.time())}.json"
json.dump(out, open(save_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n저장 완료 -> {save_path}")
