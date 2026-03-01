# PostgreSQL 데이터베이스 연결 정보 설정 가이드

## .env 파일 설정 방법

1. **.env.example 파일 복사**
```bash
copy .env.example .env
```

2. **.env 파일 내용 수정**
```
DATABASE_URL=postgresql://username:password@localhost:5432/fitness_survey
```

3. **실제 정보로 변경**
- username: PostgreSQL 사용자명
- password: PostgreSQL 비밀번호  
- localhost: DB 서버 주소
- 5432: PostgreSQL 포트
- fitness_survey: 데이터베이스 이름

## 예시

**로컬 PostgreSQL:**
```
DATABASE_URL=postgresql://postgres:123456@localhost:5432/fitness_survey
```

**클라우드 PostgreSQL:**
```
DATABASE_URL=postgresql://myuser:mypassword@db.example.com:5432/fitness_survey
```

## 확인 방법

1. **.env 파일 존재 확인**
```bash
dir .env
```

2. **환경변수 설정 확인**
```bash
$env:DATABASE_URL
```

3. **PostgreSQL 연결 테스트**
```bash
psql "postgresql://username:password@localhost:5432/fitness_survey"
```

## 문제 해결

**오류: "DATABASE_URL 환경변수가 설정되지 않았습니다"**

1. .env 파일이 있는지 확인
2. .env 파일 내용이 올바른지 확인
3. Python이 .env 파일을 읽을 수 있는지 확인
4. PostgreSQL 서버가 실행 중인지 확인

**참고: .env 파일은 .gitignore에 포함되어 Git에 올라가지 않습니다.**
