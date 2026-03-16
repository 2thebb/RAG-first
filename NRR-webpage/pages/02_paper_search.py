# -*- coding: utf-8 -*-
"""
Paper Search 탭 - 논문 목록 검색 및 브라우저
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import CORPUS_FILE, PDF_DIR

st.set_page_config(page_title="Paper Search", page_icon="📄", layout="wide")

@st.cache_data
def load_papers():
    if not CORPUS_FILE.exists():
        return None
    with open(CORPUS_FILE, encoding="utf-8") as f:
        corpus = json.load(f)
    seen, papers = set(), []
    for item in corpus:
        pid = item.get("paperId", "")
        if pid and pid not in seen:
            seen.add(pid)
            papers.append({
                "paperId": pid,
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "source": item.get("source", ""),
                "abstract": item.get("text", "")[:300] if item.get("source") != "pdf" else "",
            })
    return papers

def render():
    st.title("📄 Paper Search")
    st.caption("수집된 논문 목록 검색 및 열람")

    papers = load_papers()

    if papers is None:
        st.warning(f"corpus.json을 찾을 수 없습니다: `{CORPUS_FILE}`\n\n`config.py`에서 경로를 설정하세요.")
        return

    df = pd.DataFrame(papers)

    # ── 검색/필터 UI ─────────────────────────────────────────────────
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        keyword = st.text_input("🔍 제목/키워드 검색", placeholder="예: copper nitrate reduction ammonia")
    with col2:
        source_filter = st.selectbox("소스 유형", ["전체", "pdf", "abstract"])
    with col3:
        year_min = int(df["year"].dropna().min()) if not df["year"].dropna().empty else 2015
        year_max = int(df["year"].dropna().max()) if not df["year"].dropna().empty else 2025
        year_range = st.slider("출판 연도", year_min, year_max, (year_min, year_max))

    # ── 필터 적용 ────────────────────────────────────────────────────
    filtered = df.copy()
    if keyword:
        mask = filtered["title"].str.contains(keyword, case=False, na=False)
        filtered = filtered[mask]
    if source_filter != "전체":
        filtered = filtered[filtered["source"] == source_filter]
    year_mask = (filtered["year"].fillna(0).astype(float) >= year_range[0]) & \
                (filtered["year"].fillna(9999).astype(float) <= year_range[1])
    filtered = filtered[year_mask]

    st.caption(f"검색 결과: **{len(filtered):,}** 편 (전체 {len(df):,} 편)")
    st.divider()

    # ── 결과 테이블 ──────────────────────────────────────────────────
    ROWS_PER_PAGE = 25
    total_pages = max(1, (len(filtered) - 1) // ROWS_PER_PAGE + 1)
    page = st.number_input("페이지", min_value=1, max_value=total_pages, value=1, step=1)
    start = (page - 1) * ROWS_PER_PAGE
    page_df = filtered.iloc[start:start + ROWS_PER_PAGE]

    for _, row in page_df.iterrows():
        with st.expander(f"**{row['title'] or '제목 없음'}** ({row['year'] or '연도 미상'}) | {row['source']}"):
            st.write(f"**Paper ID:** `{row['paperId']}`")
            if row["abstract"]:
                st.write(f"**Abstract 미리보기:** {row['abstract']}...")
            # PDF 파일이 있으면 링크 표시
            pdf_path = PDF_DIR / f"{row['paperId']}.pdf"
            if pdf_path.exists():
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=f.read(),
                        file_name=f"{row['paperId']}.pdf",
                        mime="application/pdf",
                        key=f"dl_{row['paperId']}",
                    )

    st.caption(f"페이지 {page} / {total_pages}")


render()
