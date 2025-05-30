"""
test_mock_mode.py - Mock 데이터와 Mock LLM으로 프로세스 테스트
실제 DB나 LLM 없이 전체 프로세스 플로우 확인
"""

import os
import json
import pandas as pd
from unittest.mock import Mock, patch
import tempfile
from web_app import create_app
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLMManager:
    """Mock LLM Manager - 실제 LLM 대신 고정 응답 반환"""
    
    def __init__(self):
        self.mode = "mock"
        
    def generate_text(self, prompt, temperature=0.2, max_tokens=1024):
        """Mock 텍스트 생성"""
        if "SQL" in prompt or "sql" in prompt:
            return self._mock_sql_response(prompt)
        elif "차트" in prompt or "chart" in prompt:
            return self._mock_chart_response(prompt)
        else:
            return "Mock response for: " + prompt[:50] + "..."
    
    def _mock_sql_response(self, prompt):
        """Mock SQL 응답"""
        if "actual_rating" in prompt.lower():
            return "actual_rating_query"
        elif "expected_rating" in prompt.lower():
            return "expected_rating"
        elif "수정" in prompt:
            return "SELECT * FROM QMS_RAT_YMQT_N WHERE YM_QT >= '202401' AND HIQ1_APP_CD = 'CLIENT' ORDER BY YM_QT DESC FETCH FIRST 50 ROWS ONLY;"
        else:
            return "SELECT HIQ1_APP_CD, HIQ1_CUST_CD, YM_QT, ACTUAL, SCORE FROM QMS_RAT_YMQT_N WHERE YM_QT >= '202401' ORDER BY YM_QT DESC FETCH FIRST 100 ROWS ONLY;"
    
    def _mock_chart_response(self, prompt):
        """Mock 차트 JSON 응답"""
        return """{
    "title": "Mock 차트 - 고객별 실적 분석",
    "type": "bar",
    "description": "이것은 테스트용 Mock 차트입니다.",
    "data": {
        "labels": ["APPLE", "GOOGLE", "MICROSOFT", "AMAZON"],
        "datasets": [{
            "label": "실적 점수",
            "data": [85, 92, 78, 88],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
        }]
    }
}"""
    
    def generate_sql(self, query, metadata, data_sample):
        """Mock SQL 생성"""
        return self._mock_sql_response(query)
    
    def modify_sql(self, original_sql, modification_request, current_data_sample=None, metadata=None):
        """Mock SQL 수정"""
        return self._mock_sql_response(f"수정 요청: {modification_request}")
    
    def generate_chart_json(self, query, metadata, result_data):
        """Mock 차트 JSON 생성"""
        chart_json_str = self._mock_chart_response(query)
        return json.loads(chart_json_str)
    
    def close(self):
        """Mock 정리"""
        pass

