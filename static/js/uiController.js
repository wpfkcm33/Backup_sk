/**
 * UIController - UI 상태 및 전환 관리
 */
class UIController {
    constructor() {
        this.currentStep = 1;
        this.loadingElement = null;
        this.errorElement = null;
        
        this.initializeElements();
        this.setupEventListeners();
    }

    /**
     * DOM 요소 초기화
     */
    initializeElements() {
        this.loadingElement = document.getElementById('loadingState');
        this.errorElement = document.getElementById('errorMessage');
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 데이터 수정 버튼
        const modifyDataBtn = document.getElementById('modifyDataBtn');
        if (modifyDataBtn) {
            modifyDataBtn.onclick = () => this.showDataModificationModal();
        }

        // 차트 생성 진행 버튼
        const proceedToChartBtn = document.getElementById('proceedToChartBtn');
        if (proceedToChartBtn) {
            proceedToChartBtn.onclick = () => this.showStep(3);
        }

        // 차트 생성 버튼
        const generateChartBtn = document.getElementById('generateChartBtn');
        if (generateChartBtn) {
            generateChartBtn.onclick = () => this.handleChartGeneration();
        }

        // 차트 수정 버튼
        const modifyChartBtn = document.getElementById('modifyChartBtn');
        if (modifyChartBtn) {
            modifyChartBtn.onclick = () => chartManager.showChartModificationModal();
        }

        // 새 분석 시작 버튼
        const newAnalysisBtn = document.getElementById('newAnalysisBtn');
        if (newAnalysisBtn) {
            newAnalysisBtn.onclick = () => this.startNewAnalysis();
        }

        // JSON 보기 버튼
        const viewJsonBtn = document.getElementById('viewJsonBtn');
        if (viewJsonBtn) {
            viewJsonBtn.onclick = () => modalManager.showMetadataModal();
        }

        // 히스토리 보기 버튼
        const viewHistoryBtn = document.getElementById('viewHistoryBtn');
        if (viewHistoryBtn) {
            viewHistoryBtn.onclick = () => modalManager.showHistoryModal();
        }

        // 히스토리 단계 변경 이벤트
        window.addEventListener('historyStepChanged', (event) => {
            this.handleHistoryStepChange(event.detail);
        });
    }

    /**
     * 특정 단계 표시
     */
    showStep(stepNumber) {
        // 모든 단계 카드 숨기기
        for (let i = 1; i <= 4; i++) {
            const card = document.getElementById(`step${i}Card`);
            if (card) {
                if (i <= stepNumber) {
                    card.classList.remove('d-none');
                    card.classList.add('fade-in');
                } else {
                    card.classList.add('d-none');
                }
            }
        }

        this.currentStep = stepNumber;

        // 단계별 특별 처리
        if (stepNumber === 3) {
            this.focusChartRequest();
        }
    }

    /**
     * 차트 요청 입력란 포커스
     */
    focusChartRequest() {
        setTimeout(() => {
            const chartRequestInput = document.getElementById('chartRequest');
            if (chartRequestInput) {
                chartRequestInput.focus();
                document.getElementById('step3Card').scrollIntoView({ behavior: 'smooth' });
            }
        }, 300);
    }

    /**
     * 차트 생성 처리
     */
    handleChartGeneration() {
        const chartRequest = document.getElementById('chartRequest').value.trim();
        if (!chartRequest) {
            this.showError('차트 생성 요청을 입력해주세요.');
            return;
        }

        chartManager.createChart(chartRequest);
    }

