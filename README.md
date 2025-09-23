# nebula-client
[Nebula] Fast API

## 개발 환경 세팅

1) 가상환경 생성 및 활성화

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
```

2) 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3) 개발 서버 실행

```bash
uvicorn app.main:app --reload
```

4) 헬스체크

```bash
curl http://127.0.0.1:8000/health
```

