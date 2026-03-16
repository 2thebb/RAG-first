# -*- coding: utf-8 -*-
import sys, json, re, time
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from openai import OpenAI

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

# ── Retrieve ───────────────────────────────────────────────────────────
def retrieve(query, top_k=10):
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
    results   = sorted(pdf_take + abst_take, key=lambda x: x["score"], reverse=True)
    return results

def _format_passages(passages):
    return "\n\n".join(
        f"[{i+1}] Title: {p['title']}\n{p['text'][:600]}"
        for i, p in enumerate(passages)
    )

# ── 프롬프트 ───────────────────────────────────────────────────────────
_SYSTEM_SYNTH = """You are a scientific literature synthesis assistant specializing
in materials science and energy research.
Given a research query and retrieved passages, synthesize a comprehensive,
citation-backed answer following these rules:
- Cite passages inline as [1], [2], etc., matching the provided list.
- Ground every claim in the retrieved evidence; do not fabricate facts.
- Use precise scientific terminology.
- Structure the response logically (mechanisms → evidence → implications)."""

_SYSTEM_FEEDBACK = """You are a rigorous scientific reviewer.
Analyze the draft response and identify specific improvements needed.
Focus on: missing mechanisms, weak citation support, incomplete coverage,
factual gaps, or unclear logic.
Output 2-3 numbered, actionable feedback items.
If a gap requires additional retrieval, append exactly:
  RETRIEVE: <concise search query>"""

_SYSTEM_REVISE = """You are a scientific literature synthesis assistant.
Revise the draft by fully addressing each feedback point.
Preserve all valid citations from the draft.
Add new inline citations [n] only if the passage list supports them.
Maintain rigorous, precise scientific language."""

# ── 파이프라인 ─────────────────────────────────────────────────────────
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
  (d) Electronic or geometric descriptors (d-band center, coordination number, \
      *NO3 adsorption energy) correlated with high performance.

[SECTION 3 — Machine Learning-Driven Catalyst Discovery]
Identify studies applying machine learning to NRR or NO3RR catalyst \
screening or optimization WITHOUT DFT-computed features as primary inputs. \
Specifically retrieve:
  (a) ML architectures used (GNN, random forest, GPR, LLM-based), along with \
      their training data sources (experimental databases, literature mining, \
      materials repositories),
  (b) Feature engineering strategies based solely on tabulated elemental or \
      experimental properties (electronegativity, atomic radius, oxidation state, \
      measured overpotential),
  (c) Cases where ML predictions were validated experimentally, noting successes \
      and failures,
  (d) Reported limitations and dataset bottlenecks in current ML approaches.

[SYNTHESIS TASK — Research Gap Analysis & Composition Recommendation]
Based exclusively on the evidence retrieved in Sections 1-3, perform the \
following synthesis:
  1. Identify at least three under-explored catalyst compositions or structural \
     motifs that are predicted or implied to be promising but have not been \
     experimentally validated, citing the specific gap in the literature.
  2. For each candidate composition, explain the mechanistic rationale \
     (e.g., why a specific d-band filling or bimetallic synergy would suppress \
     N2 formation and favor NH3).
  3. Highlight which product selectivity challenges (from Section 1) remain \
     unsolved by the catalysts benchmarked in Section 2, and whether any ML \
     study (Section 3) has directly targeted those selectivity descriptors.
  4. Propose one high-priority experiment per gap — specifying catalyst \
     composition, synthesis strategy hint, and evaluation metric.

Format your final synthesis as:
  - Gap 1 | Candidate composition | Mechanistic rationale | Suggested experiment
  - Gap 2 | ...
  - Gap 3 | ...
"""

print(f"\n{'='*65}")
print(f"  QUERY: {RESEARCH_QUERY}")
print('='*65)

# Step 1 — Retrieve
print("\n[1/4] Retrieving passages...")
passages = retrieve(RESEARCH_QUERY, top_k=TOP_K)
print(f"      {len(passages)}개 패시지 검색됨")
for i, p in enumerate(passages):
    print(f"  [{i+1}] score={p['score']:.3f} | {p['source']:20s} | {p['title'][:55]}")

# Step 2 — Initial draft
print("\n[2/4] 초안 생성 중...")
context = _format_passages(passages)
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_SYNTH},
        {"role": "user",   "content": f"Research Query:\n{RESEARCH_QUERY}\n\nRetrieved Passages:\n{context}\n\nSynthesize a comprehensive, citation-backed answer."},
    ],
    temperature=0.7,
    max_tokens=6000,
)
draft = resp.choices[0].message.content
print(f"      초안: {len(draft.split())} words")

# Step 3 — Feedback
print("\n[3/4] 피드백 생성 중...")
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_FEEDBACK},
        {"role": "user",   "content": f"Original Query:\n{RESEARCH_QUERY}\n\nDraft Response:\n{draft}\n\nAvailable Passages:\n{context}\n\nProvide concise, specific feedback:"},
    ],
    temperature=0.3,
    max_tokens=800,
)
feedback = resp.choices[0].message.content
print(f"\n  Feedback:\n{feedback}\n")

# Step 3b — 추가 검색
extra_match = re.search(r"RETRIEVE:\s*(.+)", feedback, re.IGNORECASE)
if extra_match:
    extra_query = extra_match.group(1).strip()
    print(f"  -> 추가 검색: '{extra_query}'")
    extra = retrieve(extra_query, top_k=5)
    passages = passages + extra
    context  = _format_passages(passages)
    print(f"  -> 패시지 확장: {len(passages)}개")

# Step 4 — 최종 답변
print("[4/4] 최종 답변 생성 중...")
resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": _SYSTEM_REVISE},
        {"role": "user",   "content": f"Original Query:\n{RESEARCH_QUERY}\n\nDraft Response:\n{draft}\n\nFeedback to Address:\n{feedback}\n\nAvailable Passages:\n{context}\n\nProvide a revised, improved response:"},
    ],
    temperature=0.7,
    max_tokens=8000,
)
final = resp.choices[0].message.content

print(f"\n{'='*65}")
print("  FINAL RESPONSE")
print('='*65)
print(final)

print(f"\n{'-'*65}")
print("  REFERENCES")
print('-'*65)
for i, p in enumerate(passages):
    print(f"  [{i+1}] {p['title']} | score={p['score']:.3f} | {p['source']}")

# 저장
out = {
    "query": RESEARCH_QUERY,
    "draft": draft,
    "feedback": feedback,
    "final_response": final,
    "references": [
        {"rank": i+1, "title": p["title"], "paperId": p["paperId"], "score": p["score"]}
        for i, p in enumerate(passages)
    ],
}
save_path = RESULTS_DIR / f"result_{int(time.time())}.json"
json.dump(out, open(save_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n저장 완료 -> {save_path}")