    /**
     * 데이터 수정 모달 표시
     */
    showDataModificationModal() {
        const modal = modalManager.createModal('dataModificationModal', '데이터 수정 요청', `
            <div class="mb-3">
                <label for="dataModificationInput" class="form-label">데이터를 어떻게 수정하고 싶으신가요?</label>
                <textarea id="dataModificationInput" class="form-control" rows="4" 
                          placeholder="예: 2024년 데이터만 보여줘&#10;APPLE 고객 제외하고 보여줘&#10;매출 상위 10개만 보여줘"></textarea>
                <div class="form-text">
                    <strong>팁:</strong> 필터링, 정렬, 제한 등의 조건을 구체적으로 작성해주세요.
                </div>
            </div>
            
            <div class="mb-3">
                <h6>수정 예시:</h6>
                <div class="d-flex flex-wrap gap-2">
                    <span class="badge bg-light text-dark modify-example" data-request="2024년 데이터만 보여줘">연도 필터</span>
                    <span class="badge bg-light text-dark modify-example" data-request="상위 10개만 보여줘">개수 제한</span>
                    <span class="badge bg-light text-dark modify-example" data-request="매출 순으로 정렬해줘">정렬</span>
                    <span class="badge bg-light text-dark modify-example" data-request="특정 고객 제외하고 보여줘">특정 데이터 제외</span>
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
                document.getElementById('dataModificationInput').value = example.dataset.request;
            };
        });

        // 제출 이벤트
        modal.querySelector('[data-action="submit"]').onclick = () => {
            const modificationRequest = document.getElementById('dataModificationInput').value.trim();
            if (!modificationRequest) {
                this.showError('수정 요청을 입력해주세요.');
                return;
            }

            modalManager.closeModal(modal);
            dataManager.modifyData(modificationRequest);
        };

        modalManager.showModal(modal);
    }

    /**
     * 새 분석 시작
     */
    startNewAnalysis() {
        if (confirm('새로운 분석을 시작하시겠습니까? 현재 작업 내용이 히스토리에 저장됩니다.')) {
            // 히스토리 클리어
            sessionHistory.clear();
            
            // 모든 단계 숨기기
            for (let i = 2; i <= 4; i++) {
                const card = document.getElementById(`step${i}Card`);
                if (card) {
                    card.classList.add('d-none');
                }
            }

            // 1단계만 표시
            this.showStep(1);
            
            // 선택된 카드 초기화
            document.querySelectorAll('.predefined-query-card').forEach(card => {
                card.classList.remove('selected');
            });

            // 입력 필드 초기화
            const chartRequest = document.getElementById('chartRequest');
            if (chartRequest) {
                chartRequest.value = '';
            }

            // 맨 위로 스크롤
            window.scrollTo({ top: 0, behavior: 'smooth' });

            this.showSuccess('새로운 분석을 시작합니다.');
        }
    }

    /**
     * 히스토리 단계 변경 처리
     */
    handleHistoryStepChange(detail) {
        const { step, index } = detail;
        
        // 해당 단계에 맞는 UI 복원
        switch (step.type) {
            case sessionHistory.stepTypes.PREDEFINED:
                this.showStep(2);
                dataManager.restoreFromHistory(step);
                break;
                
            case sessionHistory.stepTypes.DATA_MODIFIED:
                this.showStep(2);
                dataManager.restoreFromHistory(step);
                break;
                
            case sessionHistory.stepTypes.CHART_CREATED:
                this.showStep(4);
                dataManager.restoreFromHistory(sessionHistory.getLastStepOfType(sessionHistory.stepTypes.DATA_MODIFIED) || 
                                               sessionHistory.getLastStepOfType(sessionHistory.stepTypes.PREDEFINED));
                chartManager.restoreFromHistory(step);
                break;
                
            case sessionHistory.stepTypes.CHART_MODIFIED:
                this.showStep(4);
                dataManager.restoreFromHistory(sessionHistory.getLastStepOfType(sessionHistory.stepTypes.DATA_MODIFIED) || 
                                               sessionHistory.getLastStepOfType(sessionHistory.stepTypes.PREDEFINED));
                chartManager.restoreFromHistory(step);
                break;
        }
    }

    /**
     * 로딩 상태 표시
     */
    showLoading(message = '처리 중입니다...') {
        if (this.loadingElement) {
            this.loadingElement.classList.remove('d-none');
            const messageElement = document.getElementById('loadingMessage');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
        this.hideError();
    }

    /**
     * 로딩 상태 숨기기
     */
    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.classList.add('d-none');
        }
    }

    /**
     * 에러 메시지 표시
     */
    showError(message) {
        if (this.errorElement) {
            this.errorElement.textContent = message;
            this.errorElement.classList.remove('d-none');
            this.errorElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        this.hideLoading();
    }

    /**
     * 에러 메시지 숨기기
     */
    hideError() {
        if (this.errorElement) {
            this.errorElement.classList.add('d-none');
        }
    }

    /**
     * 성공 메시지 표시 (임시 토스트)
     */
    showSuccess(message) {
        // 임시 토스트 생성
        const toast = document.createElement('div');
        toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        // 3초 후 자동 제거
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);

        this.hideError();
    }

    /**
     * 확인 대화상자 표시
     */
    showConfirm(message, onConfirm, onCancel = null) {
        const modal = modalManager.createModal('confirmModal', '확인', `
            <p>${message}</p>
        `, [
            { text: '취소', class: 'btn-secondary', action: 'cancel' },
            { text: '확인', class: 'btn-primary', action: 'confirm' }
        ]);

        modal.querySelector('[data-action="confirm"]').onclick = () => {
            modalManager.closeModal(modal);
            if (onConfirm) onConfirm();
        };

        modal.querySelector('[data-action="cancel"]').onclick = () => {
            modalManager.closeModal(modal);
            if (onCancel) onCancel();
        };

        modalManager.showModal(modal);
    }

    /**
     * 현재 단계 반환
     */
    getCurrentStep() {
        return this.currentStep;
    }

    /**
     * 페이지 제목 업데이트
     */
    updatePageTitle(title) {
        document.title = title ? `${title} - LLM 기반 차트 생성 시스템` : 'LLM 기반 차트 생성 시스템';
    }

    /**
     * 브라우저 뒤로가기 처리
     */
    handleBrowserBack() {
        // 브라우저 뒤로가기 시 히스토리 기반 네비게이션
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.step) {
                sessionHistory.goToStep(event.state.step);
            }
        });
    }

    /**
     * 브라우저 히스토리에 상태 추가
     */
    pushBrowserHistory(stepData) {
        const state = {
            step: sessionHistory.currentStep,
            timestamp: Date.now()
        };
        
        const url = new URL(window.location);
        url.searchParams.set('step', sessionHistory.currentStep);
        
        history.pushState(state, '', url);
    }

    /**
     * 키보드 단축키 설정
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + Enter: 현재 단계 진행
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                event.preventDefault();
                this.handleKeyboardSubmit();
            }

            // Escape: 모달 닫기
            if (event.key === 'Escape') {
                modalManager.closeAllModals();
            }

            // Ctrl/Cmd + Z: 이전 단계로
            if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
                event.preventDefault();
                this.goToPreviousStep();
            }
        });
    }

    /**
     * 키보드 제출 처리
     */
    handleKeyboardSubmit() {
        switch (this.currentStep) {
            case 3:
                this.handleChartGeneration();
                break;
            default:
                // 현재 포커스된 버튼이 있으면 클릭
                const focusedBtn = document.activeElement;
                if (focusedBtn && focusedBtn.tagName === 'BUTTON') {
                    focusedBtn.click();
                }
                break;
        }
    }

    /**
     * 이전 단계로 이동
     */
    goToPreviousStep() {
        if (sessionHistory.currentStep > 0) {
            const previousStep = sessionHistory.goToStep(sessionHistory.currentStep - 1);
            if (previousStep) {
                this.handleHistoryStepChange({ step: previousStep, index: sessionHistory.currentStep });
            }
        }
    }

    /**
     * 반응형 디자인 처리
     */
    handleResponsiveDesign() {
        const checkScreenSize = () => {
            const isMobile = window.innerWidth < 768;
            document.body.classList.toggle('mobile-view', isMobile);
            
            // 모바일에서는 테이블 스크롤 개선
            if (isMobile) {
                document.querySelectorAll('.table-responsive').forEach(table => {
                    table.style.fontSize = '0.8rem';
                });
            }
        };

        window.addEventListener('resize', checkScreenSize);
        checkScreenSize(); // 초기 실행
    }

    /**
     * 초기화
     */
    initialize() {
        this.setupKeyboardShortcuts();
        this.handleBrowserBack();
        this.handleResponsiveDesign();
        
        // 로컬 스토리지에서 히스토리 복원 시도
        if (sessionHistory.loadFromLocalStorage()) {
            const currentStep = sessionHistory.getCurrentStep();
            if (currentStep) {
                this.handleHistoryStepChange({ step: currentStep, index: sessionHistory.currentStep });
            }
        }
    }
}

// 전역 UI 컨트롤러 인스턴스
window.uiController = new UIController();