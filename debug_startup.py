#!/usr/bin/env python3
"""
debug_startup.py - 웹 앱 시작 오류 디버깅
실행 중단 원인을 상세히 분석
"""

import os
import sys
import traceback
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def check_files():
    """필수 파일 존재 확인"""
    print("📁 필수 파일 확인...")
    
    files_to_check = [
        'Rating_Test_Data.csv',
        'metadata.json',
        'web_app.py',
        'config.py',
        'main.py',
        'llm_manager.py',
        'data_manager.py',
        'chart_generator.py'
    ]
    
    missing_files = []
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} - 파일이 없습니다")
            missing_files.append(file)
    
    return missing_files

def check_directories():
    """필요한 디렉토리 확인"""
    print("\n📁 디렉토리 확인...")
    
    dirs_to_check = [
        'templates',
        'static',
        'chart_outputs', 
        'results'
    ]
    
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️ {dir_name}/ - 생성됩니다")
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"   ✅ {dir_name}/ 생성 완료")
            except Exception as e:
                print(f"   ❌ {dir_name}/ 생성 실패: {e}")

def check_imports():
    """모듈 import 확인"""
    print("\n📦 모듈 import 확인...")
    
    modules_to_check = [
        ('flask', 'Flask'),
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('matplotlib.pyplot', 'plt'),
        ('oracledb', None),
        ('requests', None)
    ]
    
    import_errors = []
    for module_name, alias in modules_to_check:
        try:
            if alias:
                exec(f"import {module_name} as {alias}")
            else:
                exec(f"import {module_name}")
            print(f"   ✅ {module_name}")
        except ImportError as e:
            print(f"   ❌ {module_name} - {e}")
            import_errors.append(module_name)
    
    return import_errors

def test_config_loading():
    """설정 파일 로딩 테스트"""
    print("\n🔧 설정 파일 테스트...")
    
    try:
        # config 모듈 import 시도
        import config
        print("   ✅ config.py import 성공")
        
        # Config 클래스 확인
        if hasattr(config, 'Config'):
            print("   ✅ Config 클래스 존재")
            
            # 기본 속성 확인
            required_attrs = ['LLM_MODE', 'csv_path', 'metadata_path']
            for attr in required_attrs:
                if hasattr(config.Config, attr):
                    value = getattr(config.Config, attr)
                    print(f"   ✅ Config.{attr} = {value}")
                else:
                    print(f"   ❌ Config.{attr} 누락")
        else:
            print("   ❌ Config 클래스 없음")
            
    except Exception as e:
        print(f"   ❌ config 로딩 실패: {e}")
        traceback.print_exc()