class MockDataManager:
    """Mock Data Manager - 실제 DB 대신 Mock 데이터 반환"""
    
    def __init__(self, csv_path, metadata_path, llm_manager=None):
        self.csv_path = csv_path
        self.metadata_path = metadata_path
        self.llm_manager = llm_manager or MockLLMManager()
        self.df = self._create_mock_dataframe()
        self.metadata = self._create_mock_metadata()
        self._sql_query = ""
        
    def _create_mock_dataframe(self):
        """Mock DataFrame 생성"""
        data = {
            'HIQ1_APP_CD': ['CLIENT', 'SERVER', 'HBM', 'CLIENT', 'SERVER'] * 20,
            'HIQ1_CUST_CD': ['G150', 'G113', 'G669', 'G932', 'G020'] * 20,
            'YM_QT': ['202401', '202402', '202403', '202404', '202501'] * 20,
            'ACTUAL': [3, 2, 4, 1, 3] * 20,
            'SCORE': [85, 92, 78, 88, 90] * 20,
            'REVENUE': [1200000, 980000, 1500000, 750000, 1100000] * 20
        }
        return pd.DataFrame(data)
    
    def _create_mock_metadata(self):
        """Mock 메타데이터 생성"""
        return {
            "tables": [{
                "ratings": {
                    "actual_rating": {
                        "description": "실제 발생한 RATING 값을 계산합니다."
                    },
                    "expected_rating": {
                        "description": "예상되는 RATING 값을 계산합니다."
                    }
                }
            }]
        }
    
    def generate_sql(self, query):
        """Mock SQL 생성"""
        sql = self.llm_manager.generate_sql(query, self.metadata, self.df.head().to_string())
        self._sql_query = sql
        return sql
    
    def _validate_sql_query(self, sql_query):
        """SQL 쿼리 유효성 검증 및 수정"""
        try:
            # Check if the sql_query is equal to actual_rating_query
            if "actual_rating_query" in sql_query:
                return "WITH QUARTER AS ( SELECT DISTINCT PLAN_QUARTER FROM HCOB_CAL ), GBW AS ( SELECT /*+ inline */ A.HIQ1_APP_CD, A.PLAN_QUARTER, A.HIQ1_CUST_CD, A.ACTUAL, A.AMT FROM QMS_GBW_VIEW A, QMS_RAT_CUST B WHERE 1 = 1 AND A.HIQ1_APP_CD = B.HIQ1_APP_CD AND A.HIQ1_CUST_CD = B.HIQ1_CUST_CD AND B.USE_YN = 'Y' ), BASE AS ( SELECT A.HIQ1_APP_CD, A.PLAN_QUARTER, A.HIQ1_CUST_CD, A.ACTUAL, A.AMT, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,- 3) AND A.PLAN_QUARTER AND HIQ1_APP_CD = A.HIQ1_APP_CD ) END AS RAT_N, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,-2) AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,1) AND HIQ1_APP_CD = A.HIQ1_APP_CD ) END AS RAT_N1, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,-1) AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,2) AND HIQ1_APP_CD = A.HIQ1_APP_CD ) END AS RAT_N2, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN A.PLAN_QUARTER AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,3) AND HIQ1_APP_CD = A.HIQ1_APP_CD ) END AS RAT_N3 FROM GBW A WHERE 1 = 1 ), BASE_ALL AS ( SELECT A.HIQ1_APP_CD, A.PLAN_QUARTER, A.HIQ1_CUST_CD, A.ACTUAL, A.AMT, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,- 3) AND A.PLAN_QUARTER ) END AS RAT_N, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,-2) AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,1) ) END AS RAT_N1, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,-1) AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,2) ) END AS RAT_N2, CASE WHEN A.ACTUAL IS NULL OR A.ACTUAL = 0 THEN 0 ELSE A.ACTUAL * A.AMT / ( SELECT SUM(NVL(AMT,0)) FROM GBW WHERE PLAN_QUARTER BETWEEN A.PLAN_QUARTER AND FN_GET_QUARTER_CALCULATION(A.PLAN_QUARTER,3) ) END AS RAT_N3 FROM GBW A WHERE 1 = 1 ), RATING AS ( SELECT /*+ inline */ HIQ1_APP_CD, PLAN_QUARTER, SUM(CASE WHEN NVL(ACTUAL,0) > 0 THEN AMT ELSE NULL END) AS ACTUAL_AMT_SUM, SUM(AMT) AS AMT_SUM, SUM(RAT_N) AS RAT_N, SUM(RAT_N1) AS RAT_N1, SUM(RAT_N2) AS RAT_N2, SUM(RAT_N3) AS RAT_N3 FROM BASE WHERE 1=1 GROUP BY HIQ1_APP_CD, PLAN_QUARTER ), RATING_ALL AS ( SELECT 'ALL' AS HIQ1_APP_CD, PLAN_QUARTER, SUM(CASE WHEN NVL(ACTUAL,0) > 0 THEN AMT ELSE NULL END) AS ACTUAL_AMT_SUM, SUM(AMT) AS AMT_SUM, SUM(RAT_N) AS RAT_N, SUM(RAT_N1) AS RAT_N1, SUM(RAT_N2) AS RAT_N2, SUM(RAT_N3) AS RAT_N3 FROM BASE_ALL WHERE 1=1 GROUP BY PLAN_QUARTER ) SELECT HIQ1_APP_CD, PLAN_QUARTER, ROUND( CASE WHEN ACTUAL_AMT_SUM IS NOT NULL THEN AMT_SUM / ACTUAL_AMT_SUM * RAT_N ELSE 0 END ,2) AS RATING, ACTUAL_AMT_SUM, AMT_SUM, RAT_N, RAT_N1, RAT_N2, RAT_N3 FROM ( SELECT R.HIQ1_APP_CD, Q.PLAN_QUARTER, ( R.ACTUAL_AMT_SUM + NVL((SELECT ACTUAL_AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT ACTUAL_AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT ACTUAL_AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS ACTUAL_AMT_SUM, ( R.AMT_SUM + NVL((SELECT AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT AMT_SUM FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS AMT_SUM, ( R.RAT_N + NVL((SELECT NVL(RAT_N1,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N2,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N3,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS RAT_N, ( R.RAT_N1 + NVL((SELECT NVL(RAT_N2,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N3,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS RAT_N1, ( R.RAT_N2 + NVL((SELECT NVL(RAT_N3,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N1,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS RAT_N2, ( R.RAT_N3 + NVL((SELECT NVL(RAT_N,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N1,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) + NVL((SELECT NVL(RAT_N2,0) FROM RATING WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3) AND HIQ1_APP_CD = R.HIQ1_APP_CD),0) ) AS RAT_N3 FROM QUARTER Q, RATING R WHERE Q.PLAN_QUARTER = R.PLAN_QUARTER(+) AND Q.PLAN_QUARTER BETWEEN '202001' AND '202503' UNION ALL SELECT R.HIQ1_APP_CD, Q.PLAN_QUARTER, ( R.ACTUAL_AMT_SUM + NVL((SELECT ACTUAL_AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT ACTUAL_AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT ACTUAL_AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS ACTUAL_AMT_SUM, ( R.AMT_SUM + NVL((SELECT AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT AMT_SUM FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS AMT_SUM, ( R.RAT_N + NVL((SELECT NVL(RAT_N1,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT NVL(RAT_N2,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT NVL(RAT_N3,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS RAT_N, ( R.RAT_N1 + NVL((SELECT NVL(RAT_N2,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT NVL(RAT_N3,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT NVL(RAT_N,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS RAT_N1, ( R.RAT_N2 + NVL((SELECT NVL(RAT_N3,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT NVL(RAT_N,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT NVL(RAT_N1,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS RAT_N2, ( R.RAT_N3 + NVL((SELECT NVL(RAT_N,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -1)),0) + NVL((SELECT NVL(RAT_N1,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -2)),0) + NVL((SELECT NVL(RAT_N2,0) FROM RATING_ALL WHERE PLAN_QUARTER = FN_GET_QUARTER_CALCULATION(Q.PLAN_QUARTER, -3)),0) ) AS RAT_N3 FROM QUARTER Q, RATING_ALL R WHERE Q.PLAN_QUARTER = R.PLAN_QUARTER(+) AND Q.PLAN_QUARTER BETWEEN '202001' AND '202503' ) ORDER BY HIQ1_APP_CD, PLAN_QUARTER"
            
            if "expected_rating" in sql_query:
                return "WITH LEGEND AS ( SELECT DISTINCT A.COMM_CD AS HIQ1_APP_CD, A.COMM_CD_NM AS HIQ1_APP_NM, B.PLAN_QUARTER FROM HCOB_COMM_CD_N A, HCOB_CAL B WHERE 1=1 AND A.COMM_CD_DIV = 'CUQ_00002' AND B.PLAN_QUARTER BETWEEN '202001' AND '202502' )SELECT L.HIQ1_APP_CD, L.HIQ1_APP_NM, L.PLAN_QUARTER, M.REVENUE_PORTION, M.PORTION, CASE WHEN L.PLAN_QUARTER > 202500 THEN 1.2 ELSE DECODE(M.PORTION,0,0,NVL(ROUND(M.REVENUE_PORTION / M.PORTION, 2),0)) END AS RATING FROM LEGEND L, ( SELECT HIQ1_APP_CD, YM_QT, SUM(REVENUE_PORTION) AS REVENUE_PORTION, SUM(DECODE(REVENUE,NULL,0,PORTION)) AS PORTION FROM ( SELECT A.HIQ1_APP_CD, A.YM_QT, A.REVENUE, ( ( ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT BETWEEN FN_GET_QUARTER_CALCULATION(A.YM_QT, -3) AND A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' AND A.HIQ1_CUST_CD = YMQT.HIQ1_CUST_CD AND A.HIQ1_APP_CD = YMQT.HIQ1_APP_CD ) + ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT = A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' AND A.HIQ1_CUST_CD = YMQT.HIQ1_CUST_CD AND A.HIQ1_APP_CD = YMQT.HIQ1_APP_CD ) ) / ( ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT BETWEEN FN_GET_QUARTER_CALCULATION(A.YM_QT, -3) AND A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' ) + ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT = A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' ) ) ) AS PORTION, ( ( ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT BETWEEN FN_GET_QUARTER_CALCULATION(A.YM_QT, -3) AND A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' AND A.HIQ1_CUST_CD = YMQT.HIQ1_CUST_CD AND A.HIQ1_APP_CD = YMQT.HIQ1_APP_CD ) + ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT = A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' AND A.HIQ1_CUST_CD = YMQT.HIQ1_CUST_CD AND A.HIQ1_APP_CD = YMQT.HIQ1_APP_CD ) ) / ( ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT BETWEEN FN_GET_QUARTER_CALCULATION(A.YM_QT, -3) AND A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' ) + ( SELECT SUM( CASE WHEN YMQT.YM_QT >= TO_CHAR(SYSDATE,'YYYY') || '0' ||TO_CHAR(SYSDATE,'Q') THEN TO_NUMBER(YMQT.ESTIMATE) ELSE GBW.AMT END ) FROM QMS_RAT_YMQT_N YMQT, QMS_RAT_CUST CUST, QMS_GBW_VIEW GBW WHERE 1=1 AND YMQT.YM_QT = A.YM_QT AND YMQT.HIQ1_CUST_CD = CUST.HIQ1_CUST_CD AND YMQT.HIQ1_APP_CD = CUST.HIQ1_APP_CD AND CUST.HIQ1_CUST_CD = GBW.HIQ1_CUST_CD AND CUST.HIQ1_APP_CD = GBW.HIQ1_APP_CD AND YMQT.YM_QT = GBW.PLAN_QUARTER(+) AND CUST.USE_YN = 'Y' ) ) ) * REVENUE AS REVENUE_PORTION FROM QMS_RAT_YMQT_N A, QMS_RAT_CUST B WHERE 1=1 AND A.HIQ1_CUST_CD = B.HIQ1_CUST_CD AND A.HIQ1_APP_CD = B.HIQ1_APP_CD AND A.YM_QT BETWEEN '202001' AND '202502' ) MAIN WHERE 1=1 GROUP BY HIQ1_APP_CD, YM_QT ) M WHERE 1=1 AND L.HIQ1_APP_CD = M.HIQ1_APP_CD(+) AND L.PLAN_QUARTER = M.YM_QT(+) ORDER BY L.PLAN_QUARTER"

            # 마크다운 코드 블록 제거
            import re
            code_block_pattern = r"```(?:sql|SQL)?\s*([\s\S]*?)```"
            code_block_match = re.search(code_block_pattern, sql_query)
            if code_block_match:
                sql_query = code_block_match.group(1).strip()
                logger.info("SQL 코드 블록에서 쿼리 추출 완료")

            # 기본 검증 - SELECT 문이 포함되어 있는지 확인
            if not sql_query or "SELECT" not in sql_query.upper():
                logger.warning("유효하지 않은 SQL 쿼리입니다. 기본 쿼리로 대체합니다.")
                return f"SELECT * FROM {self.QMS_RAT_YMQT_N} FETCH FIRST 100 ROWS ONLY"

            # SQL 주석 제거 (-- 주석 및 /* */ 주석)
            sql_query = re.sub(r"--.*?$", "", sql_query, flags=re.MULTILINE)  # 한 줄 주석
            sql_query = re.sub(r"/\*[\s\S]*?\*/", "", sql_query)  # 여러 줄 주석

            # 여러 줄에 걸친 쿼리를 한 줄로 압축
            sql_query = re.sub(r"\s+", " ", sql_query).strip()

            # SQL 명령이 여러 개 있을 경우 첫 번째 명령만 사용
            if ";" in sql_query:
                first_statement = sql_query.split(";")[0].strip()
                if first_statement:  # 빈 문자열이 아닌지 확인
                    sql_query = first_statement
                    logger.info("여러 SQL 문장에서 첫 번째 문장만 사용합니다.")

            # 누락된 세미콜론 추가
            if not sql_query.strip().endswith(';'):
                sql_query += ';'

            # 리미트 확인 (없으면 추가)
            if "FETCH FIRST" not in sql_query.upper():
                sql_query = sql_query.rstrip(';') + " FETCH FIRST 1000 ROWS ONLY"

            logger.info(f"검증 및 수정된 SQL 쿼리: {sql_query}")

            return sql_query
        except Exception as e:
            logger.error(f"SQL 쿼리 검증 중 오류 발생: {e}")
            return f"SELECT * FROM QMS_RAT_YMQT_N FETCH FIRST 100 ROWS ONLY"
    
    def execute_sql(self, sql_query):
        """Mock SQL 실행 - 항상 샘플 데이터 반환"""
        logger.info(f"Mock SQL 실행: {sql_query[:100]}...")
        
        # SQL에 따라 다른 Mock 데이터 반환
        if "actual_rating_query" in sql_query:
            # 실제 레이팅 Mock 데이터
            mock_data = {
                'HIQ1_APP_CD': ['CLIENT', 'SERVER', 'HBM', 'ALL'],
                'PLAN_QUARTER': ['202404', '202404', '202404', '202404'],
                'RATING': [1.25, 1.18, 1.32, 1.22],
                'ACTUAL_AMT_SUM': [15000000, 12000000, 18000000, 45000000]
            }
            return pd.DataFrame(mock_data)
        
        elif "expected_rating" in sql_query:
            # 예상 레이팅 Mock 데이터
            mock_data = {
                'HIQ1_APP_CD': ['CLIENT', 'SERVER', 'HBM', 'ALL'],
                'PLAN_QUARTER': ['202501', '202501', '202501', '202501'],
                'RATING': [1.28, 1.20, 1.35, 1.24],
                'REVENUE_PORTION': [16000000, 13000000, 19000000, 48000000]
            }
            return pd.DataFrame(mock_data)
        
        else:
            # 기본 Mock 데이터
            return self.df.head(50).copy()
    
    def get_sql_query(self):
        """현재 SQL 쿼리 반환"""
        return self._sql_query
    
    def close(self):
        """Mock 정리"""
        pass

