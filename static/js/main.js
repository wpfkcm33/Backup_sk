/**
 * Main Application Logic
 * 애플리케이션 초기화 및 전체 흐름 관리
 */

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', async function() {
    console.log('애플리케이션 초기화 시작...');
    
    try {
        // UI 컨트롤러 초기화
        uiController.initialize();
        
        // 미리 정의된 쿼리 로드
        await dataManager.loadPredefinedQueries();
        
        console.log('애플리케이션 초기화 완료');
        
        // 초기 상태 설정
        setupInitialState();
        
    } catch (error) {
        console.error('애플리케이션 초기화 중 오류:', error);
        uiController.showError('애플리케이션을 초기화하는 중 오류가 발생했습니다.');
    }
});

/**
 * 초기 상태 설정
 */
function setupInitialState() {
    // URL 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const stepParam = urlParams.get('step');
    
    if (stepParam && sessionHistory.steps.length > 0) {
        const stepIndex = parseInt(stepParam);
        if (stepIndex >= 0 && stepIndex < sessionHistory.steps.length) {
            sessionHistory.goToStep(stepIndex);
        }
    }
    
    // 웰컴 메시지 (첫 방문자용)
    if (!sessionHistory.steps.length && !localStorage.getItem(`welcomed_${username}`)) {
        showWelcomeMessage();
        localStorage.setItem(`welcomed_${username}`, 'true');
    }
}

/**
 * 웰컴 메시지 표시
 */
function showWelcomeMessage() {
    setTimeout(() => {
        const modal = modalManager.createModal('welcomeModal', '환영합니다! 🎉', `
            <div class="text-center">
                <h5 class="text-primary mb-3">LLM 기반 차트 생성 시스템에 오신 것을 환영합니다!</h5>
                <p class="mb-3">이 시스템은 다음과 같은 단계로 작동합니다:</p>
                
                <div class="row text-start">
                    <div class="col-md-6 mb-3">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-primary rounded-pill me-2">1</span>
                            <div>
                                <strong>예시 데이터 선택</strong>
                                <br><small class="text-muted">미리 준비된 데이터 중 분석하고 싶은 데이터를 선택하세요</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-success rounded-pill me-2">2</span>
                            <div>
                                <strong>데이터 확인 및 수정</strong>
                                <br><small class="text-muted">추출된 데이터를 확인하고 필요시 수정 요청하세요</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-info rounded-pill me-2">3</span>
                            <div>
                                <strong>차트 생성</strong>
                                <br><small class="text-muted">원하는 차트 형태를 자연어로 요청하세요</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="d-flex align-items-start">
                            <span class="badge bg-warning rounded-pill me-2">4</span>
                            <div>
                                <strong>차트 수정 및 완성</strong>
                                <br><small class="text-muted">생성된 차트를 원하는 대로 수정하고 다운로드하세요</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-info mt-3">
                    <small><strong>💡 팁:</strong> 각 단계에서 이전 단계로 돌아가거나 다른 옵션을 시도해볼 수 있습니다!</small>
                </div>
            </div>
        `, [
            { text: '시작하기', class: 'btn-primary', action: 'close' }
        ]);

        modalManager.showModal(modal);
    }, 1000);
}

/**
 * 에러 처리 설정
 */
function setupErrorHandling() {
    // 전역 에러 핸들러
    window.addEventListener('error', function(event) {
        console.error('전역 에러:', event.error);
        uiController.showError('예상치 못한 오류가 발생했습니다. 페이지를 새로고침해 주세요.');
    });

    // Promise rejection 핸들러
    window.addEventListener('unhandledrejection', function(event) {
        console.error('처리되지 않은 Promise 거부:', event.reason);
        uiController.showError('네트워크 오류가 발생했습니다. 연결을 확인해 주세요.');
    });
}

/**
 * 성능 모니터링 설정
 */
function setupPerformanceMonitoring() {
    // 페이지 로드 시간 측정
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`페이지 로드 시간: ${loadTime.toFixed(2)}ms`);
        
        // 5초 이상 걸리면 경고
        if (loadTime > 5000) {
            console.warn('페이지 로드가 느립니다.');
        }
    });
}

/**
 * 브라우저 지원 확인
 */