def test_metadata_file():
    """메타데이터 파일 테스트"""
    print("\n📋 메타데이터 파일 테스트...")
    
    try:
        import json
        
        if os.path.exists('metadata.json'):
            with open('metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"   ✅ metadata.json 로드 성공")
            print(f"   📊 메타데이터 키: {list(metadata.keys())}")
            
            if 'tables' in metadata:
                print(f"   📋 테이블 수: {len(metadata['tables'])}")
            else:
                print("   ⚠️ 'tables' 키가 없습니다")
                
        else:
            print("   ❌ metadata.json 파일이 없습니다")
            
    except Exception as e:
        print(f"   ❌ 메타데이터 로딩 실패: {e}")

def test_csv_file():
    """CSV 파일 테스트"""
    print("\n📊 CSV 파일 테스트...")
    
    try:
        import pandas as pd
        
        if os.path.exists('Rating_Test_Data.csv'):
            df = pd.read_csv('Rating_Test_Data.csv')
            print(f"   ✅ CSV 로드 성공: {len(df)} 행, {len(df.columns)} 열")
            print(f"   📋 컬럼: {list(df.columns)[:5]}...")  # 처음 5개만
        else:
            print("   ❌ Rating_Test_Data.csv 파일이 없습니다")
            
    except Exception as e:
        print(f"   ❌ CSV 로딩 실패: {e}")

def test_web_app_import():
    """web_app 모듈 import 테스트"""
    print("\n🌐 web_app.py import 테스트...")
    
    try:
        # 현재 디렉토리를 Python 경로에 추가
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.append(str(current_dir))
        
        print("   🔄 web_app 모듈 import 중...")
        import web_app
        print("   ✅ web_app.py import 성공")
        
        # 주요 함수 확인
        required_functions = ['create_app', 'main']
        for func_name in required_functions:
            if hasattr(web_app, func_name):
                print(f"   ✅ {func_name} 함수 존재")
            else:
                print(f"   ❌ {func_name} 함수 없음")
                
    except Exception as e:
        print(f"   ❌ web_app import 실패: {e}")
        traceback.print_exc()

def test_manual_startup():
    """수동 시작 테스트"""
    print("\n🚀 수동 시작 테스트...")
    
    try:
        # 환경 설정
        os.environ['API_KEY'] = 'test-key'
        
        # web_app의 main 함수를 직접 호출하는 대신 단계별 테스트
        print("   1️⃣ 모듈 import...")
        
        import config
        from config import Config, set_llm_mode
        
        print("   2️⃣ LLM 모드 설정...")
        set_llm_mode('offline')  # 안전한 오프라인 모드로 테스트
        
        print("   3️⃣ 파일 경로 설정...")
        Config.csv_path = 'Rating_Test_Data.csv'
        Config.metadata_path = 'metadata.json'
        
        print("   4️⃣ Flask 앱 생성 시도...")
        from web_app import create_app
        
        app = create_app(
            csv_path='Rating_Test_Data.csv',
            metadata_path='metadata.json',
            llm_mode='offline'
        )
        
        print("   ✅ Flask 앱 생성 성공!")
        print("   💡 실제 서버 시작 없이 생성만 테스트 완료")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 수동 시작 실패: {e}")
        traceback.print_exc()
        return False

def create_minimal_files():
    """최소한의 필수 파일 생성"""
    print("\n🔧 최소 필수 파일 생성...")
    
    # 최소 metadata.json 생성
    if not os.path.exists('metadata.json'):
        minimal_metadata = {
            "tables": [{
                "ratings": {
                    "actual_rating": {
                        "description": "실제 레이팅 데이터"
                    },
                    "expected_rating": {
                        "description": "예상 레이팅 데이터"
                    }
                }
            }]
        }
        
        try:
            import json
            with open('metadata.json', 'w', encoding='utf-8') as f:
                json.dump(minimal_metadata, f, ensure_ascii=False, indent=2)
            print("   ✅ 최소 metadata.json 생성")
        except Exception as e:
            print(f"   ❌ metadata.json 생성 실패: {e}")
    
    # 최소 CSV 파일 생성
    if not os.path.exists('Rating_Test_Data.csv'):
        minimal_csv = """HIQ1_APP_CD,HIQ1_CUST_CD,YM_QT,ACTUAL,SCORE
CLIENT,G150,202401,3,85
SERVER,G113,202401,2,92
HBM,G669,202401,4,78"""
        
        try:
            with open('Rating_Test_Data.csv', 'w', encoding='utf-8') as f:
                f.write(minimal_csv)
            print("   ✅ 최소 Rating_Test_Data.csv 생성")
        except Exception as e:
            print(f"   ❌ CSV 파일 생성 실패: {e}")

def main():
    """메인 디버깅 함수"""
    print("🔍 웹 앱 시작 오류 디버깅")
    print("=" * 60)
    
    # 1. 파일 확인
    missing_files = check_files()
    
    # 2. 디렉토리 확인
    check_directories()
    
    # 3. 모듈 import 확인
    import_errors = check_imports()
    
    # 4. 설정 파일 테스트
    test_config_loading()
    
    # 5. 데이터 파일 테스트
    test_metadata_file()
    test_csv_file()
    
    # 6. web_app import 테스트
    test_web_app_import()
    
    print("\n" + "=" * 60)
    print("📋 디버깅 결과 요약:")
    print("=" * 60)
    
    # 문제점 요약
    issues = []
    
    if missing_files:
        issues.append(f"누락된 파일: {', '.join(missing_files)}")
    
    if import_errors:
        issues.append(f"Import 오류: {', '.join(import_errors)}")
    
    if issues:
        print("❌ 발견된 문제점:")
        for issue in issues:
            print(f"   - {issue}")
        
        print("\n🔧 해결 방법:")
        
        if missing_files:
            print("   1. 누락된 파일 생성 시도...")
            create_minimal_files()
        
        if import_errors:
            print(f"   2. 패키지 설치: pip install {' '.join(import_errors)}")
    
    else:
        print("✅ 기본 파일 및 모듈 확인 완료")
        
        # 수동 시작 테스트
        print("\n🧪 수동 시작 테스트 진행...")
        if test_manual_startup():
            print("\n💡 해결책:")
            print("   파일과 모듈은 정상입니다.")
            print("   web_app.py 내부에서 조용한 오류가 발생할 가능성이 있습니다.")
            print("   다음 명령으로 더 자세한 로그를 확인하세요:")
            print("   python web_app.py --csv Rating_Test_Data.csv --metadata metadata.json --llm-mode offline --debug")
        else:
            print("\n❌ 수동 테스트도 실패했습니다.")
            print("   더 깊은 문제가 있을 수 있습니다.")

if __name__ == "__main__":
    main()