"""
main.py - 차트 생성 시스템 메인 모듈
- 프로세스 전체 흐름 관리
- 각 단계별 결과 저장
"""

import os
import sys
import json
import argparse
import pandas as pd
import time
import logging
from pathlib import Path
from typing import Dict, Any

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
from llm_manager import LLMManager
from data_manager import DataManager
from chart_generator import ChartGenerator


class ChartGenerationApp:
    def __init__(self, csv_path, metadata_path, output_dir=None, results_dir=None, llm_mode=None, username=None):
        """
        차트 생성 애플리케이션 초기화

        Parameters:
        - csv_path: CSV 데이터 파일 경로
        - metadata_path: 메타데이터 JSON 파일 경로
        - output_dir: 차트 이미지 저장 디렉토리 (기본값: Config.OUTPUT_DIR)
        - results_dir: 결과 저장 디렉토리 (기본값: Config.RESULTS_DIR)
        - llm_mode: LLM 모드 (기본값: Config.LLM_MODE)
        """
        self.csv_path = csv_path
        self.metadata_path = metadata_path
        self.username = username
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.results_dir = results_dir or Config.RESULTS_DIR

        # 폴더 생성
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

        # LLM 모드 설정
        if llm_mode:
            set_llm_mode(llm_mode)

        # LLM 매니저 초기화
        self.llm_manager = LLMManager()

        # 데이터 매니저 초기화
        self.data_manager = DataManager(
            csv_path=self.csv_path,
            metadata_path=self.metadata_path,
            llm_manager=self.llm_manager
        )

        # 차트 생성기 초기화
        self.chart_generator = ChartGenerator(
            output_dir=self.output_dir,
            llm_manager=self.llm_manager
        )

        logger.info("차트 생성 애플리케이션 초기화 완료")

    def execute_predefined_sql(self, query_id, sql_query, username):
        """
        미리 정의된 SQL 직접 실행 (LLM 거치지 않음)
        Parameters:
        - query_id: 쿼리 식별자
        - sql_query: 실행할 SQL 쿼리
        - username: 사용자명
        Returns:
        - result: SQL 처리 결과 딕셔너리
        """
        logger.info(f"미리 정의된 SQL 실행 시작: '{query_id}'")
        try:
            # SQL 직접 실행
            result_df = self.data_manager.execute_sql(sql_query)

            # 결과 반환
            result = {
                'query_id': query_id,
                'sql_query': sql_query,
                'result_df': result_df
            }
            logger.info(f"미리 정의된 SQL 실행 완료: '{query_id}'")

            # SQL 처리 결과 저장
            self.save_predefined_sql_results(query_id, sql_query, result_df, username)
            return result
        except Exception as e:
            logger.error(f"미리 정의된 SQL 실행 중 오류 발생: {e}")
            raise

    def save_predefined_sql_results(self, query_id, sql_query, result_df, username):
        """미리 정의된 SQL 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 결과 데이터 저장
            if not result_df.empty:
                result_filename = f"predefined_{query_id}_{timestamp}.csv"
                result_path = os.path.join(self.config.results_dir, result_filename)
                result_df.to_csv(result_path, index=False, encoding='utf-8-sig')
                logger.info(f"미리 정의된 쿼리 결과 저장: {result_path}")
            
            # 쿼리 로그 저장
            log_data = {
                'timestamp': timestamp,
                'username': username,
                'query_id': query_id,
                'sql_query': sql_query,
                'result_count': len(result_df),
                'result_filename': result_filename if not result_df.empty else None
            }
            
            log_filename = f"predefined_query_log_{timestamp}.json"
            log_path = os.path.join(self.config.logs_dir, log_filename)
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"미리 정의된 쿼리 로그 저장: {log_path}")
            
        except Exception as e:
            logger.error(f"미리 정의된 SQL 결과 저장 중 오류: {e}")
            # 저장 실패해도 메인 프로세스는 계속 진행
            
    def save_sql_results(self, query, sql_query, result_df, username):
        """
        SQL 처리 결과 저장
        Parameters:
        - query: 사용자 질문
        - sql_query: 생성된 SQL 쿼리
        - result_df: SQL 실행 결과 DataFrame
        """
        try:
            timestamp = int(time.time())
            username = username or "default_user"
            results_dir = os.path.join(Config.get_results_dir(username), f"sql_results_{timestamp}")
            os.makedirs(results_dir, exist_ok=True)

            # 백업 폴더 생성
            backup_dir = os.path.join(Config.get_results_dir(username), f"{username}_backup", f"sql_results_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            # 1. SQL 쿼리 저장 (기존 + 백업)
            sql_path = os.path.join(results_dir, "sql_query.sql")
            sql_backup_path = os.path.join(backup_dir, "sql_query.sql")
            with open(sql_path, 'w', encoding='utf-8') as f:
                f.write(sql_query)
            with open(sql_backup_path, 'w', encoding='utf-8') as f:
                f.write(sql_query)

            # 2. 결과 데이터 저장 (CSV) (기존 + 백업)
            result_data_path = os.path.join(results_dir, "result_data.csv")
            result_data_backup_path = os.path.join(backup_dir, "result_data.csv")
            result_df.to_csv(result_data_path, index=False)
            result_df.to_csv(result_data_backup_path, index=False)

            # 3. 정보 파일 생성 (기존 + 백업)
            info = {
                "username": username,
                "query": query,
                "timestamp": timestamp,
                "sql_path": sql_path,
                "result_data_path": result_data_path
            }
            info_path = os.path.join(results_dir, "info.json")
            info_backup_path = os.path.join(backup_dir, "info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            with open(info_backup_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"SQL 결과 저장 오류: {e}")

    def chart_process_request(self, query, chart_request, result_df, sql_query, username):
        """
        차트 생성 처리
        Parameters:
        - chart_request: 사용자의 차트 생성 요청 (자연어)
        - result_df: SQL 실행 결과 데이터
        - sql_query: 생성된 SQL 쿼리
        Returns:
        - result: 차트 처리 결과 딕셔너리
        """
        logger.info(f"차트 처리 시작: '{chart_request}'")
        try:
            # 3. 차트 JSON 생성 (2번 LLM)
            print(f"시작지점 유저이름: {username}")
            chart_json = self.chart_generator.generate_chart_json(
                chart_request, self.data_manager.metadata, result_df
            )
            
            # 4. 차트 생성
            chart_path, chart_base64 = self.chart_generator.create_chart(chart_json, result_df)
            
            # 5. 차트 설명 생성
            description = chart_json.get("description") or self.chart_generator.generate_description(
                chart_json, result_df
            )
            
            sql_request = query
            
            # 6. 결과 저장
            results_path = self.save_results(sql_request, chart_request, sql_query, result_df, chart_json, chart_path, username)
            
            # 7. 결과 반환
            result = {
                'query': query,
                'chart_request': chart_request,
                'chart_json': chart_json,
                'chart_path': chart_path,
                'chart_base64': chart_base64,
                'description': description,
                'results_path': results_path
            }
            logger.info("차트 처리 완료")
            return result
        except Exception as e:
            logger.error(f"차트 처리 중 오류 발생: {e}")
            raise

    def save_results(self, sql_request, query, sql_query, result_df, chart_json, chart_path, username):
        """
        모든 중간 결과 및 최종 결과 저장
        Parameters:
        - query: 사용자 질문
        - sql_query: 생성된 SQL 쿼리
        - result_df: SQL 실행 결과 DataFrame
        - chart_json: 차트 생성 JSON
        - chart_path: 생성된 차트 이미지 경로
        - username: 사용자 이름 (선택적)
        Returns:
        - results_path: 저장된 결과 정보 파일 경로
        """
        try:
            timestamp = int(time.time())
            # 사용자 이름 기반의 results_dir 생성
            print(f"메인 유저변수: {username}")
            username = username or "default_user"  # 인자 우선, 없으면 인스턴스의 username 사용
            results_dir = os.path.join(Config.get_results_dir(username), f"results_{timestamp}")
            os.makedirs(results_dir, exist_ok=True)

            # 백업 폴더 생성
            backup_dir = os.path.join(Config.get_results_dir(username), f"{username}_backup", f"results_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            # 1. SQL 쿼리 저장 (기존 + 백업)
            sql_path = os.path.join(results_dir, "sql_query.sql")
            sql_backup_path = os.path.join(backup_dir, "sql_query.sql")
            with open(sql_path, 'w', encoding='utf-8') as f:
                f.write(sql_query)
            with open(sql_backup_path, 'w', encoding='utf-8') as f:
                f.write(sql_query)

            # 2. 결과 데이터 저장 (CSV) (기존 + 백업)
            result_data_path = os.path.join(results_dir, "result_data.csv")
            result_data_backup_path = os.path.join(backup_dir, "result_data.csv")
            result_df.to_csv(result_data_path, index=False)
            result_df.to_csv(result_data_backup_path, index=False)

            # 3. 차트 JSON 저장 (기존 + 백업)
            chart_json_path = os.path.join(results_dir, "chart_json.json")
            chart_json_backup_path = os.path.join(backup_dir, "chart_json.json")
            with open(chart_json_path, 'w', encoding='utf-8') as f:
                json.dump(chart_json, f, ensure_ascii=False, indent=2)
            with open(chart_json_backup_path, 'w', encoding='utf-8') as f:
                json.dump(chart_json, f, ensure_ascii=False, indent=2)

            # 4. 차트 이미지 복사 (기존 + 백업)
            import shutil
            chart_filename = os.path.basename(chart_path)
            chart_copy_path = os.path.join(results_dir, chart_filename)
            chart_backup_copy_path = os.path.join(backup_dir, chart_filename)
            shutil.copy2(chart_path, chart_copy_path)
            shutil.copy2(chart_path, chart_backup_copy_path)

            # 5. 정보 파일 생성 (기존 + 백업)
            info = {
                "username": username,
                "sql_request": sql_request,
                "chart_request": query,
                "timestamp": timestamp,
                "sql_path": sql_path,
                "result_data_path": result_data_path,
                "chart_json_path": chart_json_path,
                "chart_path": chart_copy_path,
                "original_chart_path": chart_path
            }
            info_path = os.path.join(results_dir, "info.json")
            info_backup_path = os.path.join(backup_dir, "info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            with open(info_backup_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)

            return info_path
        except Exception as e:
            logger.error(f"결과 저장 오류: {e}")
            return None

    def command_line_interface(self):
        return None

    def cleanup(self):
        """리소스 정리"""
        # LLM 매니저 정리
        if self.llm_manager:
            self.llm_manager.close()

        # 데이터 매니저 정리
        if self.data_manager:
            self.data_manager.close()

        logger.info("모든 리소스가 정리되었습니다.")


def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='차트 생성 시스템')
    parser.add_argument('--csv', type=str, required=True, help='CSV 데이터 파일 경로')
    parser.add_argument('--metadata', type=str, required=True, help='메타데이터 JSON 파일 경로')
    parser.add_argument('--output', type=str, default=Config.OUTPUT_DIR, help='차트 이미지 저장 디렉토리')
    parser.add_argument('--results', type=str, default=Config.RESULTS_DIR, help='결과 저장 디렉토리')
    parser.add_argument('--llm-mode', type=str, choices=['vllm', 'api', 'offline'], default=Config.LLM_MODE.value,
                        help='LLM 모드 (vllm, api, offline)')
    parser.add_argument('--query', type=str, help='직접 처리할 쿼리 (지정시 CLI 모드 실행하지 않음)')

    return parser.parse_args()


def main():
    """메인 함수"""
    # 명령줄 인수 파싱
    args = parse_arguments()
    
    # 파일 경로 확인
    if not os.path.exists(args.csv):
        print(f"오류: CSV 파일을 찾을 수 없습니다. 경로: {args.csv}")
        return
    if not os.path.exists(args.metadata):
        print(f"오류: 메타데이터 파일을 찾을 수 없습니다. 경로: {args.metadata}")
        return

    # 애플리케이션 초기화
    app = ChartGenerationApp(
        csv_path=args.csv,
        metadata_path=args.metadata,
        output_dir=args.output,
        results_dir=args.results,
        llm_mode=args.llm_mode,
        username="default_user"
    )
    
    try:
        # 대화형 CLI 모드 실행
        app.command_line_interface()
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
    finally:
        # 항상 리소스 정리
        app.cleanup()


if __name__ == "__main__":
    main()