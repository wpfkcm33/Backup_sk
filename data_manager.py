"""
data_manager.py - 데이터 관리 모듈
- 데이터 로드 및 처리
- SQL 쿼리 생성 및 실행
"""
import os
import json
import pandas as pd
import oracledb
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import re
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, csv_path, metadata_path, llm_manager=None):
        """
        데이터 관리자 초기화
        Parameters:
        - csv_path: CSV 데이터 파일 경로
        - metadata_path: 메타데이터 JSON 파일 경로
        - llm_manager: LLM 매니저 인스턴스 (선택적)
        """
        self.csv_path = csv_path
        self.metadata_path = metadata_path
        self.llm_manager = llm_manager
        self.df = None
        self.metadata = None
        self.conn = None
        # 파일 이름을 기반으로 테이블 이름 설정
        file_name = os.path.basename(csv_path)
        self.load_data()
        # Oracle 설정
        self.setup_oracle()
        logger.info("데이터 관리자 초기화 완료")

    def load_data(self):
        """CSV 데이터 및 메타데이터 로드"""
        logger.info(f"데이터 로드 중... {self.csv_path}")
        try:
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"CSV 데이터 로드 완료: {len(self.df)} 행, {len(self.df.columns)} 열")
        except Exception as e:
            logger.error(f"CSV 데이터 로드 실패: {e}")
            raise

        logger.info(f"메타데이터 로드 중... {self.metadata_path}")
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info("메타데이터 로드 완료")
        except Exception as e:
            logger.error(f"메타데이터 로드 실패: {e}")
            raise

    # def setup_oracle(self):
    #     """Oracle 데이터베이스 설정"""
    #     logger.info("Oracle 데이터베이스 설정 중...")
    #     try:
    #         oracledb.init_oracle_client(lib_dir=r"C:\\oracle\\instantclient_21_18")
    #         # Oracle 데이터베이스 연결 설정
    #         user = "hiq1"
    #         password = "hiq11!"
    #         dsn = "10.158.122.119/HIQ1DEV"
    #         # 변경: oracledb.connect -> SQLAlchemy create_engine
    #         self.engine = create_engine(f'oracle+oracledb://{user}:{password}@{dsn}')
    #         logger.info("Oracle 데이터베이스 연결 성공")
    #     except Exception as e:
    #         logger.error(f"Oracle 설정 실패: {e}")
    #         if self.engine:
    #             self.engine.dispose()
    #             self.engine = None
    #         raise

    def setup_oracle(self):
        """Oracle 데이터베이스 설정"""
        logger.info("Oracle 데이터베이스 설정 중...")
        try:
            oracledb.init_oracle_client(lib_dir="/home/humandeep/oracle/instantclient_21_8")
            # Oracle 데이터베이스 연결 설정
            user = "system"
            password = "Test123"
            dsn = "localhost:1521/XE"
            # 변경: oracledb.connect -> SQLAlchemy create_engine
            self.engine = create_engine(f'oracle+oracledb://{user}:{password}@{dsn}')
            logger.info("Oracle 데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"Oracle 설정 실패: {e}")
            if self.engine:
                self.engine.dispose()
                self.engine = None
            raise
        
    def get_data_sample(self, rows=5):
        """데이터 샘플 추출"""
        if self.df is None:
            return "데이터가 로드되지 않았습니다."
        return self.df.head(rows).to_string()

    def generate_sql(self, query):
        """
        사용자 쿼리로부터 SQL 생성
        Parameters:
        - query: 사용자 쿼리 문자열
        Returns:
        - sql_query: 생성된 SQL 쿼리
        """
        logger.info(f"SQL 생성 중... 쿼리: '{query}'")
        if self.llm_manager is None:
            logger.warning("LLM 매니저가 설정되지 않았습니다. 기본 SQL 쿼리를 사용합니다.")
            return f"SELECT * FROM QMS_RAT_YMQT_N FETCH FIRST 100 ROWS ONLY;"

        # 데이터 샘플 추출
        data_sample = self.get_data_sample()

        # LLM으로 SQL 생성
        sql_query = self.llm_manager.generate_sql(query, self.metadata, data_sample)

        # SQL 쿼리 검증 및 수정
        sql_query = self._validate_sql_query(sql_query)

        logger.info(f"SQL 생성 완료: {sql_query}")
        self._sql_query = sql_query
        return sql_query

    def get_sql_query(self):
        return self._sql_query

    def _validate_sql_query(self, sql_query):
        """SQL 쿼리 유효성 검증 및 수정"""
        try:
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

            # 리미트 확인 (없으면 추가)
            if "FETCH FIRST" not in sql_query.upper():
                sql_query = sql_query.rstrip(';') + " FETCH FIRST 1000 ROWS ONLY"

            # 마지막 세미콜론 제거 (Oracle에서 FETCH FIRST와 함께 사용 시 문제 발생 방지)
            sql_query = sql_query.rstrip(';')

            logger.info(f"검증 및 수정된 SQL 쿼리: {sql_query}")

            return sql_query
        except Exception as e:
            logger.error(f"SQL 쿼리 검증 중 오류 발생: {e}")
            return f"SELECT * FROM QMS_RAT_YMQT_N FETCH FIRST 100 ROWS ONLY"

    def execute_sql(self, sql_query):
        """
        SQL 쿼리 실행
        Parameters:
        - sql_query: 실행할 SQL 쿼리
        Returns:
        - result_df: 쿼리 실행 결과 DataFrame
        """
        logger.info(f"SQL 실행 중: {sql_query}")
        if self.engine is None:  # 변경: self.conn -> self.engine
            logger.error("Oracle 연결이 설정되지 않았습니다.")
            return pd.DataFrame()

        try:
            # 쿼리 실행
            result_df = pd.read_sql_query(sql_query, self.engine)  # 변경: self.conn -> self.engine
            logger.info(f"SQL 실행 완료: {len(result_df)} 행, {len(result_df.columns)} 열")
            return result_df
        except Exception as e:
            logger.error(f"SQL 실행 오류: {e}")
            return pd.DataFrame()

    def close(self):
        """리소스 정리"""
        if self.engine:  # 변경: self.conn -> self.engine
            self.engine.dispose()
            self.engine = None
        logger.info("Oracle 연결 종료")