def create_mock_files():
    """Mock 파일들 생성"""
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp()
    
    # Mock CSV 파일 생성
    csv_path = os.path.join(temp_dir, 'mock_data.csv')
    mock_df = pd.DataFrame({
        'HIQ1_APP_CD': ['CLIENT', 'SERVER', 'HBM'] * 10,
        'HIQ1_CUST_CD': ['G150', 'G113', 'G669'] * 10,
        'YM_QT': ['202401', '202402', '202403'] * 10,
        'ACTUAL': [3, 2, 4] * 10,
        'SCORE': [85, 92, 78] * 10
    })
    mock_df.to_csv(csv_path, index=False)
    
    # Mock 메타데이터 파일 생성
    metadata_path = os.path.join(temp_dir, 'metadata.json')
    mock_metadata = {
        "tables": [{
            "ratings": {
                "actual_rating": {
                    "description": "실제 발생한 RATING 값을 계산합니다."
                },
                "expected_rating": {
                    "description": "예상되는 RATING 값을 계산합니다."
                }
            }
        }, {
            "database_name": "HIQ1_C",
            "table_name": "QMS_RAT_YMQT_N",
            "columns": [
                {
                    "column_name": "HIQ1_APP_CD",
                    "column_korean_name": "Application 코드",
                    "data_type": "VARCHAR2"
                },
                {
                    "column_name": "HIQ1_CUST_CD", 
                    "column_korean_name": "고객 코드",
                    "data_type": "VARCHAR2"
                }
            ]
        }]
    }
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(mock_metadata, f, ensure_ascii=False, indent=2)
    
    return csv_path, metadata_path, temp_dir

