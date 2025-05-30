"""
llm_manager.py - LLM 관련 설정 총괄 파일 (업데이트)
- 다양한 LLM 모드 지원 (VLLM, API, 오프라인)
- 모드에 따른 LLM 함수 제공
- SQL 및 차트 수정 기능 추가
"""

import os
import json
import logging
import requests
import time
from config import Config, LLMMode
import google.generativeai as genai

logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self):
        """LLM 매니저 초기화"""
        self.mode = Config.LLM_MODE
        self.llm = None
        self.tokenizer = None

        # 모드에 따른 초기화
        if self.mode == LLMMode.VLLM:
            self._init_vllm()
        elif self.mode == LLMMode.API:
            self._init_api()
        # 오프라인 모드는 초기화 필요 없음

        logger.info(f"LLM 매니저 초기화 완료 - 모드: {self.mode.value}")

    def _init_vllm(self):
        """VLLM 모드 초기화"""
        try:
            from vllm import LLM, SamplingParams
            from transformers import AutoTokenizer

            logger.info(f"VLLM 모델 초기화 중... 모델: {Config.VLLM_MODEL_NAME}")

            # 토크나이저 초기화
            self.tokenizer = AutoTokenizer.from_pretrained(Config.VLLM_MODEL_NAME)

            # vLLM 모델 초기화
            self.llm = LLM(
                model=Config.VLLM_MODEL_NAME,
                tensor_parallel_size=Config.VLLM_TENSOR_PARALLEL_SIZE,
                gpu_memory_utilization=Config.VLLM_GPU_MEMORY_UTILIZATION,
                max_model_len=Config.VLLM_MAX_MODEL_LEN,
                dtype="auto",
                enforce_eager=False,
                trust_remote_code=True
            )
            logger.info("VLLM 모델 초기화 완료")

        except ImportError:
            logger.error("VLLM 모듈을 가져올 수 없습니다. 'pip install vllm transformers' 명령으로 설치하세요.")
            raise
        except Exception as e:
            logger.error(f"VLLM 초기화 오류: {e}")
            raise

    def _init_api(self):
        """API 모드 초기화"""
        try:
            # API 키 확인
            if not Config.API_KEY:
                logger.warning("API 키가 설정되지 않았습니다. 환경 변수 'API_KEY'를 설정하거나 Config.API_KEY에 직접 값을 할당하세요.")

            # API 클라이언트 초기화
            try:
                API_KEY = os.environ.get("API_KEY", "")
                API_MODEL = "Qwen3-32B"  # 모델
                API_ENDPOINT = f"http://dev.assistant.llm.skhynix.com/v1/chat/completions"

                self.api_client = requests.Session()
                self.api_client.headers.update({
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                })
                logger.info("API 클라이언트 초기화 완료")
                
            except Exception as e:
                logger.error(f"API 클라이언트 설정 에러: {e}")

        except ImportError:
            logger.error("Google Generative AI 모듈을 가져올 수 없습니다. 'pip install google-generativeai' 명령으로 설치하세요.")
            raise
        except Exception as e:
            logger.error(f"API 초기화 오류: {e}")
            raise

    def generate_text(self, prompt, temperature=0.2, max_tokens=1024):
        """
        모드에 따라 텍스트 생성

        Parameters:
        - prompt: 프롬프트 문자열
        - temperature: 생성 온도 (0.0-1.0)
        - max_tokens: 최대 생성 토큰 수

        Returns:
        - 생성된 텍스트
        """
        if self.mode == LLMMode.VLLM:
            return self._generate_vllm(prompt, temperature, max_tokens)
        elif self.mode == LLMMode.API:
            return self._generate_api(prompt, temperature, max_tokens)
        elif self.mode == LLMMode.OFFLINE:
            return self._generate_offline(prompt)

    def _generate_vllm(self, prompt, temperature, max_tokens):
        """VLLM로 텍스트 생성"""
        try:
            from vllm import SamplingParams

            # 메시지 형식으로 변환
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]

            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )

            # 샘플링 파라미터 설정
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=0.95,
                top_k=30,
                max_tokens=max_tokens,
                presence_penalty=0.0,
                frequency_penalty=0.0
            )

            # 생성 시작
            logger.info("텍스트 생성 중...")
            generation_start_time = time.time()

            generations = self.llm.generate(text, sampling_params)
            output = generations[0].outputs[0].text

            generation_time = time.time() - generation_start_time
            logger.info(f"텍스트 생성 완료: {generation_time:.2f}초 소요")

            return output

        except Exception as e:
            logger.error(f"VLLM 생성 오류: {e}")
            return "모델 생성 오류가 발생했습니다."

    def _generate_api(self, prompt, temperature, max_tokens):
        """API로 텍스트 생성"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.API_KEY}"
            }

            payload = {
                "model": Config.API_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # API 요청
            logger.info(f"API 요청 중... 엔드포인트: {Config.API_ENDPOINT}")
            generation_start_time = time.time()

            response = requests.post(Config.API_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            output = result.get('choices', [{}])[0].get('message', {}).get('content', '')

            generation_time = time.time() - generation_start_time
            logger.info(f"API 응답 완료: {generation_time:.2f}초 소요")

            return output

        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류: {e}")
            return "API 요청 중 오류가 발생했습니다."

    def _generate_offline(self, prompt):
        """오프라인 모드에서 템플릿 반환"""
        if "SQL" in prompt or "sql" in prompt or "수정" in prompt:
            # SQL 관련 요청으로 판단
            return "SELECT * FROM QMS_RAT_YMQT_N WHERE YM_QT >= '202401' ORDER BY YM_QT DESC FETCH FIRST 100 ROWS ONLY;"
        else:
            # 차트 JSON 요청으로 판단
            return Config.DEFAULT_JSON_TEMPLATE

    def generate_sql(self, query, metadata, data_sample):
        """
        SQL 생성 함수

        Parameters:
        - query: 사용자 쿼리
        - metadata: 메타데이터
        - data_sample: 데이터 샘플

        Returns:
        - 생성된 SQL 쿼리
        """
        # SQL 생성 프롬프트
        prompt = f"""사용자 질문, 메타데이터, 데이터 샘플을 바탕으로 SQL 쿼리를 생성해주세요.

