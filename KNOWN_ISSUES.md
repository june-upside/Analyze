# 알려진 이슈 및 해결 방법

## 1. TronScan API 데이터 제한

### 문제
TronScan API는 실제로 오래된 트랜잭션 데이터를 충분히 제공하지 않을 수 있습니다. 현재 구현으로는 최근 1-2주 정도의 데이터만 수집됩니다.

### 원인
- TronScan의 무료 API는 최근 데이터에 대한 접근만 제공할 수 있음
- API 페이징에 제한이 있을 수 있음
- 특정 주소의 과거 트랜잭션 조회가 제한될 수 있음

### 해결 방법

#### 옵션 1: 더 많은 페이지 가져오기 (수정 완료)
`tron_wallet.py`를 수정하여 `max_records` 파라미터를 늘렸습니다. 
더 많은 데이터를 원하면 `max_records`를 증가시킬 수 있습니다:

```python
# data_collection/tron_wallet.py의 collect() 메서드에서
transfers = self.fetch_transfers(start_ts, end_ts, max_records=50000)  # 기본값 10000
```

#### 옵션 2: 다른 데이터 소스 사용
- **Tron Grid API**: TronGrid는 더 많은 과거 데이터 접근 가능 (API 키 필요)
- **Blockchain Explorer**: 직접 블록체인 데이터 크롤링
- **데이터 제공자**: Nansen, Dune Analytics 등의 서비스 이용

#### 옵션 3: 점진적 데이터 수집
매일/매주 스크립트를 실행하여 데이터를 점진적으로 수집:

```bash
# 크론잡 설정
0 0 * * * cd /path/to/Analyze && python main.py --collect-only
```

#### 옵션 4: 더 짧은 기간으로 분석
설정 파일에서 분석 기간을 조정:

```python
# config.py
ANALYSIS_MONTHS = 1  # 6개월 대신 1개월로 변경
```

## 2. API Rate Limiting

### 문제
많은 요청을 빠르게 보내면 API에서 차단될 수 있습니다.

### 해결 방법
`config.py`에서 `RATE_LIMIT_DELAY`를 증가:

```python
RATE_LIMIT_DELAY = 0.5  # 0.2에서 0.5로 증가
```

## 3. 데이터 재수집

캐시된 데이터를 삭제하고 다시 수집하려면:

```bash
# 캐시 삭제
rm -rf data/*.json
rm -rf data/*.csv

# 다시 수집
python main.py --no-cache
```

## 권장 사항

현재 상황에서는:

1. **짧은 기간 분석**: 1-2주 데이터로 개념 증명 (Proof of Concept)
2. **패턴 확인**: 짧은 기간이라도 입출금과 프리미엄의 상관관계 패턴 확인 가능
3. **장기 데이터 수집**: 매일 실행하여 점진적으로 데이터 축적
4. **유료 API 고려**: 더 많은 과거 데이터가 필요하면 유료 서비스 검토

## 테스트 실행

더 많은 데이터를 가져오려면:

```bash
# 기존 캐시 삭제
rm data/tron_wallet_transfers.json

# max_records를 늘려서 재실행 (코드 수정 후)
python main.py --no-cache
```

