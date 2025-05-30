"""
check_environment.py - 실제 환경 구성 확인 스크립트
데이터베이스, LLM, 파일 등 모든 구성요소 상태 체크
"""

import os
import json
import sys
import oracledb
import requests
import pandas as pd
from pathlib import Path

def check_files():
    """필수 파일 존재 확인"""
    print("📁 파일 존재 확인...")
    
    required_files = [
        'Rating_Test_Data.csv',
        'metadata.json',
        'web_app.py',
        'llm_manager.py',
        'data_manager.py',
        'chart_generator.py',
        'config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - 파일이 없습니다")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_python_packages():
    """필수 Python 패키지 확인"""
    print("\n📦 Python 패키지 확인...")
    
    required_packages = [
        'flask',
        'flask_session', 
        'pandas',
        'numpy',
        'matplotlib',
        'oracledb',
        'requests',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - 설치되지 않음")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   설치 명령: pip install {' '.join(missing_packages)}")
    
    return len(missing_packages) == 0

def check_oracle_connection():
    """Oracle 데이터베이스 연결 확인"""
    print("\n🗄️ Oracle 데이터베이스 연결 확인...")
    
    try:
        # Oracle 클라이언트 초기화
        client_lib_dir = r"/home/humandeep/oracle/instantclient_21_8"
        if os.path.exists(client_lib_dir):
            print(f"   ✅ Oracle 클라이언트 경로: {client_lib_dir}")
            try:
                oracledb.init_oracle_client(lib_dir=client_lib_dir)
                print("   ✅ Oracle 클라이언트 초기화 성공")
            except Exception as e:
                print(f"   ⚠️ Oracle 클라이언트 초기화 경고: {e}")
        else:
            print(f"   ❌ Oracle 클라이언트 경로가 없습니다: {client_lib_dir}")
            return False
        
        # 데이터베이스 연결 테스트
        # 원래 운영 서버 연결 정보 (주석 처리)
        # user = "hiq1"
        # password = "hiq11!"
        # dsn = "10.158.122.119/HIQ1DEV"
        
        # 테스트용 로컬 Oracle 연결 정보
        user = "system"
        password = "Test123"
        dsn = "localhost:1521/XE"
        
        print(f"   🔗 연결 시도: {user}@{dsn}")
        
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        
        # 간단한 쿼리 테스트
        cursor = connection.cursor()
        # 운영 테이블 쿼리 (주석 처리)
        # cursor.execute("SELECT COUNT(*) FROM QMS_RAT_YMQT_N WHERE ROWNUM <= 1")
        
        # 테스트용 기본 쿼리
        cursor.execute("SELECT 'Oracle Connection Test' FROM dual")
        result = cursor.fetchone()
        print(f"   📋 쿼리 결과: {result[0]}")
        
        cursor.close()
        connection.close()
        
        print("   ✅ Oracle 데이터베이스 연결 성공")
        return True
        
    except Exception as e:
        print(f"   ❌ Oracle 데이터베이스 연결 실패: {e}")
        return False
        
    except Exception as e:
        print(f"   ❌ Oracle 연결 실패: {e}")
        print("   💡 확인사항:")
        print("      - Oracle 클라이언트 설치")
        print("      - 네트워크 연결")
        print("      - 계정 정보")
        print("      - 방화벽 설정")
        return False

# def check_llm_api():
#     """LLM API 연결 확인"""
#     print("\n🤖 LLM API 연결 확인...")
    
#     api_key = os.environ.get("API_KEY", "")
#     if not api_key:
#         print("   ❌ API_KEY 환경변수가 설정되지 않았습니다")
#         print("   💡 설정 방법: export API_KEY='your-api-key'")
#         return False
    
#     print(f"   ✅ API_KEY 설정됨: {api_key[:10]}...")
    
#     try:
#         # API 엔드포인트 테스트
#         endpoint = "http://dev.assistant.llm.skhynix.com/v1/chat/completions"
#         headers = {
#             'Authorization': f'Bearer {api_key}',
#             'Content-Type': 'application/json'
#         }
        
#         test_payload = {
#             "model": "Qwen3-32B",
#             "messages": [
#                 {"role": "user", "content": "Hello, this is a test message."}
#             ],
#             "max_tokens": 10
#         }
        
#         print(f"   🔗 API 엔드포인트 테스트: {endpoint}")
        
#         response = requests.post(endpoint, headers=headers, json=test_payload, timeout=10)
        
#         if response.status_code == 200:
#             print("   ✅ LLM API 연결 성공")
#             return True
#         else:
#             print(f"   ❌ LLM API 응답 오류: {response.status_code}")
#             print(f"   응답: {response.text[:200]}")
#             return False
            
#     except requests.exceptions.RequestException as e:
#         print(f"   ❌ LLM API 연결 실패: {e}")
#         print("   💡 확인사항:")
#         print("      - 네트워크 연결")
#         print("      - API 키 유효성") 
#         print("      - 엔드포인트 URL")
#         return False
def check_llm_api():
    """LLM API 연결 확인"""
    print("\n🤖 LLM API 연결 확인...")
    
    # 원래 운영 API 설정 (주석 처리)
    # api_key = os.environ.get("API_KEY", "")
    # if not api_key:
    #     print("   ❌ API_KEY 환경변수가 설정되지 않았습니다")
    #     print("   💡 설정 방법: export API_KEY='your-api-key'")
    #     return False
    # 
    # print(f"   ✅ API_KEY 설정됨: {api_key[:10]}...")
    # endpoint = "http://dev.assistant.llm.skhynix.com/v1/chat/completions"
    
    # 테스트용 API 설정
    api_key = "test-api-key"  # 테스트용 더미 키 (어떤 값이든 허용)
    endpoint = "http://localhost:8000/v1/chat/completions"
    
    print(f"   ✅ 테스트 API_KEY 사용: {api_key}")
    
    try:
        # 먼저 헬스 체크
        health_endpoint = "http://localhost:8000/health"
        print(f"   🔍 헬스 체크: {health_endpoint}")
        
        health_response = requests.get(health_endpoint, timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   📊 서버 상태: {health_data.get('status', 'unknown')}")
            print(f"   🤖 모델 로드됨: {health_data.get('model_loaded', False)}")
            
            if not health_data.get('model_loaded', False):
                print("   ⚠️  모델이 아직 로딩 중입니다. 잠시 후 다시 시도하세요.")
                return False
        else:
            print(f"   ❌ 헬스 체크 실패: {health_response.status_code}")
            print("   💡 테스트 서버가 실행 중인지 확인하세요:")
            print("      python test_llm_api_server.py")
            return False
        
        # API 엔드포인트 테스트
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        test_payload = {
            "model": "Qwen2.5-32B-Instruct",  # 실제 모델명 사용
            "messages": [
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful!'"}
            ],
            "max_tokens": 50,
            "temperature": 0.1  # LLMManager와 동일한 낮은 온도 사용
        }
        
        print(f"   🔗 API 엔드포인트 테스트: {endpoint}")
        
        response = requests.post(endpoint, headers=headers, json=test_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # 응답 내용 확인
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print("   ✅ LLM API 연결 성공")
                print(f"   💬 응답 내용: {content[:100]}...")
                
                # 사용량 정보 표시 (있는 경우)
                if 'usage' in result:
                    usage = result['usage']
                    print(f"   📊 토큰 사용량: {usage.get('total_tokens', 'N/A')}")
                
                return True
            else:
                print("   ❌ 응답 형식 오류: choices 필드가 없습니다")
                return False
        else:
            print(f"   ❌ LLM API 응답 오류: {response.status_code}")
            print(f"   📝 응답 내용: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ API 요청 시간 초과 (30초)")
        print("   💡 모델이 큰 경우 응답에 시간이 걸릴 수 있습니다")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 연결 오류: 테스트 서버에 연결할 수 없습니다")
        print("   💡 다음 명령어로 테스트 서버를 시작하세요:")
        print("      python test_llm_api_server.py")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False
            
    except requests.exceptions.Timeout:
        print("   ❌ API 요청 시간 초과 (30초)")
        print("   💡 모델이 큰 경우 응답에 시간이 걸릴 수 있습니다")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 연결 오류: 테스트 서버에 연결할 수 없습니다")
        print("   💡 다음 명령어로 테스트 서버를 시작하세요:")
        print("      python test_llm_api_server.py")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False
    
def check_metadata_format():
    """메타데이터 파일 형식 확인"""
    print("\n📋 메타데이터 파일 형식 확인...")
    
    try:
        with open('metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print("   ✅ JSON 형식 유효")
        
        # 필수 구조 확인
        if 'tables' in metadata:
            print("   ✅ 'tables' 키 존재")
            
            if len(metadata['tables']) > 0:
                first_table = metadata['tables'][0]
                if 'ratings' in first_table:
                    print("   ✅ 'ratings' 정보 존재")
                    ratings = first_table['ratings']
                    
                    if 'actual_rating' in ratings:
                        print("   ✅ 'actual_rating' 정의됨")
                    if 'expected_rating' in ratings:
                        print("   ✅ 'expected_rating' 정의됨")
                        
        print(f"   📊 총 테이블 정의 수: {len(metadata.get('tables', []))}")
        return True
        
    except FileNotFoundError:
        print("   ❌ metadata.json 파일이 없습니다")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON 형식 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 메타데이터 확인 오류: {e}")
        return False

def check_csv_data():
    """CSV 데이터 파일 확인"""
    print("\n📊 CSV 데이터 파일 확인...")
    
    try:
        df = pd.read_csv('Rating_Test_Data.csv')
        print(f"   ✅ CSV 로드 성공: {len(df)} 행, {len(df.columns)} 열")
        print(f"   📋 컬럼: {list(df.columns)}")
        
        # 필수 컬럼 확인
        required_columns = ['HIQ1_APP_CD', 'HIQ1_CUST_CD', 'YM_QT']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"   ⚠️ 권장 컬럼 누락: {missing_columns}")
        else:
            print("   ✅ 필수 컬럼 모두 존재")
            
        return True
        
    except FileNotFoundError:
        print("   ❌ Rating_Test_Data.csv 파일이 없습니다")
        return False
    except Exception as e:
        print(f"   ❌ CSV 파일 오류: {e}")
        return False

def check_directories():
    """필요한 디렉토리 확인 및 생성"""
    print("\n📁 디렉토리 구조 확인...")
    
    required_dirs = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'chart_outputs',
        'results'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ {dir_path} (생성됨)")
            except Exception as e:
                print(f"   ❌ {dir_path} 생성 실패: {e}")
                return False
    
    return True

def main():
    """전체 환경 확인"""
    print("🔍 LLM 기반 차트 생성 시스템 환경 확인")
    print("=" * 60)
    
    checks = [
        ("파일", check_files),
        ("Python 패키지", check_python_packages),
        ("디렉토리", check_directories),
        ("CSV 데이터", check_csv_data),
        ("메타데이터", check_metadata_format),
        ("Oracle DB", check_oracle_connection),
        ("LLM API", check_llm_api)
    ]
    
    results = {}
    
    for name, check_func in checks:
        results[name] = check_func()
    
    print("\n" + "=" * 60)
    print("📋 환경 확인 결과:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"   {name:<15}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 모든 환경 확인 완료! 시스템을 실행할 수 있습니다.")
        print("\n🚀 실행 명령:")
        print("   python web_app.py --csv Rating_Test_Data.csv --metadata metadata.json --llm-mode api")
    else:
        print("⚠️ 일부 환경 설정이 필요합니다.")
        print("\n💡 해결 후 다시 확인해주세요.")
    
    return all_passed

if __name__ == "__main__":
    main()