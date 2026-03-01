# 서버 이미지 경로 설정 완료

## 수정된 내용

**STATIC_DIR 경로 변경:**
```python
# 이전 (동적 경로)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")

# 수정 후 (서버 실제 경로)
STATIC_DIR = "/var/www/FitSurvey/assets/images"
```

## 서버에서 확인

### 1. 파일 존재 확인
```bash
# 이미지 폴더 확인
ls -la /var/www/FitSurvey/assets/images/

# 파일 개수 확인
find /var/www/FitSurvey/assets/images/ -name "*.png" | wc -l

# 특정 파일 확인
ls -la /var/www/FitSurvey/assets/images/eq_1_photo.png
```

### 2. 권한 설정
```bash
# 폴더 권한 설정
sudo chmod -R 755 /var/www/FitSurvey/assets/images/
sudo chown -R www-data:www-data /var/www/FitSurvey/assets/images/

# 파일 권한 확인
ls -la /var/www/FitSurvey/assets/images/
```

### 3. 앱 재시작
```bash
# Streamlit 재시작
pkill -f streamlit
streamlit run app.py --server.port 8502

# 또는 서비스 재시작
sudo systemctl restart streamlit
```

### 4. 로그 확인
```bash
# 이미지 경로 로그 확인
tail -f /var/log/streamlit/app.log | grep "이미지 파일"

# 오류 로그 확인
tail -f /var/log/streamlit/error.log
```

## 경로 구조

```
/var/www/FitSurvey/
├── app.py
├── assets/
│   └── images/
│       ├── eq_1_photo.png
│       ├── eq_1_spec.png
│       ├── eq_2_photo.png
│       └── ...
└── .env
```

## 테스트 방법

### 1. 파이썬 테스트
```bash
cd /var/www/FitSurvey
python -c "
import os
STATIC_DIR = '/var/www/FitSurvey/assets/images'
print('정적 디렉토리:', STATIC_DIR)
print('폴더 존재:', os.path.exists(STATIC_DIR))
print('eq_1_photo.png 존재:', os.path.exists(os.path.join(STATIC_DIR, 'eq_1_photo.png')))
"
```

### 2. 브라우저 테스트
- 웹사이트 접속
- 장비 이미지 표시 확인
- 확대 기능 테스트

이제 실제 서버 경로에 맞춰 이미지가 정상 표시됩니다.
