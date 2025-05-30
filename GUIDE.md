# LLM 기반 차트 생성 시스템 설치 가이드

## 📋 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [Python 라이브러리 설치](#python-라이브러리-설치)
3. [Oracle 클라이언트 설치](#oracle-클라이언트-설치)
4. [환경 변수 설정](#환경-변수-설정)
5. [디렉토리 구조 설정](#디렉토리-구조-설정)
6. [설치 검증](#설치-검증)
7. [문제 해결](#문제-해결)

---

## 🖥️ 시스템 요구사항

### 최소 요구사항
- **운영체제**: Windows 10/11, Ubuntu 18.04+, macOS 10.14+
- **Python**: 3.8 이상 (권장: 3.9-3.11)
- **메모리**: 최소 8GB RAM (권장: 16GB+)
- **저장공간**: 최소 5GB 여유 공간

### 네트워크 요구사항
- Oracle 데이터베이스 서버 접근 (포트 1521)
- LLM API 서버 접근 (HTTP/HTTPS)
- 인터넷 연결 (패키지 다운로드)

---

## 🐍 Python 라이브러리 설치

### requirements.txt 파일

```txt
# 웹 프레임워크
Flask==3.0.0
Flask-Session==0.5.0

# 데이터 처리
pandas==2.1.4
numpy==1.24.3

# 차트 생성
matplotlib==3.8.2

# 데이터베이스
oracledb==2.0.1
SQLAlchemy==2.0.23

# HTTP 요청
requests==2.31.0

# 환경 설정
python-dotenv==1.0.0

# LLM 관련 (선택사항)
transformers==4.36.2
torch==2.1.2

# vLLM (GPU 환경에서만 - 선택사항)
# vllm==0.2.6

# Google Generative AI (Gemini 사용 시 - 선택사항)
google-generativeai==0.3.2

# 개발/테스트 도구
pytest==7.4.3
pytest-flask==1.3.0
```

### 설치 명령어

#### 1. 기본 설치 (필수)
```bash
pip install Flask==3.0.0
pip install Flask-Session==0.5.0
pip install pandas==2.1.4
pip install numpy==1.24.3
pip install matplotlib==3.8.2
pip install oracledb==2.0.1
pip install SQLAlchemy==2.0.23
pip install requests==2.31.0
pip install python-dotenv==1.0.0
```

#### 2. 한번에 설치
```bash
# requirements.txt 파일을 다운로드한 후
pip install -r requirements.txt
```

#### 3. LLM 모드별 추가 설치

**API 모드 (권장)**
```bash
# 추가 설치 없음 - 기본 설치만으로 충분
```

**vLLM 모드 (GPU 서버 환경)**
```bash
pip install transformers==4.36.2
pip install torch==2.1.2
pip install vllm==0.2.6
```

**Gemini API 모드**
```bash
pip install google-generativeai==0.3.2
```

#### 4. 개발/테스트 도구 (선택사항)
```bash
pip install pytest==7.4.3
pip install pytest-flask==1.3.0
```

---

## 🗄️ Oracle 클라이언트 설치

### Windows 환경

#### 1. Oracle Instant Client 다운로드
- [Oracle Instant Client 다운로드 페이지](https://www.oracle.com/database/technologies/instant-client/downloads.html)
- **Version**: 21.18 (권장)
- **Package**: Basic 또는 Basic Light

#### 2. 설치 및 설정
```cmd
# 1. 다운로드한 파일을 C:\oracle\instantclient_21_18 에 압축 해제

# 2. 환경 변수 설정 (시스템 환경 변수)
set ORACLE_HOME=C:\oracle\instantclient_21_18
set PATH=%PATH%;C:\oracle\instantclient_21_18

# 3. 재부팅 또는 cmd 재시작
```

### Linux (Ubuntu/CentOS) 환경

#### Ubuntu
```bash
# 1. 필수 패키지 설치
sudo apt-get update
sudo apt-get install libaio1 libaio-dev

# 2. Oracle Instant Client 다운로드 및 설치
wget https://download.oracle.com/otn_software/linux/instantclient/2118000/instantclient-basic-linux.x64-21.18.0.0.0dbru.zip
sudo mkdir -p /opt/oracle
sudo unzip instantclient-basic-linux.x64-21.18.0.0.0dbru.zip -d /opt/oracle/

# 3. 환경 변수 설정
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_18:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### CentOS/RHEL
```bash
# 1. 필수 패키지 설치
sudo yum install libaio

# 2. Oracle Instant Client 설치 (위와 동일)
# 3. 환경 변수 설정 (위와 동일)
```

### macOS 환경
```bash
# 1. Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Oracle Instant Client 설치
brew install instantclient-basic

# 3. 환경 변수 설정
echo 'export DYLD_LIBRARY_PATH=/opt/oracle/instantclient_21_18:$DYLD_LIBRARY_PATH' >> ~/.zshrc
source ~/.zshrc
```

---

## 🔧 환경 변수 설정

### .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# LLM API 설정
API_KEY=your-llm-api-key-here
API_MODEL=Qwen3-32B
API_ENDPOINT=http://dev.assistant.llm.skhynix.com/v1/chat/completions

# Gemini API (사용하는 경우)
GEMINI_API_KEY=your-gemini-api-key-here

# Oracle 데이터베이스 설정
ORACLE_USER=hiq1
ORACLE_PASSWORD=hiq11!
ORACLE_DSN=10.158.122.119/HIQ1DEV
ORACLE_CLIENT_LIB=C:\\oracle\\instantclient_21_18

# Flask 설정
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=False

# 디렉토리 설정
OUTPUT_DIR=./chart_outputs
RESULTS_DIR=./results
```

### 시스템 환경 변수 (Windows)

```cmd
# 시스템 속성 > 고급 > 환경 변수에서 설정
ORACLE_HOME=C:\oracle\instantclient_21_18
PATH=%PATH%;C:\oracle\instantclient_21_18
API_KEY=your-api-key-here
```

### 시스템 환경 변수 (Linux/macOS)

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export ORACLE_HOME=/opt/oracle/instantclient_21_18
export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
export API_KEY="your-api-key-here"

# 적용
source ~/.bashrc  # 또는 source ~/.zshrc
```

---

## 📁 디렉토리 구조 설정

### 프로젝트 디렉토리 생성

```bash
# 프로젝트 디렉토리 생성
mkdir llm-chart-system
cd llm-chart-system

# 필수 디렉토리 생성
mkdir templates
mkdir static
mkdir static/css
mkdir static/js
mkdir chart_outputs
mkdir results
mkdir logs

# 파일 구조 확인
tree
```

### 예상 디렉토리 구조
```
llm-chart-system/
├── .env                        # 환경 변수 파일
├── requirements.txt            # Python 패키지 목록
├── Rating_Test_Data.csv        # 데이터 파일
├── metadata.json              # 메타데이터 파일
├── web_app.py                 # 메인 웹 애플리케이션
├── main.py                    # 애플리케이션 로직
├── config.py                  # 설정 파일
├── llm_manager.py            # LLM 관리자
├── data_manager.py           # 데이터 관리자
├── chart_generator.py        # 차트 생성기
├── templates/
│   └── index.html            # 메인 HTML 템플릿
├── static/
│   ├── css/
│   │   └── main.css          # 메인 스타일시트
│   └── js/
│       ├── sessionHistory.js # 히스토리 관리
│       ├── dataManager.js    # 데이터 관리
│       ├── chartManager.js   # 차트 관리
│       ├── uiController.js   # UI 제어
│       ├── modalManager.js   # 모달 관리
│       └── main.js           # 메인 JavaScript
├── chart_outputs/            # 생성된 차트 이미지
├── results/                  # 결과 파일들
└── logs/                    # 로그 파일들
```

---

## ✅ 설치 검증

### 1. Python 환경 확인
```bash
python --version  # Python 3.8+ 확인
pip --version     # pip 확인
```

### 2. 패키지 설치 확인
```python
# test_imports.py
try:
    import flask
    import pandas
    import numpy
    import matplotlib
    import oracledb
    import requests
    print("✅ 모든 필수 패키지가 정상적으로 설치되었습니다.")
except ImportError as e:
    print(f"❌ 패키지 오류: {e}")
```

### 3. 환경 확인 스크립트 실행
```bash
python check_environment.py
```

### 4. Mock 테스트 실행
```bash
python test_mock_mode.py
```

---

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. Oracle 클라이언트 오류
```
DPI-1047: Cannot locate a 64-bit Oracle Client library
```
**해결책:**
- Oracle Instant Client 재설치
- 환경 변수 PATH 확인
- 32bit/64bit 버전 일치 확인

#### 2. matplotlib 한글 폰트 오류
```
UserWarning: Glyph missing from current font
```
**해결책:**
```bash
# Windows
pip install matplotlib
# 나눔고딕 폰트 설치 필요

# Linux
sudo apt-get install fonts-nanum
fc-cache -fv

# macOS
brew install font-nanum-gothic
```

#### 3. vLLM 설치 오류 (GPU 환경)
```
ERROR: Failed building wheel for vllm
```
**해결책:**
```bash
# CUDA 버전 확인
nvidia-smi

# PyTorch CUDA 버전 맞춤 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# vLLM 재설치
pip install vllm
```

#### 4. 메모리 부족 오류
```
OutOfMemoryError: CUDA out of memory
```
**해결책:**
- GPU 메모리 사용량 조정 (`VLLM_GPU_MEMORY_UTILIZATION=0.7`)
- 모델 크기 축소
- API 모드 사용 권장

#### 5. 포트 충돌 오류
```
OSError: [Errno 48] Address already in use
```
**해결책:**
```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/macOS

# 다른 포트 사용
python web_app.py --port 5001
```

### 디버깅 팁

#### 1. 로그 레벨 조정
```bash
python web_app.py --debug --log-level DEBUG
```

#### 2. 단계별 테스트
```bash
# 1. 환경 확인
python check_environment.py

# 2. Mock 테스트
python test_mock_mode.py

# 3. 실제 실행
python web_app.py --csv data.csv --metadata metadata.json
```

#### 3. 의존성 충돌 해결
```bash
# 가상환경 생성 (권장)
python -m venv llm_chart_env
source llm_chart_env/bin/activate  # Linux/macOS
llm_chart_env\Scripts\activate     # Windows

# 패키지 재설치
pip install -r requirements.txt
```

---

## 🚀 실행 가이드

### 1. 개발 환경에서 실행
```bash
python web_app.py --csv Rating_Test_Data.csv --metadata metadata.json --llm-mode api --debug
```

### 2. 프로덕션 환경에서 실행
```bash
python web_app.py --csv Rating_Test_Data.csv --metadata metadata.json --llm-mode api --host 0.0.0.0 --port 80
```

### 3. 사용자별 접속
```
http://localhost:5000/username
```

---

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. **환경 확인 스크립트**: `python check_environment.py`
2. **Mock 테스트**: `python test_mock_mode.py`
3. **로그 파일**: `logs/web_app.log`
