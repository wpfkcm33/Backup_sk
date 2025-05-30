/**
 * ChartManager - 차트 생성 및 관리
 */
class ChartManager {
    constructor() {
        this.currentChartData = null;
        this.currentChartJson = null;
    }

    /**
     * 차트 생성 요청 처리
     */
    async createChart(chartRequest) {
        try {
            const currentData = dataManager.getCurrentData();
            if (!currentData.data || !currentData.sql) {
                throw new Error('차트를 생성할 데이터가 없습니다.');
            }

            uiController.showLoading('차트를 생성하는 중입니다...');

            const response = await fetch(`/${username}/generate_chart`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `chart_request=${encodeURIComponent(chartRequest)}&result_data=${encodeURIComponent(JSON.stringify(currentData.data))}&sql_query=${encodeURIComponent(currentData.sql)}`
            });

            if (!response.ok) {
                throw new Error('차트 생성에 실패했습니다.');
            }

            const result = await response.json();

            // 차트 데이터 저장
            this.currentChartData = result;
            this.currentChartJson = result.chart_json;

            // 히스토리에 저장
            sessionHistory.saveStep(
                sessionHistory.stepTypes.CHART_CREATED,
                {
                    chartRequest: chartRequest,
                    chartData: result,
                    chartJson: result.chart_json
                },
                chartRequest
            );

            // UI 업데이트
            this.showChartResult(result);
            uiController.hideLoading();

        } catch (error) {
            console.error('Error creating chart:', error);
            uiController.hideLoading();
            uiController.showError(error.message);
        }
    }

    /**
     * 차트 수정 요청 처리
     */
    async modifyChart(modificationRequest) {
        try {
            if (!this.currentChartJson) {
                throw new Error('수정할 차트가 없습니다.');
            }

            uiController.showLoading('차트를 수정하는 중입니다...');

            const currentData = dataManager.getCurrentData();
            
            const response = await fetch(`/${username}/modify_chart_json`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `original_json=${encodeURIComponent(JSON.stringify(this.currentChartJson))}&modification_request=${encodeURIComponent(modificationRequest)}&result_data=${encodeURIComponent(JSON.stringify(currentData.data))}`
            });

            if (!response.ok) {
                throw new Error('차트 수정에 실패했습니다.');
            }

            const result = await response.json();

            // 차트 데이터 업데이트
            this.currentChartData = result;
            this.currentChartJson = result.chart_json;

            // 히스토리에 저장
            sessionHistory.saveStep(
                sessionHistory.stepTypes.CHART_MODIFIED,
                {
                    modificationRequest: modificationRequest,
                    chartData: result,
                    chartJson: result.chart_json
                },
                modificationRequest
            );

            // UI 업데이트
            this.updateChartDisplay(result);
            uiController.hideLoading();
            uiController.showSuccess('차트가 성공적으로 수정되었습니다.');

        } catch (error) {
            console.error('Error modifying chart:', error);
            uiController.hideLoading();
            uiController.showError(error.message);
        }
    }

    /**
     * 차트 결과 표시
     */
    showChartResult(chartData) {
        // 4단계 카드 표시
        uiController.showStep(4);

        // 차트 업데이트
        this.updateChartDisplay(chartData);

        // 스크롤 이동
        document.getElementById('step4Card').scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * 차트 디스플레이 업데이트
     */
    updateChartDisplay(chartData) {
        // 차트 제목
        const titleElement = document.getElementById('chartTitle');
        if (titleElement) {
            titleElement.textContent = chartData.title || '생성된 차트';
        }

        // 차트 이미지
        const chartImg = document.getElementById('chartImage');
        if (chartImg && chartData.chart_base64) {
            chartImg.src = `data:image/png;base64,${chartData.chart_base64}`;
            chartImg.style.display = 'block';
        }

        // 차트 설명
        const descriptionElement = document.getElementById('chartDescription');
        if (descriptionElement && chartData.description) {
            descriptionElement.innerHTML = `
                <h6>차트 설명</h6>
                <p class="text-muted">${chartData.description}</p>
            `;
        }

        // 다운로드 링크 설정
        this.setupDownloadLinks(chartData);
    }

    /**
     * 다운로드 링크 설정
     */
    setupDownloadLinks(chartData) {
        // 차트 다운로드
        const downloadChartBtn = document.getElementById('downloadChartBtn');
        if (downloadChartBtn && chartData.chart_base64) {
            const dataUrl = `data:image/png;base64,${chartData.chart_base64}`;
            downloadChartBtn.href = dataUrl;
            downloadChartBtn.download = `${chartData.title || 'chart'}.png`;
        }

        // 데이터 다운로드 버튼 이벤트
        const downloadDataBtn = document.getElementById('downloadDataBtn');
        if (downloadDataBtn) {
            downloadDataBtn.onclick = (e) => {
                e.preventDefault();
                dataManager.downloadData();
            };
        }
    }

    /**
     * 차트 요청 모달 표시
     */
    showChartRequestModal() {
        const modal = modalManager.createModal('chartRequestModal', '차트 생성 요청', `
            <div class="mb-3">
                <label for="chartRequestInput" class="form-label">어떤 차트를 만들고 싶으신가요?</label>
                <textarea id="chartRequestInput" class="form-control" rows="4" 
                          placeholder="예: 바차트로 고객별 매출을 비교해줘&#10;라인차트로 시간별 추이를 보여줘&#10;파이차트로 비율을 표시해줘"></textarea>
                <div class="form-text">
                    <strong>팁:</strong> 차트 유형(바차트, 라인차트, 파이차트 등)과 표시하고 싶은 내용을 구체적으로 작성해주세요.
                </div>
            </div>
            
            <div class="mb-3">
                <h6>예시 요청:</h6>
                <div class="d-flex flex-wrap gap-2">
                    <span class="badge bg-light text-dark chart-example" data-request="바차트로 고객별 매출을 비교해줘">바차트로 고객별 매출 비교</span>
                    <span class="badge bg-light text-dark chart-example" data-request="라인차트로 시간별 변화 추이를 보여줘">라인차트로 시간별 추이</span>
                    <span class="badge bg-light text-dark chart-example" data-request="파이차트로 각 항목의 비율을 표시해줘">파이차트로 비율 표시</span>
                </div>
            </div>
        `, [
            { text: '취소', class: 'btn-secondary', action: 'close' },
            { text: '차트 생성', class: 'btn-success', action: 'submit' }
        ]);

        // 예시 클릭 이벤트
        modal.querySelectorAll('.chart-example').forEach(example => {
            example.style.cursor = 'pointer';
            example.onclick = () => {
                document.getElementById('chartRequestInput').value = example.dataset.request;
            };
        });

        // 제출 이벤트
        modal.querySelector('[data-action="submit"]').onclick = () => {
            const chartRequest = document.getElementById('chartRequestInput').value.trim();
            if (!chartRequest) {
                uiController.showError('차트 생성 요청을 입력해주세요.');
                return;
            }

            modalManager.closeModal(modal);
            this.createChart(chartRequest);
        };

        modalManager.showModal(modal);
    }

    /**
     * 차트 수정 모달 표시
     */
    showChartModificationModal() {
        const modal = modalManager.createModal('chartModificationModal', '차트 수정 요청', `
            <div class="mb-3">
                <label for="chartModificationInput" class="form-label">차트를 어떻게 수정하고 싶으신가요?</label>
                <textarea id="chartModificationInput" class="form-control" rows="4" 
                          placeholder="예: 색상을 파란색으로 변경해줘&#10;제목을 더 크게 해줘&#10;바차트를 라인차트로 바꿔줘"></textarea>
                <div class="form-text">
                    <strong>팁:</strong> 색상, 크기, 차트 유형, 레이블 등 구체적인 수정 사항을 작성해주세요.
                </div>
            </div>
            
            <div class="mb-3">
                <h6>수정 예시:</h6>
                <div class="d-flex flex-wrap gap-2">
                    <span class="badge bg-light text-dark modify-example" data-request="색상을 파란색으로 변경해줘">색상 변경</span>
                    <span class="badge bg-light text-dark modify-example" data-request="제목을 더 크게 만들어줘">제목 크기 조정</span>
                    <span class="badge bg-light text-dark modify-example" data-request="바차트를 라인차트로 바꿔줘">차트 유형 변경</span>
                    <span class="badge bg-light text-dark modify-example" data-request="범례를 제거해줘">범례 제거</span>
                </div>
            </div>
        `, [
            { text: '취소', class: 'btn-secondary', action: 'close' },
            { text: '수정 적용', class: 'btn-warning', action: 'submit' }
        ]);

        // 예시 클릭 이벤트
        modal.querySelectorAll('.modify-example').forEach(example => {
            example.style.cursor = 'pointer';
            example.onclick = () => {
                document.getElementById('chartModificationInput').value = example.dataset.request;
            };
        });

        // 제출 이벤트
        modal.querySelector('[data-action="submit"]').onclick = () => {
            const modificationRequest = document.getElementById('chartModificationInput').value.trim();
            if (!modificationRequest) {
                uiController.showError('수정 요청을 입력해주세요.');
                return;
            }

            modalManager.closeModal(modal);
            this.modifyChart(modificationRequest);
        };

        modalManager.showModal(modal);
    }

    /**
     * 히스토리에서 단계 복원
     */
    restoreFromHistory(step) {
        if (step.type === sessionHistory.stepTypes.CHART_CREATED || 
            step.type === sessionHistory.stepTypes.CHART_MODIFIED) {
            
            this.currentChartData = step.data.chartData;
            this.currentChartJson = step.data.chartJson;

            // UI 업데이트
            this.showChartResult(step.data.chartData);
        }
    }

    /**
     * 현재 차트 데이터 가져오기
     */
    getCurrentChartData() {
        return {
            chartData: this.currentChartData,
            chartJson: this.currentChartJson
        };
    }
}

// 전역 차트 매니저 인스턴스
window.chartManager = new ChartManager();