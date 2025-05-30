/**
 * ModalManager - 모달 창 관리
 */
class ModalManager {
    constructor() {
        this.openModals = new Set();
        this.modalContainer = null;
        this.initializeContainer();
    }

    /**
     * 모달 컨테이너 초기화
     */
    initializeContainer() {
        this.modalContainer = document.getElementById('modalContainer');
        if (!this.modalContainer) {
            this.modalContainer = document.createElement('div');
            this.modalContainer.id = 'modalContainer';
            document.body.appendChild(this.modalContainer);
        }
    }

    /**
     * 모달 생성
     */
    createModal(id, title, body, buttons = []) {
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', `${id}Label`);
        modal.setAttribute('aria-hidden', 'true');

        const buttonHtml = buttons.map(btn => 
            `<button type="button" class="btn ${btn.class}" data-action="${btn.action}">${btn.text}</button>`
        ).join('');

        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="${id}Label">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${body}
                    </div>
                    ${buttons.length ? `<div class="modal-footer">${buttonHtml}</div>` : ''}
                </div>
            </div>
        `;

        // 기본 이벤트 바인딩
        this.bindModalEvents(modal);

        return modal;
    }

    /**
     * 모달 이벤트 바인딩
     */
    bindModalEvents(modal) {
        // 닫기 버튼 이벤트
        const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"], [data-action="close"]');
        closeButtons.forEach(btn => {
            btn.onclick = () => this.closeModal(modal);
        });

        // 배경 클릭으로 닫기
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        };

        // ESC 키로 닫기
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
            }
        });
    }

    /**
     * 모달 표시
     */
    showModal(modal) {
        this.modalContainer.appendChild(modal);
        this.openModals.add(modal);

        // Bootstrap 모달 초기화 및 표시
        const bsModal = new bootstrap.Modal(modal);
        modal._bsModal = bsModal;
        bsModal.show();

        // 첫 번째 입력 필드에 포커스
        setTimeout(() => {
            const firstInput = modal.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 300);

        return bsModal;
    }

    /**
     * 모달 닫기
     */
    closeModal(modal) {
        if (modal._bsModal) {
            modal._bsModal.hide();
        }

        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            this.openModals.delete(modal);
        }, 300);
    }

    /**
     * 모든 모달 닫기
     */
    closeAllModals() {
        this.openModals.forEach(modal => {
            this.closeModal(modal);
        });
    }

    /**
     * 메타데이터 보기 모달
     */
    showMetadataModal() {
        const modal = this.createModal('metadataModal', '테이블 메타데이터', `
            <div id="metadataContent">
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">로딩 중...</span>
                    </div>
                    <p class="mt-2">메타데이터를 불러오는 중입니다...</p>
                </div>
            </div>
        `, [
            { text: '닫기', class: 'btn-secondary', action: 'close' }
        ]);

        this.showModal(modal);

        // 메타데이터 로드
        this.loadMetadata(modal);
    }

    /**
     * 메타데이터 로드
     */
    async loadMetadata(modal) {
        try {
            const response = await fetch(`/${username}/get_json_data/`);
            if (!response.ok) {
                throw new Error('메타데이터를 가져오지 못했습니다.');
            }

            const data = await response.json();
            const contentDiv = modal.querySelector('#metadataContent');
            contentDiv.innerHTML = '<div id="jsonTree"></div>';
            
            this.buildJsonTree(data, modal.querySelector('#jsonTree'));

        } catch (error) {
            console.error('Error loading metadata:', error);
            const contentDiv = modal.querySelector('#metadataContent');
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h6>오류</h6>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * JSON 트리 빌드
     */
    buildJsonTree(data, parentElement, level = 0) {
        if (typeof data === 'object' && data !== null) {
            const keys = Object.keys(data);
            const ul = document.createElement('ul');
            ul.className = 'json-tree';

            for (const key of keys) {
                const li = document.createElement('li');
                const span = document.createElement('span');
                span.textContent = `${key}:`;
                span.style.fontWeight = 'bold';
                span.style.color = '#495057';

                if (typeof data[key] === 'object' && data[key] !== null) {
                    span.style.cursor = 'pointer';
                    const toggleIcon = document.createElement('span');
                    toggleIcon.textContent = ' ▶';
                    toggleIcon.style.marginLeft = '5px';
                    toggleIcon.style.color = '#6c757d';
                    span.appendChild(toggleIcon);

                    const valueContainer = document.createElement('div');
                    valueContainer.style.display = 'none';
                    
                    span.onclick = () => {
                        const isVisible = valueContainer.style.display === 'block';
                        valueContainer.style.display = isVisible ? 'none' : 'block';
                        toggleIcon.textContent = isVisible ? ' ▶' : ' ▼';
                        
                        if (!isVisible && valueContainer.children.length === 0) {
                            this.buildJsonTree(data[key], valueContainer, level + 1);
                        }
                    };

                    li.appendChild(span);
                    li.appendChild(valueContainer);
                } else {
                    const valueSpan = document.createElement('span');
                    valueSpan.textContent = ` ${data[key]}`;
                    valueSpan.style.color = '#28a745';
                    valueSpan.style.marginLeft = '10px';
                    span.appendChild(valueSpan);
                    li.appendChild(span);
                }

                ul.appendChild(li);
            }
            parentElement.appendChild(ul);
        }
    }

    /**
     * 히스토리 모달
     */
    showHistoryModal() {
        const modal = this.createModal('historyModal', '작업 히스토리', `
            <div id="historyContent">
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">로딩 중...</span>
                    </div>
                    <p class="mt-2">히스토리를 불러오는 중입니다...</p>
                </div>
            </div>
        `, [
            { text: '닫기', class: 'btn-secondary', action: 'close' }
        ]);

        this.showModal(modal);

        // 히스토리 로드
        this.loadHistory(modal);
    }

    /**
     * 히스토리 로드
     */
    async loadHistory(modal) {
        try {
            const response = await fetch(`/${username}/get_history`);
            if (!response.ok) {
                throw new Error('히스토리를 가져오지 못했습니다.');
            }

            const historyData = await response.json();
            const contentDiv = modal.querySelector('#historyContent');
            
            if (historyData.length === 0) {
                contentDiv.innerHTML = `
                    <div class="text-center text-muted">
                        <p>저장된 히스토리가 없습니다.</p>
                    </div>
                `;
                return;
            }

            const historyHtml = historyData
                .filter(item => !item.folder.endsWith('_backup'))
                .map(item => {
                    const date = new Date(parseInt(item.folder.split('_')[1]) * 1000);
                    const formattedDate = date.toLocaleString();
                    
                    return `
                        <div class="card mb-2">
                            <div class="card-body d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="card-title mb-1">${item.folder}</h6>
                                    <small class="text-muted">${formattedDate}</small>
                                </div>
                                <div>
                                    <button class="btn btn-sm btn-outline-primary me-2" 
                                            onclick="modalManager.viewHistoryFiles('${item.folder}')">
                                        파일 보기
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" 
                                            onclick="modalManager.deleteHistoryFolder('${item.folder}')">
                                        삭제
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');

            contentDiv.innerHTML = `
                <div class="mb-3">
                    <p class="text-muted">이전 작업 기록을 확인하고 관리할 수 있습니다.</p>
                </div>
                ${historyHtml}
            `;

        } catch (error) {
            console.error('Error loading history:', error);
            const contentDiv = modal.querySelector('#historyContent');
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h6>오류</h6>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * 히스토리 파일 보기
     */
    async viewHistoryFiles(folderName) {
        try {
            const response = await fetch(`/${username}/get_files?folder=${folderName}`);
            if (!response.ok) {
                throw new Error('파일 목록을 가져오지 못했습니다.');
            }

            const files = await response.json();
            
            const fileListHtml = files.map(file => {
                const icon = this.getFileIcon(file.type);
                return `
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                        <div class="d-flex align-items-center">
                            <span class="me-2">${icon}</span>
                            <span>${file.name}</span>
                        </div>
                        <button class="btn btn-sm btn-outline-secondary" 
                                onclick="modalManager.viewFile('${folderName}', '${file.name}', '${file.type}')">
                            보기
                        </button>
                    </div>
                `;
            }).join('');

            const modal = this.createModal('filesModal', `${folderName} 파일 목록`, `
                <div class="mb-3">
                    <p class="text-muted">폴더에 포함된 파일들을 확인할 수 있습니다.</p>
                </div>
                <div class="files-list">
                    ${fileListHtml}
                </div>
            `, [
                { text: '닫기', class: 'btn-secondary', action: 'close' }
            ]);

            this.showModal(modal);

        } catch (error) {
            uiController.showError(error.message);
        }
    }

    /**
     * 파일 아이콘 가져오기
     */
    getFileIcon(fileType) {
        const icons = {
            'json': '📄',
            'sql': '🔍',
            'csv': '📊',
            'png': '🖼️',
            'jpg': '🖼️',
            'jpeg': '🖼️'
        };
        return icons[fileType] || '📄';
    }

    /**
     * 파일 내용 보기
     */
    async viewFile(folderName, fileName, fileType) {
        try {
            if (fileType === 'png' || fileType === 'jpg' || fileType === 'jpeg') {
                // 이미지 파일
                const modal = this.createModal('fileViewModal', fileName, `
                    <div class="text-center">
                        <img src="/${username}/get_files?folder=${folderName}&file=${fileName}" 
                             class="img-fluid" style="max-height: 500px;" />
                    </div>
                `, [
                    { text: '닫기', class: 'btn-secondary', action: 'close' }
                ]);
                this.showModal(modal);
            } else {
                // 텍스트 파일
                const response = await fetch(`/${username}/get_files?folder=${folderName}&file=${fileName}`);
                if (!response.ok) {
                    throw new Error('파일을 가져오지 못했습니다.');
                }
    
                // 한 번만 읽고 변수에 저장
                const data = await response.json();
                
                let content;
                if (fileType === 'json') {
                    content = `<div id="jsonFileTree"></div>`;
                } else {
                    content = `<pre class="code-block">${data.content}</pre>`;
                }
    
                const modal = this.createModal('fileViewModal', fileName, content, [
                    { text: '닫기', class: 'btn-secondary', action: 'close' }
                ]);
    
                this.showModal(modal);
    
                // JSON 파일인 경우 트리 생성 (이미 읽은 data 사용)
                if (fileType === 'json') {
                    this.buildJsonTree(data, modal.querySelector('#jsonFileTree'));
                }
            }
    
        } catch (error) {
            uiController.showError(error.message);
        }
    }

    /**
     * 히스토리 폴더 삭제
     */
    async deleteHistoryFolder(folderName) {
        if (!confirm(`${folderName} 폴더를 정말로 삭제하시겠습니까?`)) {
            return;
        }

        try {
            const response = await fetch(`/${username}/delete_folder?folder=${folderName}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('폴더 삭제에 실패했습니다.');
            }

            uiController.showSuccess('폴더가 성공적으로 삭제되었습니다.');
            
            // 히스토리 모달 새로고침
            const historyModal = document.getElementById('historyModal');
            if (historyModal) {
                this.loadHistory(historyModal);
            }

        } catch (error) {
            uiController.showError(error.message);
        }
    }
}

// 전역 모달 매니저 인스턴스
window.modalManager = new ModalManager();