"""
web_app.py - 차트 생성 시스템 웹 인터페이스 (업데이트된 프로세스)
- Flask 기반 웹 애플리케이션
- 단계별 개선 프로세스 지원
- 히스토리 기반 네비게이션
"""

import os
import sys
import json
import base64
from pathlib import Path
import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory, send_file
from flask_session import Session
import pandas as pd
import numpy as np
from threading import Lock
from collections import defaultdict
import shutil

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# 내부 모듈 가져오기
from config import Config, LLMMode, set_llm_mode
from main import ChartGenerationApp

app = Flask(__name__)

# 세션 설정
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 실제 운영시 변경 필요
Session(app)

# 사용자별 chart_app 인스턴스 저장
user_chart_apps = defaultdict(lambda: None)
user_chart_apps_lock = Lock()


def get_chart_app_for_user(username):
    with user_chart_apps_lock:
        if user_chart_apps[username] is None:
            user_chart_apps[username] = ChartGenerationApp(
                csv_path=Config.csv_path,
                metadata_path=Config.metadata_path,
                output_dir=Config.get_output_dir(username),
                results_dir=Config.get_results_dir(username),
                llm_mode=Config.LLM_MODE.value,
                username=username
            )
        return user_chart_apps[username]


@app.route('/')
def index():
    """메인 페이지 리다이렉션"""
    return render_template('index.html', llm_mode=Config.LLM_MODE.value, username='default')


@app.route('/<username>')
def user_page(username):
    """사용자별 메인 페이지"""
    logger.info(f"사용자 '{username}'가 접속했습니다.")
    session['username'] = username
    return render_template('index.html', llm_mode=Config.LLM_MODE.value, username=username)


