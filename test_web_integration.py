#!/usr/bin/env python3
"""
test_web_integration.py - HTML과 백엔드 연계 통합 테스트
실제 브라우저 없이 웹 인터페이스와 백엔드 API 통합 검증
"""

import os
import sys
import json
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch
import threading
import requests
import logging

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock 모듈들 import
from test_mock_mode import MockLLMManager, MockDataManager, create_mock_files

class WebIntegrationTester:
    """웹 통합 테스트 클래스"""
    
    def __init__(self):
        self.app = None
        self.server_thread = None
        self.temp_dir = None
        self.base_url = "http://127.0.0.1:5555"  # 테스트용 포트
        self.username = "testuser"
        
    def setup_test_environment(self):
        """테스트 환경 설정"""
        print("🔧 테스트 환경 설정 중...")
        
        # Mock 파일 생성
        csv_path, metadata_path, self.temp_dir = create_mock_files()
        
        # HTML 템플릿 파일 생성
        self.create_test_templates()
        
        # JavaScript 파일 생성 
        self.create_test_static_files()
        
        return csv_path, metadata_path
    
    def create_test_templates(self):
        """테스트용 HTML 템플릿 생성"""
        templates_dir = Path(self.temp_dir) / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # 기본 HTML 템플릿 (실제 기능은 JavaScript가 담당)
        html_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM 차트 생성 시스템 - 테스트</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px 0; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .predefined-query-card { border: 2px solid #e9ecef; padding: 15px; margin: 10px; cursor: pointer; }
        .predefined-query-card:hover { border-color: #007bff; }
        .d-none { display: none; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .table th { background-color: #f2f2f2; }
        .loading { text-align: center; padding: 20px; }
        .error { color: red; padding: 10px; background: #f8d7da; border-radius: 4px; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-image { max-width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>LLM 기반 차트 생성 시스템 - 통합 테스트</h1>
        <p>사용자: <strong>{{ username }}</strong></p>
        
        <!-- 1단계: 예시 데이터 선택 -->
        <div class="card" id="step1Card">
            <h3>1단계: 예시 데이터 선택</h3>
            <div id="predefinedQueries"></div>
        </div>
        
        <!-- 2단계: 데이터 결과 -->
        <div class="card d-none" id="step2Card">
            <h3>2단계: 데이터 추출 결과</h3>
            <button id="modifyDataBtn" class="btn">데이터 수정</button>
            <table class="table" id="dataTable">
                <thead id="dataTableHead"></thead>
                <tbody id="dataTableBody"></tbody>
            </table>
            <pre id="sqlQuery" style="background: #f8f9fa; padding: 10px; border-radius: 4px;"></pre>
            <button id="proceedToChartBtn" class="btn">차트 생성 단계로</button>
        </div>
        
        <!-- 3단계: 차트 생성 -->
        <div class="card d-none" id="step3Card">
            <h3>3단계: 차트 생성</h3>
            <textarea id="chartRequest" placeholder="바차트로 고객별 점수를 보여줘" style="width: 100%; height: 100px;"></textarea>
            <br><br>
            <button id="generateChartBtn" class="btn">차트 생성</button>
        </div>
        
        <!-- 4단계: 차트 결과 -->
        <div class="card d-none" id="step4Card">
            <h3>4단계: 차트 결과</h3>
            <button id="modifyChartBtn" class="btn">차트 수정</button>
            <div class="chart-container">
                <img id="chartImage" class="chart-image" src="" alt="차트">
            </div>
            <p id="chartDescription"></p>
            <button id="newAnalysisBtn" class="btn">새 분석</button>
        </div>
        
        <!-- 로딩 및 에러 -->
        <div class="loading d-none" id="loadingState">
            <p>처리 중입니다...</p>
        </div>
        <div class="error d-none" id="errorMessage"></div>
    </div>
    
    <script>
        const username = "{{ username }}";
        let currentData = null;
        let currentSql = null;
        
        // 유틸리티 함수들
        function showElement(id) {
            document.getElementById(id).classList.remove('d-none');
        }
        
        function hideElement(id) {
            document.getElementById(id).classList.add('d-none');
        }
        
        function showLoading() {
            showElement('loadingState');
            hideElement('errorMessage');
        }
        
        function hideLoading() {
            hideElement('loadingState');
        }
        
        function showError(message) {
            const errorElement = document.getElementById('errorMessage');
            errorElement.textContent = message;
            showElement('errorMessage');
            hideLoading();
        }
        
        // API 호출 함수들
        async function fetchPredefinedQueries() {
            try {
                const response = await fetch(`/${username}/get_predefined_queries`);
                const queries = await response.json();
                renderPredefinedQueries(queries);
            } catch (error) {
                showError('미리 정의된 쿼리 로드 실패: ' + error.message);
            }
        }
        
        function renderPredefinedQueries(queries) {
            const container = document.getElementById('predefinedQueries');
            container.innerHTML = '';
            
            queries.forEach(query => {
                const card = document.createElement('div');
                card.className = 'predefined-query-card';
                card.innerHTML = `
                    <h4>${query.name}</h4>
                    <p>${query.description}</p>
                    <small>예상 데이터: ${query.estimated_rows}행</small>
                `;
                card.onclick = () => executePredefinedQuery(query.id);
                container.appendChild(card);
            });
        }
        
        async function executePredefinedQuery(queryId) {
            try {
                showLoading();
                
                const formData = new FormData();
                formData.append('query_id', queryId);
                
                const response = await fetch(`/${username}/execute_predefined_query`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                currentData = result.result_data;
                currentSql = result.sql_query;
                
                displayDataResult(result);
                hideLoading();
                
            } catch (error) {
                showError('쿼리 실행 실패: ' + error.message);
            }
        }
        
        function displayDataResult(result) {
            showElement('step2Card');
            
            // 테이블 생성
            const tableHead = document.getElementById('dataTableHead');
            const tableBody = document.getElementById('dataTableBody');
            
            if (result.result_data && result.result_data.length > 0) {
                // 헤더 생성
                const headers = Object.keys(result.result_data[0]);
                tableHead.innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
                
                // 데이터 행 생성 (최대 10행)
                const rows = result.result_data.slice(0, 10);
                tableBody.innerHTML = rows.map(row => 
                    '<tr>' + headers.map(h => `<td>${row[h] || ''}</td>`).join('') + '</tr>'
                ).join('');
            }
            
            // SQL 쿼리 표시
            document.getElementById('sqlQuery').textContent = result.sql_query;
        }
        
        async function modifyData() {
            const modificationRequest = prompt('데이터 수정 요청을 입력하세요:', '2024년 데이터만 보여줘');
            if (!modificationRequest) return;
            
            try {
                showLoading();
                
                const formData = new FormData();
                formData.append('original_sql', currentSql);
                formData.append('modification_request', modificationRequest);
                formData.append('current_data', JSON.stringify(currentData));
                
                const response = await fetch(`/${username}/modify_sql`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                currentData = result.result_data;
                currentSql = result.sql_query;
                
                displayDataResult(result);
                hideLoading();
                
            } catch (error) {
                showError('데이터 수정 실패: ' + error.message);
            }
        }
        
        async function generateChart() {
            const chartRequest = document.getElementById('chartRequest').value;
            if (!chartRequest) {
                showError('차트 생성 요청을 입력해주세요.');
                return;
            }
            
            try {
                showLoading();
                
                const formData = new FormData();
                formData.append('chart_request', chartRequest);
                formData.append('result_data', JSON.stringify(currentData));
                formData.append('sql_query', currentSql);
                
                const response = await fetch(`/${username}/generate_chart`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayChartResult(result);
                hideLoading();
                
            } catch (error) {
                showError('차트 생성 실패: ' + error.message);
            }
        }
        
        function displayChartResult(result) {
            showElement('step4Card');
            
            const chartImage = document.getElementById('chartImage');
            chartImage.src = `data:image/png;base64,${result.chart_base64}`;
            
            const description = document.getElementById('chartDescription');
            description.textContent = result.description || '차트가 생성되었습니다.';
        }
        
        function startNewAnalysis() {
            // 모든 단계 초기화
            hideElement('step2Card');
            hideElement('step3Card');
            hideElement('step4Card');
            hideElement('errorMessage');
            
            document.getElementById('chartRequest').value = '';
            currentData = null;
            currentSql = null;
            
            // 1단계로 돌아가기
            showElement('step1Card');
        }
        
        // 이벤트 리스너 설정
        document.addEventListener('DOMContentLoaded', function() {
            fetchPredefinedQueries();
            
            document.getElementById('modifyDataBtn').onclick = modifyData;
            document.getElementById('proceedToChartBtn').onclick = () => showElement('step3Card');
            document.getElementById('generateChartBtn').onclick = generateChart;
            document.getElementById('newAnalysisBtn').onclick = startNewAnalysis;
        });
    </script>
</body>
</html>'''
        
        with open(templates_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    
    def create_test_static_files(self):
        """테스트용 정적 파일 생성"""
        static_dir = Path(self.temp_dir) / "static"
        static_dir.mkdir(exist_ok=True)
        
        # CSS와 JS 디렉토리는 일단 빈 상태로 생성
        (static_dir / "css").mkdir(exist_ok=True)
        (static_dir / "js").mkdir(exist_ok=True)
    
    def start_test_server(self, csv_path, metadata_path):
        """테스트 서버 시작"""
        print("🚀 테스트 서버 시작 중...")
        
        with patch('main.LLMManager', MockLLMManager), \
             patch('main.DataManager', MockDataManager):
            
            from web_app import create_app
            
            # Flask 앱 생성
            self.app = create_app(
                csv_path=csv_path,
                metadata_path=metadata_path,
                output_dir=os.path.join(self.temp_dir, 'outputs'),
                results_dir=os.path.join(self.temp_dir, 'results'),
                llm_mode='offline'
            )
            
            # 템플릿 폴더 설정
            self.app.template_folder = os.path.join(self.temp_dir, 'templates')
            self.app.static_folder = os.path.join(self.temp_dir, 'static')
            
            # 테스트 모드 설정
            self.app.config['TESTING'] = True
            
            def run_server():
                self.app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
            
            # 별도 스레드에서 서버 실행
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # 서버 시작 대기
            time.sleep(2)
            
            print(f"✅ 테스트 서버 시작 완료: {self.base_url}")
    
    def test_main_page(self):
        """메인 페이지 테스트"""
        print("\n📄 메인 페이지 테스트...")
        
        try:
            response = requests.get(f"{self.base_url}/{self.username}", timeout=5)
            
            if response.status_code == 200:
                html_content = response.text
                
                # HTML 내용 검증
                required_elements = [
                    'LLM 기반 차트 생성 시스템',
                    'step1Card',
                    'step2Card', 
                    'step3Card',
                    'step4Card',
                    'predefinedQueries'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if missing_elements:
                    print(f"   ❌ 누락된 HTML 요소: {missing_elements}")
                    return False
                else:
                    print("   ✅ HTML 템플릿 렌더링 성공")
                    print(f"   📏 HTML 크기: {len(html_content)} 문자")
                    return True
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 메인 페이지 테스트 실패: {e}")
            return False
    
    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        print("\n🔌 API 엔드포인트 테스트...")
        
        tests = [
            self.test_predefined_queries_api,
            self.test_execute_query_api,
            self.test_modify_sql_api,
            self.test_generate_chart_api
        ]
        
        results = []
        for test in tests:
            results.append(test())
        
        return all(results)
    
    def test_predefined_queries_api(self):
        """미리 정의된 쿼리 API 테스트"""
        try:
            response = requests.get(f"{self.base_url}/{self.username}/get_predefined_queries", timeout=5)
            
            if response.status_code == 200:
                queries = response.json()
                if len(queries) > 0:
                    print("   ✅ 미리 정의된 쿼리 API 성공")
                    return True
                else:
                    print("   ❌ 쿼리 목록이 비어있음")
                    return False
            else:
                print(f"   ❌ 쿼리 API 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 쿼리 API 테스트 실패: {e}")
            return False
    
    def test_execute_query_api(self):
        """쿼리 실행 API 테스트"""
        try:
            data = {'query_id': 'actual_rating'}
            response = requests.post(f"{self.base_url}/{self.username}/execute_predefined_query", 
                                   data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'sql_query' in result and 'result_data' in result:
                    print("   ✅ 쿼리 실행 API 성공")
                    self.test_data = result  # 다음 테스트를 위해 저장
                    return True
                else:
                    print("   ❌ 응답 형식 오류")
                    return False
            else:
                print(f"   ❌ 쿼리 실행 API 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 쿼리 실행 API 테스트 실패: {e}")
            return False
    
    def test_modify_sql_api(self):
        """SQL 수정 API 테스트"""
        if not hasattr(self, 'test_data'):
            print("   ⚠️ SQL 수정 테스트 스킵 (이전 테스트 데이터 없음)")
            return True
        
        try:
            data = {
                'original_sql': self.test_data['sql_query'],
                'modification_request': '상위 10개만 보여줘',
                'current_data': json.dumps(self.test_data['result_data'])
            }
            
            response = requests.post(f"{self.base_url}/{self.username}/modify_sql", 
                                   data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'sql_query' in result:
                    print("   ✅ SQL 수정 API 성공")
                    return True
                else:
                    print("   ❌ SQL 수정 응답 형식 오류")
                    return False
            else:
                print(f"   ❌ SQL 수정 API 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ SQL 수정 API 테스트 실패: {e}")
            return False
    
    def test_generate_chart_api(self):
        """차트 생성 API 테스트"""
        if not hasattr(self, 'test_data'):
            print("   ⚠️ 차트 생성 테스트 스킵 (이전 테스트 데이터 없음)")
            return True
        
        try:
            data = {
                'chart_request': '바차트로 Application별 점수를 보여줘',
                'result_data': json.dumps(self.test_data['result_data']),
                'sql_query': self.test_data['sql_query']
            }
            
            response = requests.post(f"{self.base_url}/{self.username}/generate_chart", 
                                   data=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'chart_base64' in result:
                    print("   ✅ 차트 생성 API 성공")
                    print(f"   📊 차트 크기: {len(result['chart_base64'])} 문자")
                    return True
                else:
                    print("   ❌ 차트 생성 응답 형식 오류")
                    return False
            else:
                print(f"   ❌ 차트 생성 API 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 차트 생성 API 테스트 실패: {e}")
            return False
    
    def test_browser_simulation(self):
        """브라우저 시뮬레이션 테스트"""
        print("\n🌐 브라우저 시뮬레이션 테스트...")
        
        try:
            # 세션 생성
            session = requests.Session()
            
            # 1. 메인 페이지 접속
            response = session.get(f"{self.base_url}/{self.username}")
            if response.status_code != 200:
                print("   ❌ 메인 페이지 접속 실패")
                return False
            
            # 2. 미리 정의된 쿼리 목록 가져오기
            response = session.get(f"{self.base_url}/{self.username}/get_predefined_queries")
            queries = response.json()
            
            # 3. 첫 번째 쿼리 실행
            query_id = queries[0]['id']
            data = {'query_id': query_id}
            response = session.post(f"{self.base_url}/{self.username}/execute_predefined_query", data=data)
            result = response.json()
            
            # 4. 차트 생성
            chart_data = {
                'chart_request': '바차트로 데이터를 보여줘',
                'result_data': json.dumps(result['result_data']),
                'sql_query': result['sql_query']
            }
            response = session.post(f"{self.base_url}/{self.username}/generate_chart", data=chart_data)
            chart_result = response.json()
            
            if 'chart_base64' in chart_result:
                print("   ✅ 전체 사용자 플로우 시뮬레이션 성공")
                print("   📋 완료된 단계:")
                print("      1️⃣ 메인 페이지 접속")
                print("      2️⃣ 쿼리 목록 로드")
                print("      3️⃣ 데이터 추출")
                print("      4️⃣ 차트 생성")
                return True
            else:
                print("   ❌ 차트 생성 단계에서 실패")
                return False
                
        except Exception as e:
            print(f"   ❌ 브라우저 시뮬레이션 실패: {e}")
            return False
    
    def test_static_files(self):
        """정적 파일 서빙 테스트"""
        print("\n📁 정적 파일 테스트...")
        
        # 실제로는 존재하지 않는 파일이지만, 404 응답이 정상적으로 오는지 확인
        try:
            response = requests.get(f"{self.base_url}/static/css/main.css", timeout=5)
            # 404는 정상 (파일이 없어서)
            if response.status_code in [200, 404]:
                print("   ✅ 정적 파일 라우팅 정상")
                return True
            else:
                print(f"   ❌ 정적 파일 라우팅 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 정적 파일 테스트 실패: {e}")
            return False
    
    def cleanup(self):
        """테스트 환경 정리"""
        print("\n🧹 테스트 환경 정리 중...")
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print("   ✅ 임시 파일 정리 완료")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🌐 웹 인터페이스 통합 테스트 시작")
        print("=" * 60)
        
        try:
            # 환경 설정
            csv_path, metadata_path = self.setup_test_environment()
            
            # 서버 시작
            self.start_test_server(csv_path, metadata_path)
            
            # 테스트 실행
            tests = [
                ("메인 페이지", self.test_main_page),
                ("API 엔드포인트", self.test_api_endpoints),
                ("정적 파일", self.test_static_files),
                ("브라우저 시뮬레이션", self.test_browser_simulation)
            ]
            
            results = {}
            for test_name, test_func in tests:
                results[test_name] = test_func()
            
            # 결과 출력
            print("\n" + "=" * 60)
            print("📋 웹 통합 테스트 결과:")
            print("=" * 60)
            
            all_passed = True
            for test_name, passed in results.items():
                status = "✅ 통과" if passed else "❌ 실패"
                print(f"   {test_name:<20}: {status}")
                if not passed:
                    all_passed = False
            
            print("=" * 60)
            
            if all_passed:
                print("🎉 모든 웹 통합 테스트 통과!")
                print("\n💡 실제 브라우저에서 테스트하려면:")
                print(f"   1. python web_app.py --csv data.csv --metadata metadata.json")
                print(f"   2. 브라우저에서 http://localhost:5000/{self.username} 접속")
                print("   3. 각 단계별로 테스트 진행")
            else:
                print("⚠️ 일부 테스트가 실패했습니다.")
                print("   로그를 확인하고 문제를 해결해주세요.")
            
            return all_passed
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
            return False
        
        finally:
            self.cleanup()

def main():
    """메인 실행 함수"""
    tester = WebIntegrationTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    exit(main())