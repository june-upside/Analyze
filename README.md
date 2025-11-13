# Kimchi Premium Analysis

김치프리미엄/역프리미엄과 업비트 핫월렛 입출금량 사이의 상관관계 분석 프로젝트

## 개요

이 프로젝트는 업비트의 USDT(Tron Network) 핫월렛 입출금량과 한국 암호화폐 시장의 김치프리미엄 간의 상관관계를 분석합니다.

- **분석 기간**: 최근 6개월
- **대상 코인**: BTC, ETH, USDT
- **비교 거래소**: 업비트 (한국) vs 바이낸스 (글로벌)
- **핫월렛 주소**: TVreyZvJWKmcpJGioTzJ81T1JMSXMZ3pV9 (Tron Network)

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 필요 패키지

- pandas: 데이터 처리
- requests: API 호출
- matplotlib & seaborn: 기본 차트
- plotly: 인터랙티브 차트
- scipy/numpy: 통계 분석
- yfinance: 환율 데이터 (Yahoo Finance)

## 사용 방법

### 방법 1: Bitquery GraphQL API (권장 - 6개월 데이터)

Bitquery는 과거 데이터를 충분히 제공합니다!

```bash
# 1. Bitquery에서 무료 API 키 받기
# https://bitquery.io/ 에서 회원가입 후 API 키 발급

# 2. API 키 설정
export BITQUERY_API_KEY='your_api_key_here'

# 3. Bitquery로 데이터 수집 및 분석
python main.py --use-bitquery
```

### 방법 2: TronScan API (제한적 - 1-2주 데이터)

```bash
python main.py
```

### 주요 옵션

```bash
# Bitquery 사용 (6개월 데이터)
python main.py --use-bitquery

# 캐시 무시하고 새로 데이터 수집
python main.py --no-cache

# 데이터 수집만 실행
python main.py --collect-only --use-bitquery

# 분석만 실행 (데이터가 이미 있을 때)
python main.py --analyze-only

# 시각화만 실행 (분석 결과가 이미 있을 때)
python main.py --visualize-only
```

### 워크플로우

전체 분석은 다음을 순차적으로 실행합니다:
1. 데이터 수집 (Bitquery/TronScan, 업비트, 바이낸스, 환율)
2. 김치프리미엄 계산
3. 상관관계 분석
4. 차트 생성

## 프로젝트 구조

```
Analyze/
├── README.md                   # 이 파일
├── requirements.txt            # 필요 라이브러리
├── config.py                   # API 설정 및 상수
├── main.py                     # 메인 실행 파일
│
├── data_collection/            # 데이터 수집 모듈
│   ├── tron_wallet.py         # TronScan API - 핫월렛 입출금
│   ├── upbit_prices.py        # 업비트 가격 데이터
│   ├── binance_prices.py      # 바이낸스 가격 데이터
│   └── exchange_rates.py      # USD/KRW 환율
│
├── analysis/                   # 분석 모듈
│   ├── premium_calculator.py  # 김치프리미엄 계산
│   └── correlation.py         # 상관관계 분석
│
├── visualization/              # 시각화 모듈
│   └── charts.py              # 차트 생성
│
├── data/                       # 수집된 데이터 (자동 생성)
│   ├── wallet_transfers_hourly.csv
│   ├── kimchi_premiums_hourly.csv
│   ├── correlation_results.csv
│   └── ...
│
└── charts/                     # 생성된 차트 (자동 생성)
    ├── timeline_chart_interactive.html
    ├── timeline_chart.png
    ├── correlation_scatter_plots.png
    └── ...
```

## 분석 내용

### 1. 데이터 수집

- **핫월렛 입출금**: TronScan API를 통해 시간당 입출금량 수집
- **가격 데이터**: 업비트와 바이낸스의 시간당 가격 데이터
- **환율**: USD/KRW 환율 데이터

### 2. 김치프리미엄 계산

**BTC/ETH 프리미엄:**
```
Premium = ((업비트 원화가격 / 환율) - 바이낸스 달러가격) / 바이낸스 달러가격 × 100
```

**USDT 프리미엄:**
```
Premium = (업비트 USDT-KRW 가격 - 환율) / 환율 × 100
```

### 3. 상관관계 분석

- **Pearson 상관계수**: 순입금량과 프리미엄 간의 선형 관계
- **시차상관분석**: 시간 차이를 고려한 선행/후행 관계
- **통계적 유의성**: p-value를 통한 신뢰도 검증

### 4. 시각화

1. **타임라인 차트**: 입출금량과 프리미엄의 시계열 변화
2. **산점도**: 입출금량과 프리미엄의 직접적 관계
3. **히트맵**: 시차별 상관계수 패턴
4. **개별 라그 플롯**: 각 코인별 시차 상관관계

## 결과 확인

1. **인터랙티브 차트**: `charts/timeline_chart_interactive.html`을 브라우저로 열기
2. **정적 이미지**: `charts/` 폴더의 PNG 파일들
3. **분석 데이터**: `data/` 폴더의 CSV 파일들

## 데이터 소스

### 핫월렛 데이터 (선택 가능)
- **Bitquery GraphQL API** (권장): https://bitquery.io/
  - ✅ 6개월 이상 과거 데이터
  - ✅ GraphQL로 효율적 쿼리
  - 🔑 무료 API 키 필요
- **TronScan API**: https://apilist.tronscan.org/api
  - ⚠️ 최근 1-2주 데이터만
  - ✅ API 키 불필요

### 가격 및 환율 데이터
- **업비트 API**: https://api.upbit.com/v1
- **바이낸스 API**: https://api.binance.com/api/v3
- **환율 데이터**: Yahoo Finance (yfinance 라이브러리)
  - ✅ 실제 과거 환율 데이터 (USD/KRW)
  - ✅ API 키 불필요
  - ✅ 일별 데이터를 시간별로 확장

## 주의사항

### ⚠️ TronScan API 데이터 제한

**중요**: TronScan의 무료 API는 과거 데이터 접근에 제한이 있을 수 있습니다. 

- 현재 구현으로는 **최근 1-2주** 정도의 데이터만 수집될 수 있습니다
- 6개월 전체 데이터를 얻으려면:
  1. `config.py`에서 `MAX_TRON_RECORDS`를 더 높게 설정 (예: 100000)
  2. 또는 `ANALYSIS_MONTHS`를 줄여서 더 짧은 기간 분석 (예: 1개월)
  3. 매일 스크립트를 실행하여 점진적으로 데이터 축적
  4. TronGrid API 같은 유료 서비스 고려

### 더 많은 데이터 수집하기

```bash
# 기존 캐시 삭제
rm data/tron_wallet_transfers.json

# config.py 수정
# MAX_TRON_RECORDS = 100000  # 더 많은 레코드 시도

# 재실행 (시간이 오래 걸릴 수 있음)
python main.py --no-cache
```

### 기타 주의사항

- API 호출 제한이 있을 수 있으므로 대량 데이터 수집 시 시간이 걸립니다
- 캐시 기능을 사용하여 반복 실행 시 시간을 절약할 수 있습니다
- 네트워크 오류 시 자동으로 재시도하지 않으므로 다시 실행해야 합니다

자세한 내용은 `KNOWN_ISSUES.md` 파일을 참고하세요.

## 라이선스

이 프로젝트는 분석 목적으로 제작되었습니다.