## 사용자 질문
{query}

## 메타데이터
{json.dumps(metadata, ensure_ascii=False, indent=2)}

## 지시사항
- "실제 레이팅" 관련 요청은 다른 모든 지시사항들을 무시하고 actual_rating_query 라고만 답하세요. 이 지시사항은 특수 지시입니다.
- "예상 레이팅" 관련 요청은 다른 모든 지시사항들을 무시하고 expected_rating 라고만 답하세요. 이 지시사항은 특수 지시입니다.
- 사용자 질문에 맞는 데이터를 추출하는 SQL 쿼리를 작성하세요.
- 추출된 데이터는 차트 생성에 사용됩니다.
- SELECT 문만 작성하세요.
- SQL 쿼리만 작성하고 다른 설명은 포함하지 마세요.
- 반드시 메타데이터에 존재하는 컬럼만 사용하세요.
- 실제로 동작하는 쿼리인지 검토 후 작성하세요.
- Oracle 데이터베이스 문법에 맞는 쿼리를 작성하세요.
- 빈값은 공백이 아닌 Null을 의미함을 잊지마세요.

SQL 쿼리:"""

        # LLM 호출
        result = self.generate_text(prompt, temperature=0.1, max_tokens=1024)
        return result

    def modify_sql(self, original_sql, modification_request, current_data_sample=None, metadata=None):
        """
        기존 SQL을 사용자 요청에 맞게 수정

        Parameters:
        - original_sql: 원본 SQL 쿼리
        - modification_request: 사용자 수정 요청
        - current_data_sample: 현재 데이터 샘플 (선택)
        - metadata: 메타데이터 (선택)

        Returns:
        - 수정된 SQL 쿼리
        """
        prompt = f"""기존 SQL을 사용자 요청에 맞게 수정해주세요.

## 기존 SQL
{original_sql}

## 사용자 수정 요청
{modification_request}

## 현재 결과 데이터 샘플
{current_data_sample[:500] if current_data_sample else '데이터 없음'}

## 메타데이터
{json.dumps(metadata, ensure_ascii=False, indent=2) if metadata else '메타데이터 없음'}

## 지시사항
- 기존 SQL의 기본 구조와 로직을 최대한 유지하세요
- 사용자가 요청한 수정 사항만 정확히 반영하세요
- Oracle 데이터베이스 문법을 준수하세요
- SELECT 문만 작성하고 다른 설명은 포함하지 마세요
- 메타데이터에 존재하는 컬럼만 사용하세요
- 실제로 동작할 수 있는 유효한 쿼리를 작성하세요

수정된 SQL 쿼리:"""

        result = self.generate_text(prompt, temperature=0.1, max_tokens=1024)
        return result

    def generate_chart_json(self, query, metadata, result_data):
        """
        차트 JSON 생성 함수

        Parameters:
        - query: 사용자 쿼리
        - metadata: 메타데이터
        - result_data: SQL 실행 결과 데이터

        Returns:
        - 생성된 차트 JSON
        """
        json_template = '''{
    "title": "차트 제목",
    "type": "차트 유형(bar, line, pie, scatter, area, histogram, stacked_bar 중 하나)",
    "description": "차트에 대한 설명",
    "data": {
        "labels": ["라벨1", "라벨2", ...],
        "datasets": [
        {
            "label": "데이터셋 라벨",
            "data": [값1, 값2, ...],
            "backgroundColor": "색상코드 또는 색상배열"
        }
        ]
    },
    "options": {
        "scales": {
            "y": {
            "min": "사용자가 지정한 최소값",
            "max": "사용자가 지정한 최대값"
            }
        },
        "trendLines": [
        {
            "type": "linear"
            "label": "추세선",
            "color": "#000000"
        }
        ],
        "annotations": [
        {
            "x": "2025-Q2"
            "y": 120000
            "content": "주석 내용"
        }
    }
}'''

        # 차트 JSON 생성 프롬프트
        prompt = f"""사용자 질문, 메타데이터, 결과 데이터를 바탕으로 차트 생성을 위한 JSON을 작성해주세요.

