# voca.nuni.co.kr/toeicvoca/ 서비스 연동 가이드

## 서비스 개요
- **도메인**: voca.nuni.co.kr/toeicvoca/
- **기능**: 한국어-영어 번역 API 서비스
- **목표**: 기존 서비스 유지하며 새로운 설문 앱 연동

## 연동 방법

### 1. 웹 서버 연동 (Nginx 리버스 프록시)

```nginx
server {
    listen 80;
    server_name voca.nuni.co.kr;
    
    # 기존 서비스 유지
    location /toeicvoca/ {
        proxy_pass http://voca-internal-service:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 새로운 설문 앱 연동
    location /imunefitsurvey/ {
        proxy_pass http://localhost:8502;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 기타 경로
    location / {
        return 404;
    }
}
```

### 2. Streamlit 앱 수정

**app.py 수정:**
```python
# 기존 페이지로 리다이렉트 처리
def check_redirect():
    if 'HTTP_X_FORWARDED_HOST' in st.query_params or 'HTTP_HOST' in st.query_params:
        forwarded_host = st.query_params.get('HTTP_X_FORWARDED_HOST', st.query_params.get('HTTP_HOST', ''))
        if 'uni.co.kr' in forwarded_host:
            # 기존 서비스로 리다이렉트
            st.markdown("""
            <script>
                window.location.href = 'https://voca.nuni.co.kr/toeicvoca/';
            </script>
            """, unsafe_allow_html=True)
            st.stop()

# 앱 시작 부분에 추가
check_redirect()
```

### 3. 도메인 설정

**방법 1: 서브도메인**
- `imunefitsurvey.voca.nuni.co.kr`

**방법 2: 경로 기반**
- `voca.nuni.co.kr/imunefitsurvey/`

**방법 3: 별도 도메인**
- `imunefitsurvey.voca.nuni.co.kr`

## 배포 옵션

### 옵션 1: Nginx 리버스 프록시 (추천)
```bash
# Nginx 설정 파일 수정
sudo nano /etc/nginx/sites-available/voca.conf

# 설정 재로드 및 재시작
sudo nginx -t && sudo systemctl restart nginx
```

### 옵션 2: Cloudflare DNS
1. Cloudflare 계정 로그인
2. 도메인 추가: `imunefitsurvey.voca.nuni.co.kr`
3. 프록시 설정: `voca.nuni.co.kr/imunefitsurvey/` → 서버 IP

### 옵션 3: Apache 리버스 프록시
```apache
<VirtualHost *:80>
    ServerName voca.nuni.co.kr
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    # 기존 서비스
    ProxyPass /toeicvoca/ http://voca-internal:8080/
    ProxyPassReverse /toeicvoca/ http://voca-internal:8080/
    
    # 새로운 설문 앱
    ProxyPass /imunefitsurvey/ http://localhost:8502/
    ProxyPassReverse /imunefitsurvey/ http://localhost:8502/
</VirtualHost>
```

## 보안 고려사항

### 1. CORS 설정
```python
# app.py에 CORS 헤더 추가
st.markdown("""
<script>
    // CORS 헤더 설정
    fetch('https://api.example.com/data', {
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    });
</script>
""", unsafe_allow_html=True)
```

### 2. 인증 처리
```python
# 기존 인증 확인
def check_existing_auth():
    # 기존 voca 인증 세션 확인 로직
    pass

# Streamlit 세션과 연동
def sync_sessions():
    # 기존 세션과 Streamlit 세션 동기화
    pass
```

### 3. SSL 인증서
```bash
# Let's Encrypt로 SSL 발급
sudo certbot --nginx -d voca.nuni.co.kr
```

## 테스트 방법

### 1. 로컬 테스트
```bash
# 로컬에서 접속 테스트
curl -I http://localhost:8502
```

### 2. 외부 접속 테스트
```bash
# 도메인 접속 테스트
curl -I https://voca.nuni.co.kr/imunefitsurvey/
```

## 문제 해결

### 1. 프록시 충돌
```nginx
# 특정 경로 제외
location ^/toeicvoca/admin/ {
    return 403;
}
```

### 2. 세션 공유 문제
```python
# 세션 키 충돌 방지
session_key = f"voca_session_{st.session_state.get('phone_suffix', '')}"
```

### 3. 정적 파일 경로
```python
# 정적 파일 접근
STATIC_PATH = "/var/www/voca/static"
if os.path.exists(STATIC_PATH + image_path):
    st.image(os.path.join(STATIC_PATH, image_path))
```

## 유지보수 방안

### 1. 이중화 처리
```python
# 기존 서비스와 새로운 서비스 모두 사용 가능
def get_equipment_data():
    try:
        # 기존 voca API에서 데이터 가져오기
        return fetch_from_voca_api()
    except:
        # 새로운 DB에서 데이터 가져오기
        return fetch_from_local_db()
```

### 2. 점진적 마이그레이션
```python
# 단계별 마이그레이션 계획
PHASE_1 = "기존 서비스 유지"
PHASE_2 = "이중 운영"
PHASE_3 = "완전 전환"
```

이 방법으로 기존 voca 서비스를 유지하면서 새로운 설문 앱을 연동할 수 있습니다.
