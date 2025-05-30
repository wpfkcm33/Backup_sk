/**
 * SessionHistory - 사용자 세션의 단계별 히스토리 관리
 */
class SessionHistory {
    constructor() {
        this.steps = [];
        this.currentStep = -1;
        this.stepTypes = {
            PREDEFINED: 'predefined',
            DATA_MODIFIED: 'data_modified',
            CHART_CREATED: 'chart_created',
            CHART_MODIFIED: 'chart_modified'
        };
    }

    /**
     * 새로운 단계 저장
     * @param {string} stepType - 단계 유형
     * @param {Object} data - 단계 데이터
     * @param {string} userInput - 사용자 입력
     */
    saveStep(stepType, data, userInput = '') {
        const step = {
            type: stepType,
            timestamp: Date.now(),
            data: data,
            userInput: userInput,
            id: this.generateStepId()
        };

        // 현재 위치 이후의 단계들 제거 (새로운 분기 생성)
        this.steps = this.steps.slice(0, this.currentStep + 1);
        this.steps.push(step);
        this.currentStep = this.steps.length - 1;

        this.updateNavigationUI();
        this.saveToLocalStorage();
        
        return step;
    }

    /**
     * 특정 단계로 이동
     * @param {number} stepIndex - 이동할 단계 인덱스
     * @returns {Object|null} 해당 단계 데이터
     */
    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.steps.length) {
            this.currentStep = stepIndex;
            this.updateNavigationUI();
            this.saveToLocalStorage();
            return this.steps[stepIndex];
        }
        return null;
    }

    /**
     * 현재 단계 가져오기
     * @returns {Object|null}
     */
    getCurrentStep() {
        if (this.currentStep >= 0 && this.currentStep < this.steps.length) {
            return this.steps[this.currentStep];
        }
        return null;
    }

    /**
     * 특정 타입의 가장 최근 단계 가져오기
     * @param {string} stepType - 단계 타입
     * @returns {Object|null}
     */
    getLastStepOfType(stepType) {
        for (let i = this.currentStep; i >= 0; i--) {
            if (this.steps[i].type === stepType) {
                return this.steps[i];
            }
        }
        return null;
    }

    /**
     * 현재 단계의 모든 시도 기록 가져오기
     * @returns {Array}
     */
    getCurrentStepHistory() {
        const currentType = this.getCurrentStep()?.type;
        if (!currentType) return [];

        return this.steps.filter(step => step.type === currentType);
    }

    /**
     * 단계 ID 생성
     * @returns {string}
     */
    generateStepId() {
        return `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 네비게이션 UI 업데이트
     */
    updateNavigationUI() {
        const breadcrumb = document.getElementById('stepBreadcrumb');
        const historyContainer = document.getElementById('stepHistoryContainer');
        const historyItems = document.getElementById('stepHistoryItems');
        const navigation = document.getElementById('historyNavigation');

        if (!breadcrumb) return;

        // 히스토리가 있으면 네비게이션 표시
        if (this.steps.length > 0) {
            navigation.classList.remove('d-none');
        }

        // 브레드크럼 업데이트
        const stepNames = {
            [this.stepTypes.PREDEFINED]: '예시 선택',
            [this.stepTypes.DATA_MODIFIED]: '데이터 수정',
            [this.stepTypes.CHART_CREATED]: '차트 생성',
            [this.stepTypes.CHART_MODIFIED]: '차트 수정'
        };

        const uniqueStepTypes = [...new Set(this.steps.map(step => step.type))];
        const currentStepType = this.getCurrentStep()?.type;

        breadcrumb.innerHTML = '';
        uniqueStepTypes.forEach((stepType, index) => {
            const li = document.createElement('li');
            li.className = 'breadcrumb-item';

            if (stepType === currentStepType) {
                li.classList.add('active');
                li.textContent = stepNames[stepType] || stepType;
            } else {
                li.classList.add('completed');
                const a = document.createElement('a');
                a.href = '#';
                a.textContent = stepNames[stepType] || stepType;
                a.onclick = (e) => {
                    e.preventDefault();
                    this.goToLastStepOfType(stepType);
                };
                li.appendChild(a);
            }

            breadcrumb.appendChild(li);
        });

        // 현재 단계의 히스토리 아이템들 업데이트
        const currentStepHistory = this.getCurrentStepHistory();
        if (currentStepHistory.length > 1) {
            historyContainer.classList.remove('d-none');
            historyItems.innerHTML = '';

            currentStepHistory.forEach((step, index) => {
                const item = document.createElement('div');
                item.className = 'step-history-item';
                if (step.id === this.getCurrentStep()?.id) {
                    item.classList.add('current');
                }

                const time = new Date(step.timestamp).toLocaleTimeString();
                item.textContent = `시도 ${index + 1} (${time})`;
                item.onclick = () => {
                    const stepIndex = this.steps.findIndex(s => s.id === step.id);
                    if (stepIndex !== -1) {
                        this.goToStep(stepIndex);
                        // UI 업데이트 이벤트 발생
                        window.dispatchEvent(new CustomEvent('historyStepChanged', {
                            detail: { step: step, index: stepIndex }
                        }));
                    }
                };

                historyItems.appendChild(item);
            });
        } else {
            historyContainer.classList.add('d-none');
        }
    }

    /**
     * 특정 타입의 마지막 단계로 이동
     * @param {string} stepType
     */
    goToLastStepOfType(stepType) {
        for (let i = this.steps.length - 1; i >= 0; i--) {
            if (this.steps[i].type === stepType) {
                this.goToStep(i);
                // UI 업데이트 이벤트 발생
                window.dispatchEvent(new CustomEvent('historyStepChanged', {
                    detail: { step: this.steps[i], index: i }
                }));
                break;
            }
        }
    }

    /**
     * 로컬 스토리지에 저장
     */
    saveToLocalStorage() {
        try {
            const data = {
                steps: this.steps,
                currentStep: this.currentStep,
                timestamp: Date.now()
            };
            localStorage.setItem(`sessionHistory_${username}`, JSON.stringify(data));
        } catch (error) {
            console.warn('Failed to save session history to localStorage:', error);
        }
    }

    /**
     * 로컬 스토리지에서 복원
     */
    loadFromLocalStorage() {
        try {
            const data = localStorage.getItem(`sessionHistory_${username}`);
            if (data) {
                const parsed = JSON.parse(data);
                // 1시간 이내의 데이터만 복원
                if (Date.now() - parsed.timestamp < 3600000) {
                    this.steps = parsed.steps || [];
                    this.currentStep = parsed.currentStep || -1;
                    this.updateNavigationUI();
                    return true;
                }
            }
        } catch (error) {
            console.warn('Failed to load session history from localStorage:', error);
        }
        return false;
    }

    /**
     * 히스토리 초기화
     */
    clear() {
        this.steps = [];
        this.currentStep = -1;
        this.updateNavigationUI();
        try {
            localStorage.removeItem(`sessionHistory_${username}`);
        } catch (error) {
            console.warn('Failed to clear session history from localStorage:', error);
        }
        
        // 네비게이션 숨기기
        const navigation = document.getElementById('historyNavigation');
        if (navigation) {
            navigation.classList.add('d-none');
        }
    }

    /**
     * 디버그용 히스토리 정보 출력
     */
    debug() {
        console.log('Session History Debug:', {
            steps: this.steps,
            currentStep: this.currentStep,
            currentStepData: this.getCurrentStep()
        });
    }
}

// 전역 히스토리 인스턴스
window.sessionHistory = new SessionHistory();