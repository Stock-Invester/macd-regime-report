# macd-regime-report

Ticker + 결과 문자열을 `rules.yaml`로 자동 변환하고, 상태 머신(IN/OUT)을 기반으로 일일/수시 리포트를 생성하는 엔진입니다.

## 구현 범위 (MVP)
- 문자열 파싱 -> `rules.yaml` 생성
- 임의 월봉(`1M~12M`) MACD/hist/ZQZMOM 계산
- SPX 게이트(`^GSPC` 월봉 MACD + FRED DFEDTARU rate cut 이벤트)
- 상태 저장(`state_store.csv`) 기반 상태 머신
- 결과 출력(`report.csv` + 콘솔 markdown table)

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

## 입력 포맷
`Ticker`, `Result` 컬럼을 가진 CSV.

예:
```csv
Ticker,Result
AAPL,"매수 (3달봉), 매도 (1달봉), 오실, 침체, 1달봉 ZQ"
MSFT,"매수 (2달봉), 매도 (1달봉), 금리인하"
```

## 1) rules.yaml 생성
```bash
python run_report.py build-rules --input ticker_results.csv --out rules.yaml
```

## 2) 리포트 실행
```bash
python run_report.py run-report --rules rules.yaml --state state_store.csv --out report.csv
```

## 상태 머신 규칙
- `ExitPass=True` -> 무조건 `OUT`
- `PrevPos=OUT`이면 `EntryPass=True`일 때만 `IN` 복귀
- 그 외는 이전 상태 유지

액션 매핑:
- OUT->IN = BUY
- IN->OUT = SELL
- IN->IN = HOLD
- OUT->OUT = WAIT

## 주요 파일
- `src/macd_regime/parser.py`: 결과 문자열 -> 룰 파싱
- `src/macd_regime/indicators.py`: MACD, histogram delta, ZQZMOM, k개월봉 리샘플링
- `src/macd_regime/data_sources.py`: yfinance/FRED 로더
- `src/macd_regime/engine.py`: SPX gate + 상태 머신 + report 생성
- `src/macd_regime/cli.py`: CLI 엔트리포인트
