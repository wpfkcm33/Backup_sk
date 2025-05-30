"""
chart_generator.py - 차트 생성 모듈
- JSON 기반 차트 생성
- 다양한 차트 유형 지원
"""
import matplotlib
matplotlib.use('Agg')
import os
import json
import time
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import base64
import io
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# 한글 폰트 설정 시도
def setup_korean_font():
    """한글 폰트 설정"""
    font_path = None
    
    # 폰트 파일 검색 경로
    font_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NanumGothic.ttf'),
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        'C:/Windows/Fonts/malgun.ttf'
    ]
    
    # 가용한 폰트 파일 찾기
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if font_path:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        logger.info(f"한글 폰트 설정 완료: {font_path}")
        return font_prop
    else:
        logger.warning("한글 폰트 파일을 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        return None

# 폰트 초기화
font_prop = setup_korean_font()

class ChartGenerator:
    def __init__(self, output_dir="./chart_outputs", llm_manager=None):
        """
        차트 생성기 초기화
        
        Parameters:
        - output_dir: 차트 이미지 저장 디렉토리
        - llm_manager: LLM 매니저 인스턴스 (선택적)
        """
        self.output_dir = output_dir
        self.llm_manager = llm_manager
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 차트 유형별 생성 함수 매핑
        self.chart_functions = {
            'bar': self._create_bar_chart,
            'line': self._create_line_chart,
            'pie': self._create_pie_chart,
            'scatter': self._create_scatter_chart,
            'area': self._create_area_chart,
            'histogram': self._create_histogram_chart,
            'stacked_bar': self._create_stacked_bar_chart
        }
        
        logger.info("차트 생성기 초기화 완료")
    
    def generate_chart_json(self, query, metadata, result_df):
        """
        차트 생성 JSON 생성
        
        Parameters:
        - query: 사용자 쿼리
        - metadata: 메타데이터
        - result_df: 쿼리 실행 결과 DataFrame
        
        Returns:
        - chart_json: 차트 생성 JSON
        """
        logger.info("차트 JSON 생성 중...")
        
        if self.llm_manager is None:
            logger.warning("LLM 매니저가 설정되지 않았습니다. 기본 차트 JSON을 사용합니다.")
            # 기본 차트 JSON 생성
            return self._create_default_chart_json(result_df)
        
        # 결과 데이터 문자열화
        result_data_str = result_df.to_string()
        
        # LLM으로 차트 JSON 생성
        chart_json = self.llm_manager.generate_chart_json(query, metadata, result_data_str)
        
        # JSON 검증 및 수정
        chart_json = self._validate_chart_json(chart_json, result_df)
        
        logger.info(f"차트 JSON 생성 완료: {chart_json.get('type', '알 수 없음')} 차트")
        return chart_json
    
    def _create_default_chart_json(self, df):
        """기본 차트 JSON 생성"""
        if df.empty:
            return {
                "type": "bar",
                "title": "데이터 없음",
                "description": "쿼리 결과에 데이터가 없습니다.",
                "data": {
                    "labels": [],
                    "datasets": []
                }
            }
        
        # 컬럼이 2개 이상이면 첫 번째 컬럼을 x축, 나머지를 y축으로 사용
        if len(df.columns) >= 2:
            x_column = df.columns[0]
            y_columns = df.columns[1:]
            
            # 데이터셋 구성
            datasets = []
            for col in y_columns:
                datasets.append({
                    "label": col,
                    "data": df[col].tolist()
                })
            
            return {
                "type": "bar",
                "title": f"{x_column}별 {', '.join(y_columns)} 차트",
                "description": f"{x_column}에 따른 {', '.join(y_columns)}의 변화를 보여주는 차트입니다.",
                "data": {
                    "labels": df[x_column].tolist(),
                    "datasets": datasets
                }
            }
        
        # 컬럼이 1개인 경우
        else:
            column = df.columns[0]
            return {
                "type": "bar",
                "title": f"{column} 차트",
                "description": f"{column}의 분포를 보여주는 차트입니다.",
                "data": {
                    "labels": range(len(df)),
                    "datasets": [{
                        "label": column,
                        "data": df[column].tolist()
                    }]
                }
            }
    
    def _validate_chart_json(self, chart_json, df):
        """차트 JSON 유효성 검증 및 수정"""
        # 필수 필드 확인
        if not isinstance(chart_json, dict):
            logger.error("생성된 차트 JSON이 유효하지 않습니다.")
            return self._create_default_chart_json(df)
        
        # 차트 유형 확인
        if "type" not in chart_json or chart_json["type"] not in self.chart_functions:
            chart_json["type"] = "bar"
        
        # 제목 확인
        if "title" not in chart_json or not chart_json["title"]:
            chart_json["title"] = "데이터 차트"
        
        # 설명 확인
        if "description" not in chart_json:
            chart_json["description"] = f"{chart_json['title']}입니다."
        
        # 데이터 필드 확인
        if "data" not in chart_json:
            chart_json["data"] = {
                "labels": df[df.columns[0]].tolist() if not df.empty and len(df.columns) > 0 else [],
                "datasets": []
            }
        
        # 라벨 확인
        if "labels" not in chart_json["data"]:
            chart_json["data"]["labels"] = df[df.columns[0]].tolist() if not df.empty and len(df.columns) > 0 else []
        
        # 데이터셋 확인
        if "datasets" not in chart_json["data"] or not chart_json["data"]["datasets"]:
            if not df.empty and len(df.columns) > 1:
                chart_json["data"]["datasets"] = [{
                    "label": col,
                    "data": df[col].tolist()
                } for col in df.columns[1:]]
            else:
                chart_json["data"]["datasets"] = []
        
        return chart_json
    
    def create_chart(self, chart_json, result_df):
        """
        차트 생성 및 저장
        
        Parameters:
        - chart_json: 차트 생성 JSON
        - result_df: 쿼리 실행 결과 DataFrame
        
        Returns:
        - chart_path: 생성된 차트 이미지 경로
        - chart_base64: Base64 인코딩된 차트 이미지
        """
        logger.info(f"차트 생성 시작: {chart_json.get('type', '알 수 없음')} 차트")
        
        # 차트 유형 확인
        chart_type = chart_json.get("type", "bar")
        
        # 그림 크기 설정
        figsize = chart_json.get("figsize", (12, 6))
        plt.figure(figsize=figsize)
        
        # 차트 스타일 설정
        chart_style = chart_json.get("style", "default")
        if chart_style != "default" and chart_style in plt.style.available:
            plt.style.use(chart_style)
        
        # 차트 생성 함수 호출
        if chart_type in self.chart_functions:
            self.chart_functions[chart_type](chart_json, result_df)
        else:
            logger.warning(f"지원하지 않는 차트 유형: {chart_type}, 기본 바차트로 대체합니다.")
            self._create_bar_chart(chart_json, result_df)
        
        # 제목 설정
        title = chart_json.get("title", "")
        if title:
            if font_prop:
                plt.title(title, fontproperties=font_prop, fontsize=16, pad=20)
            else:
                plt.title(title, fontsize=16, pad=20)
        
        # 레이아웃 조정
        plt.tight_layout()
        
        # 차트 저장
        timestamp = int(time.time())
        chart_filename = f"{chart_type}_{timestamp}.png"
        chart_path = os.path.join(self.output_dir, chart_filename)
        plt.savefig(chart_path, dpi=100, bbox_inches="tight")
        
        # 이미지를 Base64로 인코딩
        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format="png", dpi=100, bbox_inches="tight")
        img_bytesio.seek(0)
        img_bytes = img_bytesio.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # 차트 리소스 정리
        plt.close()
        
        logger.info(f"차트 생성 완료: {chart_path}")
        return chart_path, img_base64
    
    def _create_bar_chart(self, chart_json, df):
        """바차트 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # X축 범위 계산
        x = range(len(labels))
        
        # 바 차트 속성
        bar_width = 0.8 / len(datasets) if datasets else 0.8
        
        # 각 데이터셋에 대해 바 생성
        for i, dataset in enumerate(datasets):
            bar_data = dataset.get("data", [])
            bar_label = dataset.get("label", f"데이터 {i+1}")
            
            # 위치 계산
            bar_positions = [pos + (i - len(datasets)/2 + 0.5) * bar_width for pos in x]
            
            # 바 생성
            plt.bar(bar_positions, bar_data, width=bar_width, label=bar_label)
        
        # X축 레이블 설정
        if labels:
            plt.xticks(x, labels, rotation=45 if len(labels) > 5 else 0)
        
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    def _create_line_chart(self, chart_json, df):
        """라인차트 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # X축 범위 계산
        x = range(len(labels))
        
        # 각 데이터셋에 대해 라인 생성
        for i, dataset in enumerate(datasets):
            line_data = dataset.get("data", [])
            line_label = dataset.get("label", f"데이터 {i+1}")
            
            # 라인 속성
            marker = "o"
            linestyle = "-"
            
            # 라인 생성
            plt.plot(x, line_data, marker=marker, linestyle=linestyle, label=line_label)
        
        # X축 레이블 설정
        if labels:
            plt.xticks(x, labels, rotation=45 if len(labels) > 5 else 0)
        
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        
        # 1. Y축 범위 설정 (options.scales.y)
        options = chart_json.get("options", {})
        scales = options.get("scales", {})
        y_scales = scales.get("y", {})
        if y_scales:
            min_y = y_scales.get("min")
            max_y = y_scales.get("max")
            if min_y is not None and max_y is not None:
                plt.ylim(min_y, max_y)
        
        # 2. 추세선 추가 (options.trendLines)
        trend_lines = options.get("trendLines", [])
        for trend in trend_lines:
            trend_type = trend.get("type", "linear")
            color = trend.get("color", "#000000")
            label = trend.get("label", "추세선")
            # 여기에 추세선 계산 로직 추가 (예: 선형 회귀)
            # 단순 예시: 평균 기울기 기반 직선
            if len(x) > 1 and len(line_data) > 1:
                slope = (line_data[-1] - line_data[0]) / (x[-1] - x[0])
                trend_line = [line_data[0] + slope * xi for xi in x]
                plt.plot(x, trend_line, color=color, linestyle="--", label=label)
        
        # 3. 주석 추가 (options.annotations)
        annotations = options.get("annotations", [])
        for annotation in annotations:
            x_val = annotation.get("x")
            y_val = annotation.get("y")
            content = annotation.get("content", "")
            if x_val in labels:
                x_index = labels.index(x_val)
                plt.annotate(
                    content,
                    (x_index, y_val),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=9,
                    color="black",
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor="gray", facecolor="white")
                )
    
    def _create_pie_chart(self, chart_json, df):
        """파이차트 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # 첫 번째 데이터셋만 사용
        if datasets:
            pie_data = datasets[0].get("data", [])
            
            # None 값을 제거
            pie_data = [d for d in pie_data if d is not None]
            
            # pandas Series로 변환하여 NaN 값을 제거
            pie_data_series = pd.Series(pie_data)
            pie_data_series = pie_data_series.dropna()
            
            # NaN 값을 제거한 인덱스에 대응하는 labels 제거
            labels = [labels[i] for i in pie_data_series.index]
            
            pie_data = pie_data_series.tolist()
            
            # 음수 데이터는 파이차트에 적합하지 않음
            if any(d < 0 for d in pie_data):
                logger.warning("파이차트에 음수 데이터가 있습니다. 절대값으로 변환합니다.")
                pie_data = [abs(d) for d in pie_data]
            
            # 파이차트 생성
            if pie_data:  # pie_data가 비어 있지 않은지 확인
                plt.pie(pie_data, labels=labels, autopct="%1.1f%%", startangle=90)
                plt.axis("equal")
            else:
                plt.text(0.5, 0.5, "데이터가 없습니다.", ha="center", va="center")
        else:
            plt.text(0.5, 0.5, "데이터가 없습니다.", ha="center", va="center")
    
    def _create_scatter_chart(self, chart_json, df):
        """산점도 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # 각 데이터셋에 대해 산점도 생성
        for i, dataset in enumerate(datasets):
            scatter_data = dataset.get("data", [])
            scatter_label = dataset.get("label", f"데이터 {i+1}")
            
            # X 좌표 (인덱스 또는 라벨 인덱스)
            x = range(len(scatter_data))
            
            # 산점도 생성
            plt.scatter(x, scatter_data, label=scatter_label, alpha=0.7)
        
        # X축 레이블 설정
        if labels:
            plt.xticks(range(len(labels)), labels, rotation=45 if len(labels) > 5 else 0)
        
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
    
    def _create_area_chart(self, chart_json, df):
        """영역 차트 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # X축 범위 계산
        x = range(len(labels))
        
        # 각 데이터셋에 대해 영역 차트 생성
        for i, dataset in enumerate(datasets):
            area_data = dataset.get("data", [])
            area_label = dataset.get("label", f"데이터 {i+1}")
            
            # 영역 차트 생성
            plt.fill_between(x, area_data, alpha=0.3)
            plt.plot(x, area_data, label=area_label)
        
        # X축 레이블 설정
        if labels:
            plt.xticks(x, labels, rotation=45 if len(labels) > 5 else 0)
        
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    def _create_histogram_chart(self, chart_json, df):
        """히스토그램 생성"""
        data = chart_json.get("data", {})
        datasets = data.get("datasets", [])
        
        # 첫 번째 데이터셋만 사용
        if datasets:
            hist_data = datasets[0].get("data", [])
            hist_label = datasets[0].get("label", "데이터")
            
            # 히스토그램 생성
            plt.hist(hist_data, bins=10, alpha=0.7, label=hist_label)
        
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    def _create_stacked_bar_chart(self, chart_json, df):
        """누적 바차트 생성"""
        data = chart_json.get("data", {})
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        # X축 범위 계산
        x = range(len(labels))
        
        # 누적 데이터 준비
        bottom = np.zeros(len(labels))
        
        # 각 데이터셋에 대해 누적 바 생성
        for i, dataset in enumerate(datasets):
            bar_data = dataset.get("data", [])
            bar_label = dataset.get("label", f"데이터 {i+1}")
            
            # 누적 바 생성
            plt.bar(x, bar_data, bottom=bottom, label=bar_label)
            
            # 다음 층을 위한 바닥 업데이트
            bottom += np.array(bar_data)
        
        # X축 레이블 설정
        if labels:
            plt.xticks(x, labels, rotation=45 if len(labels) > 5 else 0)
        
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    def generate_description(self, chart_json, result_df):
        """
        차트 설명 생성
        
        Parameters:
        - chart_json: 차트 생성 JSON
        - result_df: 쿼리 실행 결과 DataFrame
        
        Returns:
        - description: 차트 설명 문자열
        """
        # 이미 설명이 있으면 그대로 사용
        if "description" in chart_json and chart_json["description"]:
            return chart_json["description"]
        
        # 기본 설명 생성
        chart_type = chart_json.get("type", "bar")
        title = chart_json.get("title", "차트")
        
        # 차트 유형별 한글 설명
        chart_type_kr = {
            "bar": "바차트",
            "line": "라인차트",
            "pie": "파이차트",
            "scatter": "산점도",
            "area": "영역차트",
            "histogram": "히스토그램",
            "stacked_bar": "누적 바차트"
        }.get(chart_type, "차트")
        
        # 데이터 정보
        data_info = ""
        if not result_df.empty:
            data_info = f"이 차트는 {len(result_df)} 행의 데이터를 기반으로 합니다."
        
        return f"{title}은(는) {chart_type_kr}로 표현되었습니다. {data_info}"