@app.route('/<username>/get_predefined_queries')
def get_predefined_queries(username):
    """미리 정의된 쿼리 목록 반환"""
    try:
        with open(Config.metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # metadata에서 ratings 정보 추출하여 미리 정의된 쿼리 생성
        predefined_queries = []
        
        # tables의 첫 번째 항목에서 ratings 정보 확인
        if 'tables' in metadata and len(metadata['tables']) > 0:
            first_table = metadata['tables'][0]
            if 'ratings' in first_table:
                ratings = first_table['ratings']
                
                for rating_type, rating_info in ratings.items():
                    predefined_queries.append({
                        'id': rating_type,
                        'name': rating_type.replace('_', ' ').title(),
                        'description': rating_info.get('description', ''),
                        'estimated_rows': '100-1000',  # 예상 행 수
                        'category': 'rating'
                    })
        
        # 추가 예시 쿼리들
        additional_queries = [
            {
                'id': 'customer_performance_2024',
                'name': '2024년 고객별 실적',
                'description': '2024년 각 고객별 실적 데이터를 조회합니다.',
                'estimated_rows': '200-500',
                'category': 'performance'
            },
            {
                'id': 'quarterly_amt_analysis',
                'name': '분기별 AMT 분석',
                'description': '분기별 AMT(매출액) 데이터를 분석합니다.',
                'estimated_rows': '50-200',
                'category': 'financial'
            }
        ]
        
        predefined_queries.extend(additional_queries)
        
        return jsonify(predefined_queries)
        
    except Exception as e:
        logger.error(f"미리 정의된 쿼리 로드 오류: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/<username>/execute_predefined_query', methods=['POST'])
def execute_predefined_query(username):
    """미리 정의된 쿼리 실행"""
    try:
        query_id = request.form.get('query_id')
        if not query_id:
            return jsonify({'error': '쿼리 ID가 필요합니다.'}), 400

        chart_app = get_chart_app_for_user(username)
        
        # 미리 정의된 SQL 쿼리 매핑
        predefined_queries = {
            'actual_rating': """
                SELECT r.HIQ1_CUST_CD as customer_code,
                       CASE r.HIQ1_CUST_CD 
                           WHEN 'G113' THEN 'GOOGLE'
                           WHEN 'G150' THEN 'APPLE' 
                           WHEN 'G669' THEN 'AMD'
                           WHEN 'G932' THEN 'AMAZON'
                           WHEN 'G118' THEN 'HUAWEI'
                           WHEN 'G010' THEN 'HP INC'
                           WHEN 'G021' THEN 'ACER'
                           WHEN 'G163' THEN 'MICROSOFT'
                           WHEN 'G020' THEN 'DELL'
                           WHEN 'G959' THEN 'XIAOMI'
                           ELSE r.HIQ1_CUST_CD
                       END as customer_name,
                       r.HIQ1_APP_CD as app_type,
                       r.YM_QT as quarter,
                       r.ACTUAL as actual_rating,
                       r.SCORE as score,
                       r.EXPECTED_DATE as expected_date
                FROM QMS_RAT_YMQT_N r
                WHERE r.ACTUAL IS NOT NULL
                ORDER BY r.YM_QT DESC, TO_NUMBER(r.SCORE) DESC
            """,
            'expected_rating': """
                SELECT r.HIQ1_CUST_CD as customer_code,
                       CASE r.HIQ1_CUST_CD 
                           WHEN 'G113' THEN 'GOOGLE'
                           WHEN 'G150' THEN 'APPLE' 
                           WHEN 'G669' THEN 'AMD'
                           WHEN 'G932' THEN 'AMAZON'
                           WHEN 'G118' THEN 'HUAWEI'
                           WHEN 'G010' THEN 'HP INC'
                           WHEN 'G021' THEN 'ACER'
                           WHEN 'G163' THEN 'MICROSOFT'
                           WHEN 'G020' THEN 'DELL'
                           WHEN 'G959' THEN 'XIAOMI'
                           ELSE r.HIQ1_CUST_CD
                       END as customer_name,
                       r.HIQ1_APP_CD as app_type,
                       r.YM_QT as quarter,
                       r.FORECAST as expected_rating,
                       r.REVENUE as revenue_rating,
                       r.EXPECTED_DATE as expected_date
                FROM QMS_RAT_YMQT_N r
                WHERE r.FORECAST IS NOT NULL
                ORDER BY r.EXPECTED_DATE DESC, r.YM_QT DESC
            """,
            'customer_performance_2024': """
                SELECT g.HIQ1_CUST_CD as customer_code,
                       CASE g.HIQ1_CUST_CD 
                           WHEN 'G113' THEN 'GOOGLE'
                           WHEN 'G150' THEN 'APPLE' 
                           WHEN 'G669' THEN 'AMD'
                           WHEN 'G932' THEN 'AMAZON'
                           WHEN 'G118' THEN 'HUAWEI'
                           WHEN 'G010' THEN 'HP INC'
                           WHEN 'G021' THEN 'ACER'
                           WHEN 'G163' THEN 'MICROSOFT'
                           WHEN 'G020' THEN 'DELL'
                           WHEN 'G959' THEN 'XIAOMI'
                           ELSE g.HIQ1_CUST_CD
                       END as customer_name,
                       g.HIQ1_APP_CD as app_type,
                       g.AMT as performance_amount,
                       g.ACTUAL as actual_rating,
                       g.SCORE as performance_score,
                       g.PLAN_QUARTER as quarter
                FROM QMS_GBW_VIEW g
                WHERE g.PLAN_QUARTER LIKE '2024%'
                ORDER BY g.AMT DESC, TO_NUMBER(g.SCORE) DESC
            """,
            'quarterly_amt_analysis': """
                SELECT g.PLAN_QUARTER as quarter,
                       g.HIQ1_APP_CD as app_type,
                       COUNT(*) as customer_count,
                       SUM(g.AMT) as total_amount,
                       AVG(g.AMT) as avg_amount,
                       MAX(g.AMT) as max_amount,
                       MIN(g.AMT) as min_amount,
                       ROUND(AVG(TO_NUMBER(g.SCORE)), 2) as avg_score
                FROM QMS_GBW_VIEW g
                WHERE g.AMT IS NOT NULL
                GROUP BY g.PLAN_QUARTER, g.HIQ1_APP_CD
                ORDER BY g.PLAN_QUARTER DESC, total_amount DESC
            """
        }
        
        # 쿼리 ID 확인
        if query_id not in predefined_queries:
            return jsonify({'error': f'정의되지 않은 쿼리 ID: {query_id}'}), 400
        
        # 고정된 SQL 쿼리 가져오기
        sql_query = predefined_queries[query_id]
        
        # SQL 직접 실행 (LLM 거치지 않음)
        result = chart_app.execute_predefined_sql(query_id, sql_query, username)

        return jsonify({
            'query_id': query_id,
            'sql_query': result['sql_query'],
            'result_data': result['result_df'].replace({np.nan: None}).to_dict(orient='records')
        })

    except Exception as e:
        logger.error(f"미리 정의된 쿼리 실행 오류: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/<username>/modify_sql', methods=['POST'])
def modify_sql(username):
    """SQL 수정 요청 처리"""
    try:
        original_sql = request.form.get('original_sql')
        modification_request = request.form.get('modification_request')
        current_data = request.form.get('current_data')

        if not all([original_sql, modification_request]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400

        chart_app = get_chart_app_for_user(username)
        
        # LLM을 통한 SQL 수정
        if chart_app.llm_manager:
            # 수정 프롬프트 생성
            modify_prompt = f"""
기존 SQL을 사용자 요청에 맞게 수정해주세요.

## 기존 SQL
{original_sql}

## 사용자 수정 요청
{modification_request}

## 현재 데이터 샘플
{current_data[:500] if current_data else 'N/A'}

## 지시사항
- 기존 SQL의 구조를 최대한 유지하면서 수정하세요
- 사용자 요청사항만 반영하세요
- Oracle 문법을 준수하세요
- SELECT 문만 작성하고 다른 설명은 포함하지 마세요

수정된 SQL:
"""
            
            modified_sql = chart_app.llm_manager.generate_text(modify_prompt, temperature=0.1, max_tokens=1024)
            
            # SQL 검증 및 정제
            modified_sql = chart_app.data_manager._validate_sql_query(modified_sql)
            
            # 수정된 SQL 실행
            result_df = chart_app.data_manager.execute_sql(modified_sql)
            
            return jsonify({
                'sql_query': modified_sql,
                'result_data': result_df.replace({np.nan: None}).to_dict(orient='records'),
                'modification_applied': modification_request
            })
        else:
            return jsonify({'error': 'LLM 매니저가 설정되지 않았습니다.'}), 500

    except Exception as e:
        logger.error(f"SQL 수정 오류: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/<username>/generate_chart', methods=['POST'])
def generate_chart(username):
    """차트 생성 요청 처리"""
    try:
        chart_request = request.form.get('chart_request')
        result_data = request.form.get('result_data')
        sql_query = request.form.get('sql_query')

        if not all([chart_request, result_data]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400

        chart_app = get_chart_app_for_user(username)
        
        # JSON 파싱
        result_data_dict = json.loads(result_data)
        result_df = pd.DataFrame.from_records(result_data_dict)

        # 차트 생성
        result = chart_app.chart_process_request(
            query=chart_request,
            chart_request=chart_request,
            result_df=result_df,
            sql_query=sql_query,
            username=username
        )

        return jsonify({
            'title': result['chart_json'].get('title', '차트'),
            'chart_base64': result['chart_base64'],
            'description': result['description'],
            'chart_json': result['chart_json']
        })

    except Exception as e:
        logger.error(f"차트 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/<username>/modify_chart_json', methods=['POST'])
def modify_chart_json(username):
    """차트 JSON 수정 요청 처리"""
    try:
        original_json = request.form.get('original_json')
        modification_request = request.form.get('modification_request')
        result_data = request.form.get('result_data')

        if not all([original_json, modification_request]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400

        chart_app = get_chart_app_for_user(username)
        
        if chart_app.llm_manager:
            # 수정 프롬프트 생성
            modify_prompt = f"""
기존 차트 설정을 사용자 요청에 맞게 수정해주세요.

## 기존 차트 JSON
{original_json}

## 사용자 수정 요청
{modification_request}

## 지시사항
- 기존 차트의 기본 구조는 유지하세요
- 요청된 부분만 정확히 수정하세요
- 유효한 JSON 형식으로 반환하세요
- 마크다운이나 설명 없이 순수한 JSON만 반환하세요

수정된 차트 JSON:
"""
            
            modified_json_str = chart_app.llm_manager.generate_text(modify_prompt, temperature=0.2, max_tokens=2048)
            
            # JSON 파싱 및 검증
            try:
                # 마크다운 코드 블록 제거
                import re
                json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                matches = re.findall(json_pattern, modified_json_str)
                
                if matches:
                    json_str = matches[0]
                else:
                    start_idx = modified_json_str.find('{')
                    end_idx = modified_json_str.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = modified_json_str[start_idx:end_idx]
                    else:
                        raise ValueError("JSON 형식을 찾을 수 없습니다.")
                
                modified_chart_json = json.loads(json_str)
                
                # 수정된 JSON으로 차트 재생성
                result_data_dict = json.loads(result_data) if result_data else []
                result_df = pd.DataFrame.from_records(result_data_dict)
                
                chart_path, chart_base64 = chart_app.chart_generator.create_chart(modified_chart_json, result_df)
                
                return jsonify({
                    'title': modified_chart_json.get('title', '수정된 차트'),
                    'chart_base64': chart_base64,
                    'description': modified_chart_json.get('description', ''),
                    'chart_json': modified_chart_json
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}")
                return jsonify({'error': 'LLM이 유효한 JSON을 생성하지 못했습니다.'}), 500
        else:
            return jsonify({'error': 'LLM 매니저가 설정되지 않았습니다.'}), 500

    except Exception as e:
        logger.error(f"차트 JSON 수정 오류: {e}")
        return jsonify({'error': str(e)}), 500


# 기존 라우트들 (유지)
@app.route('/charts/<path:filename>')
def serve_chart(filename):
    """차트 이미지 제공"""
    chart_app = get_chart_app_for_user(session.get('username', 'default'))
    return send_from_directory(chart_app.output_dir, filename)


@app.route('/results/<path:filename>')
def serve_result(filename):
    """결과 파일 제공"""
    chart_app = get_chart_app_for_user(session.get('username', 'default'))
    return send_from_directory(chart_app.results_dir, filename)


@app.route('/<username>/get_json_data/')
def get_json_data(username):
    """메타데이터 반환"""
    try:
        with open(Config.metadata_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return jsonify(json_data)
    except Exception as e:
        logger.error(f"메타데이터 로드 오류: {e}")
        return jsonify({"error": "JSON 데이터를 가져오지 못했습니다."}), 500


@app.route('/<username>/get_history')
def get_history(username):
    """사용자 히스토리 반환"""
    try:
        history_folder = os.path.join(Config.BASE_RESULTS_DIR, username)
        
        if not os.path.exists(history_folder):
            return jsonify([])

        folders = [f for f in os.listdir(history_folder) 
                  if os.path.isdir(os.path.join(history_folder, f))]
        history_data = [{"folder": f} for f in sorted(folders, reverse=True)]
        
        return jsonify(history_data)
    except Exception as e:
        logger.error(f"히스토리 로드 오류: {e}")
        return jsonify({"error": "히스토리 데이터를 가져오지 못했습니다."}), 500


@app.route('/<username>/delete_folder', methods=['DELETE'])
def delete_folder(username):
    """히스토리 폴더 삭제"""
    try:
        folder_name = request.args.get('folder')
        if not folder_name:
            return jsonify({"error": "폴더 이름이 필요합니다."}), 400

        folder_path = os.path.join(Config.BASE_RESULTS_DIR, username, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({"error": "폴더가 존재하지 않습니다."}), 404

        # 실제 폴더 삭제
        import shutil
        shutil.rmtree(folder_path)
        logger.info(f"폴더 삭제 완료: {folder_path}")
        
        return jsonify({"message": "폴더가 성공적으로 삭제되었습니다."}), 200
        
    except Exception as e:
        logger.error(f"폴더 삭제 오류: {e}")
        return jsonify({"error": "폴더 삭제에 실패했습니다."}), 500


@app.route('/<username>/get_files')
def get_files(username):
    """파일 내용 반환 또는 폴더 내 파일 목록 반환"""
    try:
        folder = request.args.get('folder')
        file_name = request.args.get('file')
        
        if not folder:
            return jsonify({"error": "폴더 이름이 필요합니다."}), 400

        folder_path = os.path.join(Config.BASE_RESULTS_DIR, username, folder)
        
        if not os.path.exists(folder_path):
            return jsonify({"error": "폴더가 존재하지 않습니다."}), 404

        # file 매개변수가 없으면 폴더 내 파일 목록 반환
        if not file_name:
            files = []
            for f in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, f)):
                    file_type = f.split('.')[-1] if '.' in f else 'unknown'
                    files.append({"name": f, "type": file_type})
            return jsonify(files)
        
        # file 매개변수가 있으면 특정 파일 내용 반환
        file_path = os.path.join(folder_path, file_name)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "파일이 존재하지 않습니다."}), 404

        if file_name.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        elif file_name.endswith(('.csv', '.sql')):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify({"content": f.read()})
        elif file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return send_file(file_path, mimetype='image/*')
        else:
            return jsonify({"error": "지원되지 않는 파일 형식입니다."}), 400
            
    except Exception as e:
        logger.error(f"파일 로드 오류: {e}")
        return jsonify({"error": "파일을 가져오지 못했습니다."}), 500


@app.route('/set_llm_mode', methods=['POST'])
def set_mode():
    """LLM 모드 변경"""
    try:
        mode = request.form.get('mode', '')
        if not mode:
            return jsonify({'error': '모드가 지정되지 않았습니다.'}), 400
        
        set_llm_mode(mode)
        return jsonify({'success': True, 'mode': Config.LLM_MODE.value})
    except Exception as e:
        logger.error(f"모드 변경 오류: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
    """파비콘 제공"""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


# 정적 파일 라우트
@app.route('/static/<path:filename>')
def serve_static(filename):
    """정적 파일 제공"""
    return send_from_directory('static', filename)


# 에러 핸들러
@app.errorhandler(404)
def not_found_error(error):
    """404 에러 핸들러"""
    return jsonify({'error': '요청한 리소스를 찾을 수 없습니다.'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {error}")
    return jsonify({'error': '내부 서버 오류가 발생했습니다.'}), 500


@app.errorhandler(413)
def too_large(error):
    """413 에러 핸들러 (파일 크기 초과)"""
    return jsonify({'error': '파일 크기가 너무 큽니다.'}), 413


# 요청 전후 처리
@app.before_request
def before_request():
    """요청 전 처리"""
    # CORS 헤더 설정 (필요한 경우)
    pass


@app.after_request
def after_request(response):
    """요청 후 처리"""
    # 보안 헤더 추가
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


def create_app(csv_path, metadata_path, output_dir=None, results_dir=None, llm_mode=None, username=None):
    """Flask 애플리케이션 생성 및 초기화"""
    # Config 업데이트
    Config.csv_path = csv_path
    Config.metadata_path = metadata_path
    
    if output_dir:
        Config.BASE_OUTPUT_DIR = output_dir
    if results_dir:
        Config.BASE_RESULTS_DIR = results_dir
    if llm_mode:
        set_llm_mode(llm_mode)

    # 필요한 디렉토리 생성
    directories = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'static/images',
        Config.BASE_OUTPUT_DIR,
        Config.BASE_RESULTS_DIR
    ]
    
    for directory in directories:
        dir_path = os.path.join(current_dir, directory) if not os.path.isabs(directory) else directory
        os.makedirs(dir_path, exist_ok=True)

    # 기본 favicon 생성 (없는 경우)
    favicon_path = os.path.join(current_dir, 'static', 'favicon.ico')
    if not os.path.exists(favicon_path):
        # 기본 16x16 ICO 파일 생성 (투명)
        ico_data = (
            b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00'
            b'\x16\x00\x00\x00\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00'
            b'\x20\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x00' * 1024
        )
        try:
            with open(favicon_path, 'wb') as f:
                f.write(ico_data)
        except Exception as e:
            logger.warning(f"기본 favicon 생성 실패: {e}")

    logger.info("Flask 애플리케이션 초기화 완료")
    return app


def setup_logging(debug=False):
    """로깅 설정"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 파일 핸들러 (로그 파일에 저장)
    try:
        log_dir = os.path.join(current_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'web_app.log'),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"로그 파일 설정 실패: {e}")
        # 파일 핸들러 실패 시 콘솔만 사용
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[console_handler]
        )


def validate_config():
    """설정 유효성 검사"""
    errors = []
    
    # 필수 파일 존재 확인
    if not os.path.exists(Config.csv_path):
        errors.append(f"CSV 파일이 존재하지 않습니다: {Config.csv_path}")
    
    if not os.path.exists(Config.metadata_path):
        errors.append(f"메타데이터 파일이 존재하지 않습니다: {Config.metadata_path}")
    
    # LLM 모드별 설정 확인
    if Config.LLM_MODE == LLMMode.API and not Config.API_KEY:
        errors.append("API 모드를 사용하려면 API_KEY가 설정되어야 합니다.")
    
    # 디렉토리 쓰기 권한 확인
    try:
        test_file = os.path.join(Config.BASE_OUTPUT_DIR, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        errors.append(f"출력 디렉토리에 쓰기 권한이 없습니다: {Config.BASE_OUTPUT_DIR}")
    
    return errors


def main():
    """웹 애플리케이션 실행"""
    print("시작")
    import argparse
    
    parser = argparse.ArgumentParser(description='차트 생성 시스템 웹 인터페이스 - 새로운 단계별 프로세스')
    parser.add_argument('--csv', type=str, required=True, help='CSV 데이터 파일 경로')
    parser.add_argument('--metadata', type=str, required=True, help='메타데이터 JSON 파일 경로')
    parser.add_argument('--output', type=str, default='./chart_outputs', help='차트 이미지 저장 디렉토리')
    parser.add_argument('--results', type=str, default='./results', help='결과 저장 디렉토리')
    parser.add_argument('--llm-mode', type=str, choices=['vllm', 'api', 'offline'], 
                        default='api', help='LLM 모드 (기본값: api)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='서버 호스트 (기본값: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='서버 포트 (기본값: 5000)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='로그 레벨')
    
    args = parser.parse_args()

    # 로깅 설정
    setup_logging(args.debug)
    
    # Config 업데이트
    Config.csv_path = args.csv
    Config.metadata_path = args.metadata
    Config.BASE_OUTPUT_DIR = args.output
    Config.BASE_RESULTS_DIR = args.results
    
    # LLM 모드 설정
    try:
        set_llm_mode(args.llm_mode)
    except ValueError as e:
        print(f"오류: {e}")
        return 1

    # 설정 유효성 검사
    config_errors = validate_config()
    if config_errors:
        print("설정 오류:")
        for error in config_errors:
            print(f"  - {error}")
        return 1

    # 애플리케이션 생성
    flask_app = create_app(
        csv_path=args.csv,
        metadata_path=args.metadata,
        output_dir=args.output,
        results_dir=args.results,
        llm_mode=args.llm_mode
    )

    # 웹 서버 실행
    try:
        print("=" * 60)
        print("🚀 LLM 기반 차트 생성 시스템")
        print("=" * 60)
        print(f"📊 서버 주소: http://{args.host}:{args.port}")
        print(f"🤖 LLM 모드: {Config.LLM_MODE.value}")
        print(f"📁 데이터 파일: {args.csv}")
        print(f"📋 메타데이터: {args.metadata}")
        print(f"💾 결과 저장: {args.results}")
        print("=" * 60)
        print("✨ 새로운 단계별 개선 프로세스:")
        print("   1️⃣  예시 데이터 선택")
        print("   2️⃣  데이터 확인 및 수정 (선택사항)")
        print("   3️⃣  차트 생성 요청")
        print("   4️⃣  차트 수정 및 완성 (선택사항)")
        print("   🔄 히스토리 기반 단계 간 이동")
        print("=" * 60)
        print("🌐 브라우저에서 위 주소로 접속하세요!")
        print("📝 사용자별 접속: http://{0}:{1}/[사용자명]".format(args.host, args.port))
        print("=" * 60)
        
        # Flask 앱 실행
        flask_app.run(
            host=args.host, 
            port=args.port, 
            debug=args.debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 프로그램이 사용자에 의해 중단되었습니다.")
        return 0
    except Exception as e:
        logger.error(f"웹 서버 실행 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")
        return 1
if __name__ == '__main__':
    main()