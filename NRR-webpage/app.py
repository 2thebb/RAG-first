# -*- coding: utf-8 -*-
"""
NRR Literature Hub - 메인 앱 진입점
실행: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="NRR Literature Hub",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚗️ NRR Literature Hub")
st.subheader("Nitrate Reduction Reaction — RAG 기반 문헌 분석 플랫폼")

st.markdown("""
이 플랫폼은 **NO3RR (Nitrate Reduction Reaction)** 관련 논문 데이터셋을 분석하고,
FAISS 벡터 검색과 LLM 합성을 통해 연구 질문에 답변합니다.

---

### 사용 방법

1. 왼쪽 사이드바에서 탭을 선택하세요
2. 시작 전 `config.py`에서 데이터 경로를 확인/수정하세요

---

### 탭 안내

| 탭 | 기능 |
|---|---|
| 📊 Overview | 논문 데이터셋 통계 대시보드 (연도별, 소스별 분포) |
| 📄 Paper Search | 논문 목록 검색 및 필터링, PDF 다운로드 |
| 🔬 RAG Query | FAISS 검색 + LLM 합성 파이프라인 실행 |
| 🗂️ Query History | 과거 쿼리 결과 열람 및 내보내기 |

---

### 빠른 시작

```bash
# 패키지 설치
pip install -r requirements.txt

# config.py에서 데이터 경로 설정 후 실행
streamlit run app.py
```

---
""")

st.info("👈 왼쪽 사이드바에서 탭을 선택하거나, 위 안내에 따라 시작하세요.")
