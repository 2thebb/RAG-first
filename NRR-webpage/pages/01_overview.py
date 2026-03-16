# -*- coding: utf-8 -*-
"""
Overview 탭 - 논문 데이터셋 통계 대시보드
"""
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import CORPUS_FILE

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

@st.cache_data
def load_corpus():
    if not CORPUS_FILE.exists():
        return None
    with open(CORPUS_FILE, encoding="utf-8") as f:
        return json.load(f)

def render():
    st.title("📊 Overview")
    st.caption("NRR 논문 데이터셋 통계")

    corpus = load_corpus()

    if corpus is None:
        st.warning(f"corpus.json을 찾을 수 없습니다: `{CORPUS_FILE}`\n\n`config.py`에서 경로를 설정하세요.")
        _render_demo()
        return

    # ── 기본 통계 ────────────────────────────────────────────────────
    papers = {}
    for item in corpus:
        pid = item.get("paperId", "unknown")
        if pid not in papers:
            papers[pid] = item

    total_chunks   = len(corpus)
    total_papers   = len(papers)
    pdf_chunks     = sum(1 for c in corpus if c.get("source") == "pdf")
    abst_chunks    = total_chunks - pdf_chunks
    pdf_papers     = sum(1 for p in papers.values() if p.get("source") == "pdf")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 논문 수", f"{total_papers:,}")
    col2.metric("PDF 보유 논문", f"{pdf_papers:,}")
    col3.metric("총 청크 수", f"{total_chunks:,}")
    col4.metric("PDF 청크 / Abstract 청크", f"{pdf_chunks:,} / {abst_chunks:,}")

    st.divider()

    # ── 연도별 분포 ───────────────────────────────────────────────────
    years = []
    for p in papers.values():
        y = p.get("year") or p.get("publicationDate", "")
        if y:
            try:
                years.append(int(str(y)[:4]))
            except ValueError:
                pass

    if years:
        year_df = pd.Series(years).value_counts().sort_index().reset_index()
        year_df.columns = ["year", "count"]
        fig_year = px.bar(
            year_df, x="year", y="count",
            title="연도별 논문 수",
            color_discrete_sequence=["#2196F3"],
            labels={"year": "출판 연도", "count": "논문 수"},
        )
        fig_year.update_layout(height=320)
        st.plotly_chart(fig_year, use_container_width=True)

    # ── 소스 유형 파이 차트 ───────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        source_df = pd.DataFrame(
            {"유형": ["PDF 청크", "Abstract 청크"], "수": [pdf_chunks, abst_chunks]}
        )
        fig_pie = px.pie(source_df, names="유형", values="수", title="청크 소스 유형",
                         color_discrete_sequence=["#4CAF50", "#FF9800"])
        fig_pie.update_layout(height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        # 청크당 텍스트 길이 분포
        lengths = [len(c.get("text", "")) for c in corpus]
        fig_hist = px.histogram(
            x=lengths, nbins=50,
            title="청크 텍스트 길이 분포",
            labels={"x": "텍스트 길이 (chars)", "y": "청크 수"},
            color_discrete_sequence=["#9C27B0"],
        )
        fig_hist.update_layout(height=320)
        st.plotly_chart(fig_hist, use_container_width=True)


def _render_demo():
    """데이터 없을 때 데모 화면"""
    st.info("아래는 데이터 연결 시 표시될 데모 레이아웃입니다.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 논문 수", "~2,000")
    col2.metric("PDF 보유 논문", "~2,000")
    col3.metric("총 청크 수", "~40,000")
    col4.metric("PDF / Abstract", "~30,000 / ~10,000")
    st.caption("실제 데이터가 연결되면 통계가 자동으로 계산됩니다.")


render()
