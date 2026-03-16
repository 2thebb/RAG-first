# -*- coding: utf-8 -*-
"""
RAG Query 탭 - FAISS 검색 + LLM 합성 파이프라인 UI
"""
import streamlit as st
import json
import time
import re
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import INDEX_FILE, CORPUS_FILE, RETRIEVER_MODEL, LLM_MODEL, TOP_K_DEFAULT

st.set_page_config(page_title="RAG Query", page_icon="🔬", layout="wide")

# ── 인덱스 로딩 (캐시) ───────────────────────────────────────────────
@st.cache_resource
def load_rag_resources():
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        if not INDEX_FILE.exists() or not CORPUS_FILE.exists():
            return None, None, None
        faiss_index = faiss.read_index(str(INDEX_FILE))
        model = SentenceTransformer(RETRIEVER_MODEL)
        corpus = json.load(open(CORPUS_FILE, encoding="utf-8"))
        return faiss_index, model, corpus
    except ImportError as e:
        return None, None, str(e)
    except Exception as e:
        return None, None, str(e)


def retrieve(query, faiss_index, model, corpus, top_k):
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = faiss_index.search(q_emb.astype(np.float32), top_k * 10)

    pdf_results, abst_results, seen_ids = [], [], set()
    for score, idx in zip(scores[0], idxs[0]):
        if idx < 0 or idx >= len(corpus):
            continue
        item = corpus[idx].copy()
        item["score"] = float(score)
        pid = item.get("paperId", str(idx))
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        if item.get("source") == "pdf":
            pdf_results.append(item)
        else:
            abst_results.append(item)

    pdf_take  = pdf_results[:top_k // 2]
    abst_take = abst_results[:top_k - len(pdf_take)]
    return sorted(pdf_take + abst_take, key=lambda x: x["score"], reverse=True)


def format_passages(passages):
    return "\n\n".join(
        f"[{i+1}] Title: {p['title']}\n{p['text'][:600]}"
        for i, p in enumerate(passages)
    )


def render():
    st.title("🔬 RAG Query")
    st.caption("FAISS 벡터 검색 + LLM 문헌 합성 파이프라인")

    # ── 사이드바 설정 ─────────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ 파이프라인 설정")
        openai_key = st.text_input("OpenAI API Key", type="password",
                                   help="sk-... 형태의 키를 입력하세요")
        top_k = st.slider("검색 패시지 수 (Top-K)", 5, 30, TOP_K_DEFAULT)
        use_web = st.checkbox("웹 검색 보완 활성화", value=False,
                               help="DuckDuckGo로 최신 논문 정보를 보완합니다 (duckduckgo-search 필요)")
        st.divider()
        st.caption("RAG 데이터 경로")
        st.code(str(INDEX_FILE), language=None)

    # ── 리소스 로딩 ──────────────────────────────────────────────────
    faiss_index, model, corpus_or_err = load_rag_resources()
    data_ready = faiss_index is not None and model is not None

    if not data_ready:
        if isinstance(corpus_or_err, str):
            st.error(f"RAG 리소스 로딩 실패: {corpus_or_err}")
        else:
            st.warning(
                "FAISS 인덱스 또는 corpus.json이 없습니다.\n\n"
                "`config.py`에서 `BASE_DIR` 경로를 올바르게 설정하세요.\n\n"
                "또는 `faiss`, `sentence-transformers` 패키지를 설치하세요:\n"
                "```\npip install faiss-cpu sentence-transformers\n```"
            )
        return

    corpus = corpus_or_err
    st.success(f"✅ 인덱스 로드 완료 — 벡터 {faiss_index.ntotal:,}개 / 청크 {len(corpus):,}개")

    # ── 쿼리 입력 ────────────────────────────────────────────────────
    st.subheader("연구 쿼리 입력")
    query = st.text_area(
        "질문을 입력하세요",
        height=120,
        placeholder="예: What are the most effective Cu-based catalysts for NO3RR to NH3 and what are their faradaic efficiencies?",
    )

    preset_col1, preset_col2, preset_col3 = st.columns(3)
    if preset_col1.button("🔖 반응 메커니즘"):
        query = "Explain the reaction mechanism of NO3RR including key intermediates and selectivity towards NH3 vs N2."
    if preset_col2.button("🔖 Cu 촉매 벤치마킹"):
        query = "Survey Cu-based electrocatalysts for NO3RR: best NH3 yield rate, faradaic efficiency, and operating potential."
    if preset_col3.button("🔖 ML 촉매 스크리닝"):
        query = "What ML approaches have been used for NO3RR catalyst discovery without DFT features? Include architectures and experimental validations."

    run_btn = st.button("🚀 파이프라인 실행", type="primary", disabled=not bool(query and openai_key))

    if not openai_key:
        st.info("사이드바에 OpenAI API Key를 입력하면 파이프라인을 실행할 수 있습니다.")

    if run_btn and query and openai_key:
        _run_pipeline(query, faiss_index, model, corpus, top_k, openai_key, use_web)


def _run_pipeline(query, faiss_index, model, corpus, top_k, openai_key, use_web):
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)

    _SYSTEM_SYNTH = (
        "You are a scientific literature synthesis assistant specializing in "
        "materials science and electrochemistry.\n"
        "Given a research query and retrieved passages, synthesize a comprehensive, "
        "citation-backed answer.\n"
        "- Cite passages inline as [1], [2], etc.\n"
        "- Ground every claim in the retrieved evidence.\n"
        "- Use precise scientific terminology.\n"
        "- Structure the response: mechanisms → evidence → implications."
    )
    _SYSTEM_FEEDBACK = (
        "You are a rigorous scientific reviewer. Analyze the draft and identify "
        "2-3 specific improvements needed.\n"
        "If additional retrieval is needed, append exactly: RETRIEVE: <search query>"
    )
    _SYSTEM_REVISE = (
        "You are a scientific literature synthesis assistant. Revise the draft by "
        "fully addressing each feedback point. Preserve valid citations. "
        "Maintain rigorous, precise scientific language."
    )

    with st.status("파이프라인 실행 중...", expanded=True) as status:
        # Step 1 — Retrieve
        st.write("**[1/4] FAISS 검색 중...**")
        passages = retrieve(query, faiss_index, model, corpus, top_k)
        st.write(f"  → {len(passages)}개 패시지 검색됨")

        # Step 2 — Draft
        st.write("**[2/4] 초안 생성 중...**")
        context = format_passages(passages)
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_SYNTH},
                {"role": "user",   "content": f"Query:\n{query}\n\nPassages:\n{context}\n\nSynthesize a comprehensive answer."},
            ],
            temperature=0.7, max_tokens=4000,
        )
        draft = resp.choices[0].message.content

        # Step 3 — Feedback
        st.write("**[3/4] 자기 피드백 생성 중...**")
        resp_fb = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_FEEDBACK},
                {"role": "user",   "content": f"Query:\n{query}\n\nDraft:\n{draft}\n\nPassages:\n{context}\n\nProvide feedback:"},
            ],
            temperature=0.3, max_tokens=600,
        )
        feedback = resp_fb.choices[0].message.content

        # Step 3b — 추가 FAISS 검색
        extra_match = re.search(r"RETRIEVE:\s*(.+)", feedback, re.IGNORECASE)
        if extra_match:
            extra_query = extra_match.group(1).strip()
            st.write(f"  → 추가 검색: `{extra_query}`")
            extra = retrieve(extra_query, faiss_index, model, corpus, 5)
            passages = passages + extra
            context = format_passages(passages)

        # Step 3c — 웹 검색 보완 (옵션)
        web_context = ""
        if use_web:
            st.write("**[3b] 웹 검색 보완 중...**")
            try:
                from duckduckgo_search import DDGS
                web_queries = re.findall(r"RETRIEVE:\s*(.+)", feedback, re.IGNORECASE)
                if not web_queries:
                    web_queries = [query[:100] + " 2024 2025"]
                for wq in web_queries[:2]:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(wq + " electrochemistry catalyst", max_results=4))
                    for r in results:
                        web_context += f"[Web] {r.get('title','')}: {r.get('body','')[:300]}\n\n"
                st.write(f"  → 웹 결과 {len(results)}건 수집")
            except Exception as e:
                st.write(f"  → 웹 검색 실패: {e}")

        # Step 4 — Final
        st.write("**[4/4] 최종 답변 생성 중...**")
        final_context = context
        if web_context:
            final_context += f"\n\n--- Supplementary Web Results ---\n{web_context}"
        resp_final = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_REVISE},
                {"role": "user",   "content": f"Query:\n{query}\n\nDraft:\n{draft}\n\nFeedback:\n{feedback}\n\nPassages:\n{final_context}\n\nProvide revised response:"},
            ],
            temperature=0.7, max_tokens=6000,
        )
        final = resp_final.choices[0].message.content
        status.update(label="✅ 완료!", state="complete")

    # ── 결과 표시 ────────────────────────────────────────────────────
    st.subheader("📋 최종 답변")
    st.markdown(final)

    with st.expander("💬 초안 (Draft)"):
        st.markdown(draft)

    with st.expander("🔍 피드백"):
        st.text(feedback)

    with st.expander(f"📚 참고 패시지 ({len(passages)}개)"):
        for i, p in enumerate(passages):
            st.write(f"**[{i+1}]** `score={p['score']:.3f}` | `{p.get('source','?')}` | {p.get('title','')}")
            st.caption(p.get("text", "")[:200] + "...")
            st.divider()

    # ── 세션 히스토리 저장 ────────────────────────────────────────────
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "final": final,
        "references": [{"rank": i+1, "title": p.get("title",""), "score": p["score"]} for i, p in enumerate(passages)],
    })


render()
