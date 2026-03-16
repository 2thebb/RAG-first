# NRR Literature Hub

NO3RR(질산 환원 반응) 논문 데이터셋을 위한 RAG 기반 웹 인터페이스.

## 구조

```
NRR-webpage/
├── app.py              # 메인 진입점
├── config.py           # 데이터 경로 및 모델 설정 ← 여기서 경로 수정
├── requirements.txt
└── pages/
    ├── 01_overview.py       # 데이터셋 통계 대시보드
    ├── 02_paper_search.py   # 논문 검색/목록
    ├── 03_rag_query.py      # RAG 파이프라인 실행
    └── 04_query_history.py  # 쿼리 이력
```

## 설치 및 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. config.py 수정 - BASE_DIR을 실제 데이터 경로로 변경
#    예: BASE_DIR = Path(r"C:\Users\Park Sangyeop\Documents\GitHub\openscholar_rag")

# 3. 실행
cd NRR-webpage
streamlit run app.py
```

## 데이터 경로 설정 (`config.py`)

현재 스크립트(`run_pipeline.py`)에서 사용하는 경로와 동일하게 설정:
- `BASE_DIR` → `openscholar_rag` 폴더 위치
- 그 안에 `index/faiss.index`, `index/corpus.json`이 있어야 합니다

## 기능

| 탭 | 설명 |
|---|---|
| Overview | 논문 수, 연도별/소스별 분포 차트 |
| Paper Search | 제목 키워드 검색, 연도 필터, PDF 다운로드 |
| RAG Query | FAISS 검색 → 초안 → 피드백 → 최종 답변 파이프라인 |
| Query History | 세션 이력 및 저장된 JSON 결과 열람 |
