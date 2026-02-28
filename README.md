# 아파트 휘트니스 장비 교체 설문 웹

Python Streamlit과 PostgreSQL을 사용한 아파트 휘트니스 장비 교체 설문 웹 애플리케이션입니다.

## 기능

- **기본 정책 설문**: 장비 교체 방식(일괄/선별)에 대한 의견 수렴
- **개별 장비 투표**: 운동존/프리웨이트존별 장비 상태 투표
- **휴대폰 인증**: 전화번호 뒷자리 4자리로 응답자 구분
- **Upsert 지원**: 동일 번호로 재응답 시 최신 응답으로 갱신

## 데이터베이스 스키마

```sql
-- users 테이블: 기본 정책 의견
CREATE TABLE users (
    phone_suffix VARCHAR(4) PRIMARY KEY,
    policy_opinion VARCHAR(20) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- item_votes 테이블: 개별 장비 의견
CREATE TABLE item_votes (
    phone_suffix VARCHAR(4) REFERENCES users(phone_suffix) ON DELETE CASCADE,
    item_id VARCHAR(50) NOT NULL,
    vote_type VARCHAR(20) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (phone_suffix, item_id)
);
```

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env.example` 파일을 `.env`로 복사하고 데이터베이스 URL을 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
DATABASE_URL=postgresql://username:password@localhost:5432/fitness_survey
```

### 3. PostgreSQL 데이터베이스 생성

```sql
CREATE DATABASE fitness_survey;
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

## 장비 이미지 추가

`images/` 폴더를 생성하고 장비별 사진을 아래와 같은 경로에 저장합니다:

```
images/
├── treadmill_1.jpg
├── treadmill_2.jpg
├── treadmill_3.jpg
├── elliptical_1.jpg
├── elliptical_2.jpg
├── bike_1.jpg
├── bike_2.jpg
├── bench_1.jpg
├── dumbbell_set.jpg
├── squat_rack.jpg
├── cable_machine.jpg
├── lat_pulldown.jpg
└── leg_press.jpg
```

이미지가 없을 경우 placeholder가 표시됩니다.

## 배포

### Streamlit Cloud 배포

1. [share.streamlit.io](https://share.streamlit.io)에 접속
2. GitHub 저장소 연결
3. `DATABASE_URL` 시크릿 추가

### 환경변수 (Streamlit Cloud Secrets)

`.streamlit/secrets.toml` 파일 생성:
```toml
DATABASE_URL = "postgresql://username:password@host:5432/fitness_survey"
```

## 프로젝트 구조

```
FitSurvay/
├── app.py              # 메인 Streamlit 애플리케이션
├── models.py           # SQLAlchemy ORM 모델
├── requirements.txt    # Python 의존성
├── .env.example        # 환경변수 템플릿
├── .env                # 실제 환경변수 (gitignore)
├── images/             # 장비 사진 폴더
└── README.md           # 문서
```

## 기술 스택

- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Language**: Python 3.9+

## 라이선스

MIT License
