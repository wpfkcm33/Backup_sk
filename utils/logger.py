"""
logger.py - 로깅 유틸리티
- 로깅 설정 중앙화
"""

import logging
import os
import sys
from pathlib import Path

def setup_logger(name, log_level=logging.INFO, log_file=None):
    """
    로거 설정
    
    Parameters:
    - name: 로거 이름
    - log_level: 로깅 레벨
    - log_file: 로그 파일 경로 (선택적)
    
    Returns:
    - logger: 설정된 로거 인스턴스
    """
    # 로거 인스턴스 가져오기
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 포맷터 설정
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_default_logger():
    """기본 로깅 설정"""
    # 현재 디렉토리 가져오기
    current_dir = Path(__file__).parent.parent
    
    # 로그 디렉토리 설정
    log_dir = os.path.join(current_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    log_file = os.path.join(log_dir, 'chart_system.log')
    
    # 루트 로거 설정
    return setup_logger('', logging.INFO, log_file)