"""
config.py - 차트 생성 시스템 설정 파일
- LLM 모드 설정
- 경로 및 기본 설정
"""

import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# LLM 모드 정의
class LLMMode(Enum):
    VLLM = "vllm"           # 로컬 vLLM 모델 사용
    API = "api"             # 외부 API 사용 (OpenAI)
    OFFLINE = "offline"     # LLM 미사용 (오프라인 모드)

# 기본 설정
class Config:
    # LLM 설정
    LLM_MODE = LLMMode.VLLM  # 기본값은 VLLM 모드
    
    # VLLM 모드 설정
    VLLM_MODEL_NAME = "Qwen/Qwen3-32B-AWQ"
    VLLM_TENSOR_PARALLEL_SIZE = 2
    VLLM_GPU_MEMORY_UTILIZATION = 0.85
    VLLM_MAX_MODEL_LEN = 16384
    
    # API 모드 설정 (Gemini)
    # API_KEY = os.environ.get("GEMINI_API_KEY", "")
    # API_MODEL = "gemini-2.5-flash-preview-04-17"  # Gemini 모델
    # API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{API_MODEL}:generateContent?key={API_KEY}"
    
    API_KEY = os.environ.get("API_KEY", "")
    API_MODEL = "Qwen3-32B"  # 모델
    # API_ENDPOINT = f"http://dev.assistant.llm.skhynix.com/v1/chat/completions"
    API_ENDPOINT = f"http://localhost:8000/v1/chat/completions"
    
    # 오프라인 모드 설정
    # 영업부 매출과 순이익을 월별로 조회하는 SQL 쿼리
    DEFAULT_SQL_TEMPLATE = """
    SELECT 
        날짜,
        SUM(CASE WHEN 부서 = '영업부' THEN 매출 ELSE 0 END) AS 영업부_매출,
        SUM(CASE WHEN 부서 = '영업부' THEN 순이익 ELSE 0 END) AS 영업부_순이익
    FROM {table_name}
    GROUP BY 날짜
    ORDER BY 날짜
    LIMIT 100;
    """
    
    # 영업부 매출과 순이익을 비교하는 라인 차트 JSON
    DEFAULT_JSON_TEMPLATE = """
    {
        "type": "line",
        "title": "2024년 영업부 매출과 순이익 추이",
        "description": "2024년 영업부의 월별 매출과 순이익을 비교하는 라인 차트입니다. 매출과 순이익 모두 증가하는 추세를 보이고 있습니다.",
        "data": {
            "labels": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"],
            "datasets": [
                {
                    "label": "영업부 매출",
                    "data": [203000000, 214000000, 233000000, 223000000, 247000000, 255000000, 238000000, 245000000, 263000000, 270000000, 280000000, 305000000],
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)"
                },
                {
                    "label": "영업부 순이익",
                    "data": [66000000, 71000000, 83000000, 77000000, 92000000, 95000000, 87000000, 90000000, 98000000, 102000000, 106000000, 115000000],
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)"
                }
            ]
        },
        "options": {
            "responsive": true,
            "maintainAspectRatio": false,
            "scales": {
                "y": {
                    "beginAtZero": true,
                    "title": {
                        "display": true,
                        "text": "금액 (원)"
                    }
                },
                "x": {
                    "title": {
                        "display": true,
                        "text": "월"
                    }
                }
            }
        },
        "figsize": [12, 6]
    }
    """
    
    # 경로 설정
    OUTPUT_DIR = "./chart_outputs"
    RESULTS_DIR = "./results"
    csv_path = "Rating_Test_Data.csv"
    metadata_path = 'metadata.json'
    
    # 웹 앱 설정
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    FLASK_DEBUG = False
    
    BASE_RESULTS_DIR = "./results"
    BASE_OUTPUT_DIR = "./chart_outputs"
    
    @classmethod
    def get_output_dir(cls, username=None):
        if username:
            return os.path.join(cls.BASE_OUTPUT_DIR, f"{username}")
        return cls.BASE_OUTPUT_DIR
    
    @classmethod
    def get_results_dir(cls, username=None):
        if username:
            print(username)
            return os.path.join(cls.BASE_RESULTS_DIR, f"{username}")
        return cls.BASE_RESULTS_DIR

# 설정 변경 함수
def set_llm_mode(mode):
    if isinstance(mode, str):
        try:
            Config.LLM_MODE = LLMMode(mode.lower())
        except ValueError:
            raise ValueError(f"유효하지 않은 LLM 모드: {mode}. 'vllm', 'api', 'offline' 중 하나여야 합니다.")
    elif isinstance(mode, LLMMode):
        Config.LLM_MODE = mode
    else:
        raise TypeError("mode는 문자열 또는 LLMMode 열거형이어야 합니다.")
    
    print(f"LLM 모드가 '{Config.LLM_MODE.value}'로 설정되었습니다.")