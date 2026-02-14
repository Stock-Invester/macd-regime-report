# macd-regime-report

상태 머신 기반 MACD 리포트 엔진 MVP입니다.

## 구현 범위

- `(Ticker, 결과 문자열)` 입력으로 `rules.yaml` 자동 생성
- yfinance/FRED 데이터 기반 지표 평가
- SPX 게이트(`SPX_1M_MACD < SIGNAL` AND `RATE_CUT_EVENT`) 계산
- 종목별 IN/OUT 상태를 `state_store.json`에 저장/복원
- 실행마다 `report.csv` + 콘솔 markdown 테이블 출력

## rules.yaml 스키마(요약)

```yaml
schema_version: 1
rules:
  - ticker: AAPL
    raw_text: "매수 (3달봉) ..."
    entry:
      timeframe: "3M"
      signal:
        kind: macd_state | macd_hist_delta
        direction: macd_above_signal | increasing
      gate: []
      confirm:
        - kind: zqzmom_delta_positive
          timeframe: "1M"
    exit:
      timeframe: "1M"
      signal:
        kind: macd_state | macd_hist_delta
        direction: macd_below_signal | decreasing
      gate: [SPX_GATE_ON]
      confirm: []
```

## 설치

```bash
pip install -e .
```

## 사용법

1) 입력 CSV 준비 (`Ticker,Result` 컬럼 필수)

```csv
Ticker,Result
AAPL,"매수 (3달봉) / 매도 (1달봉) 침체 1달봉 ZQ"
MSFT,"매수 (2달봉) 오실 / 매도 (1달봉) 금리인하"
```

2) 규칙 생성

```bash
macd-regime build-rules --input-csv input.csv --output rules.yaml
```

3) 엔진 실행

```bash
macd-regime run --rules rules.yaml --state state_store.json --report report.csv
```

## 상태 머신 규칙

- `ExitPass=True`이면 항상 `NewPos=OUT`
- `PrevPos=OUT`은 `EntryPass=True`일 때만 `IN`으로 복귀
- 액션 매핑
  - OUT->IN: BUY
  - IN->OUT: SELL
  - IN->IN: HOLD
  - OUT->OUT: WAIT