def test_full_process():
    """전체 프로세스 테스트"""
    
    print("🚀 Mock 모드로 전체 프로세스 테스트 시작...")
    
    # Mock 파일 생성
    csv_path, metadata_path, temp_dir = create_mock_files()
    
    try:
        # Mock 패치 적용
        with patch('main.LLMManager', MockLLMManager), \
             patch('main.DataManager', MockDataManager):
            
            # Flask 앱 생성
            app = create_app(
                csv_path=csv_path,
                metadata_path=metadata_path,
                output_dir=os.path.join(temp_dir, 'outputs'),
                results_dir=os.path.join(temp_dir, 'results'),
                llm_mode='offline'
            )
            
            app.config['TESTING'] = True
            client = app.test_client()
            
            print("✅ Flask 앱 생성 완료")
            
            # 1. 메인 페이지 테스트
            response = client.get('/testuser')
            assert response.status_code == 200
            print("✅ 메인 페이지 로드 성공")
            
            # 2. 미리 정의된 쿼리 목록 테스트
            response = client.get('/testuser/get_predefined_queries')
            assert response.status_code == 200
            queries = response.get_json()
            print(f"✅ 미리 정의된 쿼리 {len(queries)}개 로드 성공")
            
            # 3. 예시 쿼리 실행 테스트
            response = client.post('/testuser/execute_predefined_query', 
                                 data={'query_id': 'actual_rating'})
            assert response.status_code == 200
            result = response.get_json()
            assert 'sql_query' in result
            assert 'result_data' in result
            print("✅ 예시 쿼리 실행 성공")
            
            # 4. SQL 수정 테스트
            response = client.post('/testuser/modify_sql', data={
                'original_sql': result['sql_query'],
                'modification_request': '2024년 데이터만 보여줘',
                'current_data': json.dumps(result['result_data'])
            })
            assert response.status_code == 200
            modified_result = response.get_json()
            print("✅ SQL 수정 기능 성공")
            
            # 5. 차트 생성 테스트
            response = client.post('/testuser/generate_chart', data={
                'chart_request': '바차트로 Application별 점수를 보여줘',
                'result_data': json.dumps(result['result_data']),
                'sql_query': result['sql_query']
            })
            assert response.status_code == 200
            chart_result = response.get_json()
            assert 'chart_base64' in chart_result
            print("✅ 차트 생성 성공")
            
            # 6. 차트 수정 테스트
            response = client.post('/testuser/modify_chart_json', data={
                'original_json': json.dumps(chart_result['chart_json']),
                'modification_request': '색상을 파란색으로 변경해줘',
                'result_data': json.dumps(result['result_data'])
            })
            assert response.status_code == 200
            modified_chart = response.get_json()
            print("✅ 차트 수정 기능 성공")
            
            print("\n🎉 전체 프로세스 테스트 성공!")
            print("="*50)
            print("✅ 1단계: 예시 데이터 선택")
            print("✅ 2단계: 데이터 수정") 
            print("✅ 3단계: 차트 생성")
            print("✅ 4단계: 차트 수정")
            print("="*50)
            
            return True
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 임시 파일 정리
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_full_process()
    if success:
        print("\n💡 실제 환경에서 실행하려면:")
        print("   1. Oracle DB 연결 설정")
        print("   2. LLM API 키 설정") 
        print("   3. 실제 데이터 파일 준비")
        print("   4. python web_app.py --csv data.csv --metadata metadata.json")
    else:
        print("\n❌ 테스트 실패 - 코드 수정이 필요합니다.")