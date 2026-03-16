# -*- coding: utf-8 -*-
"""
NRR RAG Web App - Configuration
로컬 데이터 경로를 여기서 설정하세요.
"""
from pathlib import Path

# ── 데이터 경로 설정 ─────────────────────────────────────────────────────
# Windows 로컬 경로 예: r"C:\Users\Park Sangyeop\Documents\GitHub\openscholar_rag"
# Linux/Mac 경로 예: Path("/home/user/openscholar_rag")
BASE_DIR    = Path("./openscholar_rag")   # 앱 실행 위치 기준 상대 경로

INDEX_DIR   = BASE_DIR / "index"
RESULTS_DIR = BASE_DIR / "results"
PDF_DIR     = BASE_DIR / "pdfs"           # PDF 파일 저장 폴더 (있는 경우)

INDEX_FILE  = INDEX_DIR / "faiss.index"
CORPUS_FILE = INDEX_DIR / "corpus.json"
META_FILE   = INDEX_DIR / "metadata.json" # 논문 메타데이터 (선택)

# ── 모델 설정 ──────────────────────────────────────────────────────────
RETRIEVER_MODEL = "OpenSciLM/OpenScholar_Retriever"
TOP_K_DEFAULT   = 15

# ── LLM 설정 ──────────────────────────────────────────────────────────
LLM_MODEL = "gpt-4.1"   # OpenAI 모델명

# ── UI 설정 ───────────────────────────────────────────────────────────
APP_TITLE   = "NRR Literature Hub"
APP_ICON    = "⚗️"
THEME_COLOR = "#1a3a5c"
