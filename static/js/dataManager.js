/**
 * DataManager - 데이터 관련 작업 관리
 */
class DataManager {
    constructor() {
        this.predefinedQueries = [];
        this.currentData = null;
        this.currentSql = null;
    }

    /**
     * 미리 정의된 쿼리 목록 로드
     */
    async loadPredefinedQueries() {
        try {
            const response = await fetch(`/${username}/get_predefined_queries`);
            if (!response.ok) {
                throw new Error('미리 정의된 쿼리를 가져오지 못했습니다.');
            }
            
            this.predefinedQueries = await response.json();
            this.renderPredefinedQueries();
            return this.predefinedQueries;
        } catch (error) {
            console.error('Error loading predefined queries:', error);
            uiController.showError('미리 정의된 쿼리를 로드하는 중 오류가 발생했습니다.');
            return [];
        }
    }

    /**
     * 미리 정의된 쿼리 UI 렌더링
     */
    renderPredefinedQueries() {
        const container = document.getElementById('predefinedQueries');
        if (!container) return;

        container.innerHTML = '';

        this.predefinedQueries.forEach((query, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const card = document.createElement('div');
            card.className = 'card predefined-query-card h-100';
            card.dataset.queryId = query.id;
            card.onclick = () => this.selectPredefinedQuery(query);

            card.innerHTML = `
                <div class="card-body">
                    <h6 class="query-title">${query.name}</h6>
                    <p class="query-description">${query.description}</p>
                    <small class="query-sample-count">예상 데이터: ${query.estimated_rows || '알 수 없음'}행</small>
                </div>
            `;

            col.appendChild(card);
            container.appendChild(col);
        });
    }

