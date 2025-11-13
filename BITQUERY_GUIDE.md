# Bitquery 사용 가이드

Bitquery GraphQL API를 사용하면 **6개월 이상의 과거 데이터**를 가져올 수 있습니다!

## 1단계: API 키 발급

### 무료 플랜
1. https://bitquery.io/ 방문
2. 우측 상단 "Sign Up" 클릭
3. 이메일로 가입
4. 대시보드에서 API 키 확인

### 무료 플랜 제한
- ✅ **월 100,000 포인트** 무료
- ✅ 대부분의 쿼리는 1-10 포인트
- ✅ 6개월 데이터 수집에 충분함
- 💳 더 많이 필요하면 유료 플랜

## 2단계: API 키 설정

### macOS/Linux
```bash
# 터미널에서 실행
export BITQUERY_API_KEY='your_api_key_here'

# 영구적으로 설정하려면 ~/.bashrc 또는 ~/.zshrc에 추가
echo "export BITQUERY_API_KEY='your_api_key_here'" >> ~/.zshrc
source ~/.zshrc
```

### Windows (PowerShell)
```powershell
$env:BITQUERY_API_KEY='your_api_key_here'

# 영구적으로 설정
[System.Environment]::SetEnvironmentVariable('BITQUERY_API_KEY','your_api_key_here','User')
```

### 확인
```bash
echo $BITQUERY_API_KEY
# API 키가 출력되면 성공!
```

## 3단계: 데이터 수집

```bash
cd /Users/june/Documents/Workspace/Analyze

# Bitquery로 6개월 데이터 수집
python main.py --use-bitquery --no-cache
```

## 예상 소요 시간

- **Bitquery 쿼리**: 2-5분 (6개월 데이터)
- **업비트/바이낸스 가격**: 5-10분
- **분석 및 차트**: 1-2분
- **총**: 약 10-15분

## GraphQL 쿼리 예제

우리 코드에서 사용하는 쿼리:

```graphql
query ($network: TronNetwork!, $address: String!, $token: String!, 
       $from: ISO8601DateTime, $till: ISO8601DateTime, 
       $offset: Int!, $limit: Int!) {
  tron(network: $network) {
    transfers(
      options: {offset: $offset, limit: $limit, desc: "block.timestamp.time"}
      date: {since: $from, till: $till}
      currency: {is: $token}
      any: [
        {sender: {is: $address}}
        {receiver: {is: $address}}
      ]
    ) {
      block {
        timestamp {
          time(format: "%Y-%m-%d %H:%M:%S")
        }
      }
      sender {
        address
      }
      receiver {
        address
      }
      amount
      currency {
        address
        symbol
      }
      transaction {
        hash
      }
    }
  }
}
```

## 수동 테스트

Bitquery IDE에서 직접 테스트해볼 수 있습니다:
1. https://graphql.bitquery.io/ide 접속
2. 우측 상단에 API 키 입력
3. 위 쿼리 복사
4. Variables에 다음 입력:
```json
{
  "network": "tron",
  "address": "TVreyZvJWKmcpJGioTzJ81T1JMSXMZ3pV9",
  "token": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "from": "2024-05-01",
  "till": "2024-11-13",
  "offset": 0,
  "limit": 10
}
```
5. "Run Query" 클릭

## 문제 해결

### "API key required" 에러
```bash
# API 키가 설정되었는지 확인
echo $BITQUERY_API_KEY

# 없으면 다시 설정
export BITQUERY_API_KEY='your_api_key_here'
```

### "Rate limit exceeded" 에러
- 무료 플랜의 월간 한도를 초과한 경우
- 다음 달까지 기다리거나 유료 플랜 고려

### "No data in response" 에러
- 날짜 범위 확인
- 주소가 정확한지 확인
- Bitquery IDE에서 직접 테스트

## TronScan vs Bitquery 비교

| 특징 | TronScan | Bitquery |
|------|----------|----------|
| API 키 | 불필요 | 필요 (무료) |
| 과거 데이터 | 1-2주 | 6개월+ |
| 속도 | 느림 (페이징) | 빠름 (GraphQL) |
| 안정성 | 보통 | 높음 |
| 권장 | 테스트용 | 실제 분석용 |

## 다음 단계

Bitquery로 6개월 데이터를 수집했다면:

```bash
# 전체 분석 실행
python main.py --use-bitquery

# 결과 확인
open charts/timeline_chart_interactive.html
```

즐거운 분석 되세요! 🎉

