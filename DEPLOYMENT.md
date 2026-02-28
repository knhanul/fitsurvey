# 아파트 휘트니스 장비 교체 설문

## GitHub 연동 및 배포 방법

### 1. GitHub 저장소 생성

1. [GitHub](https://github.com)에 로그인
2. 새 저장소 생성: `fitness-survey`
3. 저장소 복사 URL 복사

### 2. 로컬 저장소 설정

```bash
# 프로젝트 폴더로 이동
cd "e:\Pjt\FitSurvay"

# Git 초기화
git init

# 원격 저장소 연결
git remote add origin https://github.com/사용자이름/fitness-survey.git

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: 아파트 휘트니스 장비 교체 설문 애플리케이션"
```

### 3. GitHub에 푸시

```bash
# 메인 브랜치에 푸시
git push -u origin main
```

### 4. 배포 옵션

#### 옵션 1: Streamlit Cloud (추천)
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 저장소 연결
3. `.env` 파일에 환경변수 설정
4. 자동 배포

#### 옵션 2: VPS 서버 배포
```bash
# 서버에서 클론
git clone https://github.com/사용자이름/fitness-survey.git
cd fitness-survey

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 PostgreSQL 정보 입력

# 애플리케이션 실행
streamlit run app.py --server.port 8501
```

#### 옵션 3: Docker 배포
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

```bash
# Docker 이미지 빌드 및 실행
docker build -t fitness-survey .
docker run -p 8501:8501 fitness-survey
```

### 5. .gitignore 설정

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/
```

### 6. 데이터베이스 설정

**Streamlit Cloud Secrets:**
```
DATABASE_URL=postgresql://username:password@host:5432/fitness_survey
```

**VPS 서버:**
```bash
# PostgreSQL 설치 및 설정
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb fitness_survey
```

이제 Git을 통해 서버에 쉽게 배포할 수 있습니다.
