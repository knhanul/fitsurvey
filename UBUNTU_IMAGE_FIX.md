# 우분투 서버 이미지 문제 해결 가이드

## 문제 원인 분석

### 1. 파일 경로 문제
- **Windows**: `assets/images/eq_1_photo.png`
- **Ubuntu**: `/app/assets/images/eq_1_photo.png` (절대 경로 필요)

### 2. 파일 권한 문제
- 이미지 파일 권한 없음
- 폴더 접근 권한 없음

### 3. 파일 존재 여부
- 배포 시 이미지 파일 누락
- 잘못된 경로 참조

## 해결 방법

### 1. 파일 경로 수정 (app.py)

**현재 코드:**
```python
image_path = equipment.get('photo_image_path', f"assets/images/eq_{equipment['id']}_photo.png")
```

**수정된 코드:**
```python
import os

# 절대 경로로 변경
base_path = os.path.dirname(os.path.abspath(__file__))
image_path = equipment.get('photo_image_path', os.path.join(base_path, "assets/images", f"eq_{equipment['id']}_photo.png"))
```

### 2. 파일 권한 설정

**서버에서 실행:**
```bash
# 이미지 폴더 권한 설정
sudo chmod -R 755 /app/assets/images/
sudo chown -R www-data:www-data /app/assets/images/

# 모든 이미지 파일 권한 설정
sudo chmod 644 /app/assets/images/*.png
```

### 3. 파일 존재 확인

**서버에서 확인:**
```bash
# 이미지 파일 목록 확인
ls -la /app/assets/images/

# 파일 개수 확인
find /app/assets/images/ -name "*.png" | wc -l

# 특정 파일 확인
ls -la /app/assets/images/eq_1_photo.png
```

### 4. Streamlit 설정 수정

**app.py에 추가:**
```python
import os

# 정적 파일 경로 설정
STATIC_DIR = os.path.join(os.path.dirname(__file__), "assets/images")

def check_image_exists(image_path):
    """이미지 파일 존재 여부 확인"""
    if not os.path.isabs(image_path):
        image_path = os.path.join(STATIC_DIR, os.path.basename(image_path))
    
    if os.path.exists(image_path):
        return image_path
    else:
        # 로그 출력
        print(f"이미지 파일 없음: {image_path}")
        return None
```

### 5. 배포 스크립트 수정

**deploy.sh:**
```bash
#!/bin/bash

# 이미지 파일 복사 확인
echo "이미지 파일 복사 중..."
cp -r assets/images/ /app/assets/

# 권한 설정
chmod -R 755 /app/assets/
chown -R www-data:www-data /app/assets/

# 확인
ls -la /app/assets/images/
```

### 6. Docker 사용 시

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 이미지 파일 복사
COPY assets/images/ ./assets/images/

# 권한 설정
RUN chmod -R 755 ./assets/

# 나머지 설정...
```

## 디버깅 방법

### 1. 로그 확인
```bash
# Streamlit 로그 확인
tail -f /var/log/streamlit/app.log

# 시스템 로그 확인
journalctl -u streamlit -f
```

### 2. 파일 시스템 확인
```bash
# 현재 작업 디렉토리 확인
pwd

# 파일 구조 확인
find . -name "*.png" -type f

# 권한 확인
ls -la assets/
```

### 3. 테스트 코드 추가

**app.py에 디버깅 코드 추가:**
```python
# 이미지 경로 디버깅
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"스크립트 경로: {os.path.dirname(__file__)}")
print(f"이미지 경로: {image_path}")
print(f"파일 존재: {os.path.exists(image_path)}")
```

## 빠른 해결 방법

### 1. 즉시 적용 코드
```python
import os

def get_image_path(equipment_id, image_type="photo"):
    """이미지 경로 가져오기"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_name = f"eq_{equipment_id}_{image_type}.png"
    image_path = os.path.join(base_dir, "assets", "images", image_name)
    
    if os.path.exists(image_path):
        return image_path
    else:
        # 기본 이미지 반환
        return os.path.join(base_dir, "assets", "images", "default.png")
```

### 2. 서버에서 직접 확인
```bash
# 서버 접속 후
cd /app
python -c "
import os
print('현재 디렉토리:', os.getcwd())
print('이미지 폴더:', os.path.exists('assets/images'))
print('이미지 파일:', os.path.exists('assets/images/eq_1_photo.png'))
"
```

## 최종 확인

1. **파일 존재**: 모든 이미지 파일이 서버에 있는지
2. **경로 정확**: 절대 경로로 참조하는지  
3. **권한 설정**: 파일 읽기 권한이 있는지
4. **로그 확인**: 에러 메시지가 있는지

이 방법들로 우분투 서버의 이미지 문제를 해결할 수 있습니다.