    /**
     * 미리 정의된 쿼리 선택
     */
    async selectPredefinedQuery(query) {
        try {
            // 선택된 카드 하이라이트
            document.querySelectorAll('.predefined-query-card').forEach(card => {
                card.classList.remove('selected');
            });
            document.querySelector(`[data-query-id="${query.id}"]`).classList.add('selected');

            uiController.showLoading('데이터를 추출하는 중입니다...');

            // 미리 정의된 쿼리 실행
            const response = await fetch(`/${username}/execute_predefined_query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `query_id=${encodeURIComponent(query.id)}`
            });

            if (!response.ok) {
                throw new Error('데이터 추출에 실패했습니다.');
            }

            const result = await response.json();
            
            // 데이터 저장
            this.currentData = result.result_data;
            this.currentSql = result.sql_query;

            // 히스토리에 저장
            sessionHistory.saveStep(
                sessionHistory.stepTypes.PREDEFINED,
                {
                    query: query,
                    sql: result.sql_query,
                    data: result.result_data
                },
                `선택: ${query.name}`
            );

            // UI 업데이트
            this.showDataResult(query, result);
            uiController.hideLoading();

        } catch (error) {
            console.error('Error executing predefined query:', error);
            uiController.hideLoading();
            uiController.showError(error.message);
        }
    }

    /**
     * 데이터 결과 표시
     */
    showDataResult(query, result) {
        // 2단계 카드 표시
        uiController.showStep(2);
        
        // 제목 설정
        document.getElementById('selectedQueryTitle').textContent = query.name;
        
        // 데이터 테이블 생성
        this.createDataTable(result.result_data);
        
        // SQL 쿼리 표시
        document.getElementById('currentSqlQuery').textContent = result.sql_query;

        // 스크롤 이동
        document.getElementById('step2Card').scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * 데이터 수정 요청 처리
     */
    async modifyData(modificationRequest) {
        try {
            uiController.showLoading('데이터를 수정하는 중입니다...');

            const response = await fetch(`/${username}/modify_sql`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `original_sql=${encodeURIComponent(this.currentSql)}&modification_request=${encodeURIComponent(modificationRequest)}&current_data=${encodeURIComponent(JSON.stringify(this.currentData))}`
            });

            if (!response.ok) {
                throw new Error('데이터 수정에 실패했습니다.');
            }

            const result = await response.json();

            // 데이터 업데이트
            this.currentData = result.result_data;
            this.currentSql = result.sql_query;

            // 히스토리에 저장
            sessionHistory.saveStep(
                sessionHistory.stepTypes.DATA_MODIFIED,
                {
                    modificationRequest: modificationRequest,
                    sql: result.sql_query,
                    data: result.result_data
                },
                modificationRequest
            );

            // UI 업데이트
            this.createDataTable(result.result_data);
            document.getElementById('currentSqlQuery').textContent = result.sql_query;

            uiController.hideLoading();
            uiController.showSuccess('데이터가 성공적으로 수정되었습니다.');

        } catch (error) {
            console.error('Error modifying data:', error);
            uiController.hideLoading();
            uiController.showError(error.message);
        }
    }

    /**
     * 데이터 테이블 생성
     */
    createDataTable(data) {
        const tableHead = document.getElementById('dataTableHead');
        const tableBody = document.getElementById('dataTableBody');

        // 테이블 초기화
        tableHead.innerHTML = '';
        tableBody.innerHTML = '';

        // 데이터가 없는 경우
        if (!data || data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="100%" class="text-center py-3">데이터가 없습니다.</td></tr>';
            return;
        }

        // 테이블 헤더 생성
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.scope = 'col';
            th.textContent = key;
            headerRow.appendChild(th);
        });
        tableHead.appendChild(headerRow);

        // 테이블 본문 생성 (최대 50행)
        const maxRows = Math.min(data.length, 50);
        for (let i = 0; i < maxRows; i++) {
            const row = data[i];
            const tr = document.createElement('tr');
            
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                
                // 값 처리
                if (value === null || value === undefined) {
                    td.textContent = '-';
                    td.className = 'text-muted';
                } else if (typeof value === 'number') {
                    td.textContent = value.toLocaleString();
                    td.style.textAlign = 'right';
                } else {
                    td.textContent = value;
                }
                
                tr.appendChild(td);
            });
            
            tableBody.appendChild(tr);
        }

        // 행 수 제한 메시지
        if (data.length > 50) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = Object.keys(data[0]).length;
            td.className = 'text-center text-muted py-2';
            td.textContent = `전체 ${data.length}행 중 50행만 표시합니다.`;
            tr.appendChild(td);
            tableBody.appendChild(tr);
        }
    }

    /**
     * 현재 데이터 가져오기
     */
    getCurrentData() {
        return {
            data: this.currentData,
            sql: this.currentSql
        };
    }

    /**
     * 데이터 다운로드
     */
    downloadData() {
        if (!this.currentData) {
            uiController.showError('다운로드할 데이터가 없습니다.');
            return;
        }

        const dataToDownload = {
            sql_query: this.currentSql,
            result_data: this.currentData,
            timestamp: new Date().toISOString(),
            total_rows: this.currentData.length
        };

        const blob = new Blob([JSON.stringify(dataToDownload, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `data_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * 히스토리에서 단계 복원
     */
    restoreFromHistory(step) {
        if (step.type === sessionHistory.stepTypes.PREDEFINED || 
            step.type === sessionHistory.stepTypes.DATA_MODIFIED) {
            
            this.currentData = step.data.data;
            this.currentSql = step.data.sql;

            // UI 업데이트
            if (step.type === sessionHistory.stepTypes.PREDEFINED) {
                this.showDataResult(step.data.query, {
                    result_data: step.data.data,
                    sql_query: step.data.sql
                });
            } else {
                uiController.showStep(2);
                this.createDataTable(step.data.data);
                document.getElementById('currentSqlQuery').textContent = step.data.sql;
            }
        }
    }
}

// 전역 데이터 매니저 인스턴스
window.dataManager = new DataManager();