function checkBrowserSupport() {
    const requiredFeatures = [
        'fetch',
        'localStorage',
        'CustomEvent',
        'URLSearchParams'
    ];

    const unsupportedFeatures = requiredFeatures.filter(feature => !(feature in window));
    
    if (unsupportedFeatures.length > 0) {
        uiController.showError(
            `이 브라우저는 일부 기능을 지원하지 않습니다. 최신 브라우저를 사용해 주세요.\n` +
            `지원되지 않는 기능: ${unsupportedFeatures.join(', ')}`
        );
        return false;
    }
    
    return true;
}

/**
 * 개발 모드 설정
 */
function setupDevelopmentMode() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('개발 모드 활성화');
        
        // 개발용 단축키
        document.addEventListener('keydown', function(event) {
            // Ctrl+Shift+D: 디버그 정보 출력
            if (event.ctrlKey && event.shiftKey && event.key === 'D') {
                console.log('=== 디버그 정보 ===');
                console.log('세션 히스토리:', sessionHistory.debug());
                console.log('현재 데이터:', dataManager.getCurrentData());
                console.log('현재 차트:', chartManager.getCurrentChartData());
                console.log('현재 단계:', uiController.getCurrentStep());
            }
            
            // Ctrl+Shift+C: 히스토리 클리어
            if (event.ctrlKey && event.shiftKey && event.key === 'C') {
                if (confirm('세션 히스토리를 클리어하시겠습니까?')) {
                    sessionHistory.clear();
                    uiController.startNewAnalysis();
                }
            }
        });
        
        // 전역 디버그 함수 등록
        window.debugApp = {
            sessionHistory,
            dataManager,
            chartManager,
            uiController,
            modalManager
        };
    }
}

/**
 * 사용자 활동 추적 (옵션)
 */
function setupUserActivityTracking() {
    let lastActivity = Date.now();
    
    // 사용자 활동 감지
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, function() {
            lastActivity = Date.now();
        });
    });
    
    // 5분마다 비활성 상태 확인
    setInterval(function() {
        const inactiveTime = Date.now() - lastActivity;
        if (inactiveTime > 300000) { // 5분
            console.log('사용자 비활성 상태 감지');
            // 필요시 세션 상태 저장
            sessionHistory.saveToLocalStorage();
        }
    }, 60000); // 1분마다 체크
}

/**
 * 접근성 개선
 */
function setupAccessibility() {
    // 키보드 네비게이션 개선
    document.addEventListener('keydown', function(event) {
        // Tab 키로 포커스 이동 시 시각적 표시
        if (event.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });

    // 마우스 클릭 시 키보드 네비게이션 모드 해제
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });

    // 스크린 리더를 위한 라이브 영역 설정
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.id = 'liveRegion';
    document.body.appendChild(liveRegion);

    // 상태 변경 시 스크린 리더에 알림
    window.addEventListener('historyStepChanged', function(event) {
        const stepNames = {
            'predefined': '예시 데이터 선택됨',
            'data_modified': '데이터 수정됨',
            'chart_created': '차트 생성됨',
            'chart_modified': '차트 수정됨'
        };
        
        const message = stepNames[event.detail.step.type] || '단계 변경됨';
        liveRegion.textContent = message;
    });
}

/**
 * 앱 초기화 완료 후 설정
 */
function initializeAppFeatures() {
    setupErrorHandling();
    setupPerformanceMonitoring();
    setupAccessibility();
    
    if (checkBrowserSupport()) {
        setupDevelopmentMode();
        setupUserActivityTracking();
    }
}

// 초기화 완료 후 추가 기능 설정
window.addEventListener('load', initializeAppFeatures);

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', function() {
    // 현재 상태 저장
    sessionHistory.saveToLocalStorage();
    
    // 리소스 정리
    modalManager.closeAllModals();
});

/**
 * 유틸리티 함수들
 */
window.AppUtils = {
    /**
     * 날짜 포맷팅
     */
    formatDate: function(timestamp) {
        return new Date(timestamp).toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * 파일 크기 포맷팅
     */
    formatFileSize: function(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * 텍스트 복사
     */
    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            uiController.showSuccess('클립보드에 복사되었습니다.');
        } catch (error) {
            console.error('클립보드 복사 실패:', error);
            uiController.showError('클립보드 복사에 실패했습니다.');
        }
    },

    /**
     * 디바운스 함수
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * 쓰로틀 함수
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

console.log('메인 애플리케이션 로직 로드 완료');