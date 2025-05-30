#!/usr/bin/env python3
"""
테스트용 LLM API 서버
실제 LLM 모델을 사용하여 API 요청에 응답하는 테스트 서버
"""

from flask import Flask, request, jsonify
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
import logging
import time
import os
import threading

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 글로벌 변수
llm = None
tokenizer = None
model_loaded = False

def load_model():
    """모델 및 토크나이저 로드"""
    global llm, tokenizer, model_loaded
    
    try:
        # 모델 설정 - LLMManager와 동일한 설정 사용
        model_name = "Qwen/Qwen3-32B-AWQ"  # Qwen32B 모델 사용
        
        logger.info(f"Loading model: {model_name}")
        
        # 토크나이저 먼저 로드
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info("Tokenizer loaded successfully.")
        
        # vLLM 모델 로드 - LLMManager와 동일한 설정
        logger.info("Loading vLLM model...")
        llm = LLM(
            model=model_name,
            tensor_parallel_size=2,  # 2개 GPU 사용 (Config와 동일)
            gpu_memory_utilization=0.85,  # 메모리 사용량 조절
            max_model_len=16384,  # 최대 컨텍스트 길이
            dtype="auto",  # 자동 데이터 타입
            enforce_eager=False,  # 성능 최적화를 위해 TorchScript 사용
            trust_remote_code=True  # 원격 모델 코드 신뢰
        )
        
        model_loaded = True
        logger.info("Model and tokenizer loaded successfully.")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        model_loaded = False

# 서버 시작 시 별도 스레드에서 모델 로드
threading.Thread(target=load_model, daemon=True).start()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy" if model_loaded else "loading",
        "model_loaded": model_loaded,
        "timestamp": time.time()
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI 호환 채팅 완성 API"""
    
    # 모델 로딩 상태 확인
    if not model_loaded:
        return jsonify({
            "error": {
                "message": "Model is still loading. Please wait and try again.",
                "type": "model_loading_error",
                "code": "model_not_ready"
            }
        }), 503
    
    try:
        # 요청 데이터 파싱
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": {
                    "message": "Invalid JSON in request body",
                    "type": "invalid_request_error"
                }
            }), 400
        
        # 필수 필드 확인
        messages = data.get('messages', [])
        if not messages:
            return jsonify({
                "error": {
                    "message": "Messages field is required",
                    "type": "invalid_request_error"
                }
            }), 400
        
        # 요청 파라미터 추출
        model_name = data.get('model', 'Qwen3-32B')
        max_tokens = data.get('max_tokens', 2048)
        temperature = data.get('temperature', 0.6)
        top_p = data.get('top_p', 0.95)
        
        logger.info(f"Processing chat completion request with {len(messages)} messages")
        
        # 시스템 메시지가 없으면 기본 시스템 메시지 추가
        if not any(msg.get('role') == 'system' for msg in messages):
            system_message = {
                "role": "system", 
                "content": "You are a helpful assistant."
            }
            messages = [system_message] + messages
        
        # 채팅 템플릿 적용 - LLMManager와 동일한 방식
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # QwQ 모델 특성 비활성화
        )
        
        logger.info("Generating response...")
        generation_start_time = time.time()
        
        # vLLM 샘플링 파라미터 설정 - LLMManager와 동일한 설정
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            top_k=30,  # LLMManager와 동일
            max_tokens=max_tokens,
            presence_penalty=0.0,  # LLMManager와 동일
            frequency_penalty=0.0  # LLMManager와 동일
        )
        
        # 텍스트 생성
        generations = llm.generate(text, sampling_params)
        output = generations[0].outputs[0].text
        
        generation_time = time.time() - generation_start_time
        logger.info(f"Generation completed in {generation_time:.2f} seconds")
        
        # OpenAI 형식의 응답 생성
        response = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": output
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(text.split()),  # 대략적인 토큰 수
                "completion_tokens": len(output.split()),  # 대략적인 토큰 수
                "total_tokens": len(text.split()) + len(output.split())
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        return jsonify({
            "error": {
                "message": f"Internal server error: {str(e)}",
                "type": "internal_error"
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """사용 가능한 모델 목록"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "Qwen2.5-32B-Instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "test-server"
            },
            {
                "id": "Qwen3-32B",
                "object": "model", 
                "created": int(time.time()),
                "owned_by": "test-server"
            }
        ]
    })

@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        "error": {
            "message": "Not found",
            "type": "invalid_request_error"
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    return jsonify({
        "error": {
            "message": "Internal server error",
            "type": "internal_error"
        }
    }), 500

if __name__ == '__main__':
    print("🚀 테스트용 LLM API 서버 시작")
    print("=" * 50)
    print("📝 사용 가능한 엔드포인트:")
    print("   GET  /health - 헬스 체크")
    print("   GET  /v1/models - 모델 목록")
    print("   POST /v1/chat/completions - 채팅 완성")
    print("=" * 50)
    print("⚠️  모델 로딩에 시간이 걸릴 수 있습니다.")
    print("   /health 엔드포인트로 로딩 상태를 확인하세요.")
    print("=" * 50)
    
    # 개발 서버 실행 (운영에서는 gunicorn 등 사용 권장)
    app.run(
        host='0.0.0.0',  # 모든 인터페이스에서 접근 가능
        port=8000,       # 포트 8000 사용
        debug=False,     # 디버그 모드 비활성화 (모델 로딩 안정성)
        threaded=True    # 멀티스레드 지원
    )