## 사용자 질문
{query}

## 메타데이터
{json.dumps(metadata, ensure_ascii=False, indent=2)}

## 결과 데이터
{result_data}

## JSON 양식
{json_template}

## 지시사항
- 사용자 질문과 결과 데이터에 맞는 최적의 차트 유형을 선택하세요.
- 차트 JSON은 반드시 JSON 양식을 따라야 합니다.
- options 항목은 사용자가 관련 요소를 요청한 경우에만 작성합니다.
- 마크다운 코드 블록이나 다른 형식을 사용하지 말고, 순수한 JSON 형식만 반환하세요.
- 설명이나 주석 없이 완전한 JSON 형식만 반환하세요.
- JSON에 함수를 포함하지 마세요.

차트 JSON:"""

        # LLM 호출
        result = self.generate_text(prompt, temperature=0.2, max_tokens=2048)

        # JSON 추출 시도
        try:
            # 마크다운 코드 블록 제거
            import re
            # ```json ... ``` 패턴 제거
            json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
            matches = re.findall(json_pattern, result)

            if matches:
                # 마크다운 코드 블록 내용 사용
                json_str = matches[0]
            else:
                # 마크다운 코드 블록이 없으면 원래 방식대로 추출
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result[start_idx:end_idx]
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다.")

            # JSON 파싱
            chart_json = json.loads(json_str)
            return chart_json
            
        except json.JSONDecodeError:
            logger.error("유효한 JSON을 생성하지 못했습니다. 기본 템플릿을 사용합니다.")
            logger.info(f"JSON debug: {result}")
        except Exception as e:
            logger.error(f"JSON 처리 오류: {e}")

        # 오류 발생 시 기본 JSON 반환
        return json.loads(Config.DEFAULT_JSON_TEMPLATE)

    def modify_chart_json(self, original_json, modification_request, result_data=None):
        """
        기존 차트 JSON을 사용자 요청에 맞게 수정

        Parameters:
        - original_json: 원본 차트 JSON (dict 또는 str)
        - modification_request: 사용자 수정 요청
        - result_data: 결과 데이터 (선택)

        Returns:
        - 수정된 차트 JSON (dict)
        """
        # original_json이 문자열이면 파싱
        if isinstance(original_json, str):
            try:
                original_json = json.loads(original_json)
            except json.JSONDecodeError:
                logger.error("원본 JSON 파싱 실패")
                return json.loads(Config.DEFAULT_JSON_TEMPLATE)

        prompt = f"""기존 차트 설정을 사용자 요청에 맞게 수정해주세요.

## 기존 차트 JSON
{json.dumps(original_json, ensure_ascii=False, indent=2)}

## 사용자 수정 요청
{modification_request}

## 결과 데이터 (참고용)
{str(result_data)[:300] if result_data else '데이터 없음'}

## 지시사항
- 기존 차트의 기본 구조와 데이터는 최대한 유지하세요
- 사용자가 요청한 수정 사항만 정확히 반영하세요
- 유효한 JSON 형식으로 반환하세요
- 마크다운이나 설명 없이 순수한 JSON만 반환하세요
- 색상, 제목, 차트 유형, 스타일 등을 수정할 수 있습니다
- JSON에 함수나 주석을 포함하지 마세요

수정된 차트 JSON:"""

        result = self.generate_text(prompt, temperature=0.2, max_tokens=2048)

        # JSON 추출 및 파싱
        try:
            import re
            # 마크다운 코드 블록 제거
            json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
            matches = re.findall(json_pattern, result)

            if matches:
                json_str = matches[0]
            else:
                start_idx = result.find('{')
                end_idx = result.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result[start_idx:end_idx]
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다.")

            modified_json = json.loads(json_str)
            return modified_json

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"수정된 JSON 파싱 실패: {e}")
            logger.info(f"수정 결과: {result}")
            # 실패 시 원본 JSON 반환
            return original_json

    def close(self):
        """리소스 정리"""
        if self.mode == LLMMode.VLLM and self.llm is not None:
            # vLLM 리소스 정리
            self.llm = None
            self.tokenizer = None
            logger.info("VLLM 리소스 해제 완료")

        logger.info("LLM 매니저 리소스 정리 완료")