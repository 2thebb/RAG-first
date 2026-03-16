# -*- coding: utf-8 -*-
"""
Query History 탭 - 과거 쿼리 결과 열람
"""
import streamlit as st
import json
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import RESULTS_DIR

st.set_page_config(page_title="Query History", page_icon="🗂️", layout="wide")

def render():
    st.title("🗂️ Query History")
    st.caption("저장된 RAG 쿼리 결과 이력")

    # ── 현재 세션 히스토리 ─────────────────────────────────────────────
    session_history = st.session_state.get("history", [])

    tab1, tab2 = st.tabs(["현재 세션", "저장된 파일"])

    with tab1:
        if not session_history:
            st.info("이번 세션에서 실행된 쿼리가 없습니다. RAG Query 탭에서 쿼리를 실행하세요.")
        else:
            st.write(f"**{len(session_history)}개** 쿼리 실행됨")
            for i, item in enumerate(reversed(session_history)):
                with st.expander(f"[{item['timestamp']}] {item['query'][:80]}..."):
                    st.markdown(item["final"])
                    st.divider()
                    st.write("**참고 논문:**")
                    for ref in item.get("references", [])[:5]:
                        st.write(f"  [{ref['rank']}] {ref['title']} (score: {ref['score']:.3f})")

            # 전체 내보내기
            if st.button("📥 세션 히스토리 JSON 다운로드"):
                st.download_button(
                    label="다운로드",
                    data=json.dumps(session_history, ensure_ascii=False, indent=2),
                    file_name=f"rag_history_{int(time.time())}.json",
                    mime="application/json",
                )

    with tab2:
        if not RESULTS_DIR.exists():
            st.warning(f"결과 폴더가 없습니다: `{RESULTS_DIR}`")
        else:
            result_files = sorted(RESULTS_DIR.glob("result_*.json"), reverse=True)
            if not result_files:
                st.info("저장된 결과 파일이 없습니다.")
            else:
                st.write(f"**{len(result_files)}개** 파일 발견")
                selected = st.selectbox(
                    "파일 선택",
                    options=result_files,
                    format_func=lambda p: p.name,
                )
                if selected:
                    data = json.loads(selected.read_text(encoding="utf-8"))
                    st.subheader("쿼리")
                    st.text(data.get("query", "")[:500])
                    st.subheader("최종 답변")
                    st.markdown(data.get("final_response", ""))
                    st.subheader("참고 논문")
                    for ref in data.get("references", [])[:10]:
                        st.write(f"  [{ref['rank']}] {ref['title']} (score: {ref['score']:.3f})")


render()
