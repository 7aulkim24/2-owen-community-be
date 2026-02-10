import { getErrorMessage, getSuccessMessage } from './error-messages.js';

// API 베이스 URL 설정
// window.APP_CONFIG.API_BASE_URL (Runtime Config) 우선, 없으면 localhost
export const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || `http://${window.location.hostname}:8000`;

/**
 * 이미지 경로를 전체 URL로 변환합니다.
 * @param {string} path - 이미지 경로 (예: /public/image/profile/...)
 * @returns {string} 전체 URL 또는 기본 이미지 경로
 */
export const getFullImageUrl = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    if (path.startsWith('/public')) return `${API_BASE_URL}${path}`;
    return path;
};

// 표준 API 요청 함수
// 백엔드의 StandardResponse 포맷(code, message, data, details)을 처리합니다.
export const request = async (url, options = {}) => {
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            credentials: 'include', // 세션 쿠키 포함을 위해 필수
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        // 응답 헤더에서 Request ID 추출
        const requestId = response.headers.get('X-Request-ID') || 'LOCAL';

        // 204 No Content 처리
        if (response.status === 204) return null;

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            // 백엔드 에러 응답 처리 (StandardResponse 포맷)
            const errorMessage = result.message || 'API 요청에 실패했습니다.';
            const error = new Error(errorMessage);
            error.code = result.code;
            error.details = result.details;
            error.requestId = requestId; // 에러 객체에 ID 주입
            throw error;
        }

        // 성공 시 데이터와 코드 함께 반환 (StandardResponse 포맷 대응)
        return {
            data: result.data,
            code: result.code
        };
    } catch (error) {
        // 에러 발생 지점과 ID를 명확히 출력
        const location = error.requestId ? 'Backend/DB' : 'Frontend/Network';
        console.error(`[${error.requestId || 'N/A'}] [${location}] Error:`, {
            message: error.message,
            code: error.code,
            url: `${API_BASE_URL}${url}`,
            options: options,
            stack: error.stack
        });
        throw error;
    }
};

/**
 * 전역 토스트 메시지 표시 함수
 * @param {string} message - 표시할 메시지
 * @param {string} type - 'success', 'error' 등 (기본: 'success')
 */
export const showToast = (message, type = 'success') => {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // 다음 프레임에서 show 클래스 추가하여 애니메이션 작동
    setTimeout(() => toast.classList.add('show'), 10);

    // 3초 후 제거
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
};

/**
 * 공통 API 에러 처리 함수
 * @param {Error} error - 에러 객체
 * @param {HTMLElement} formElement - 에러 메시지를 표시할 폼 요소 (선택사항)
 */
export const handleApiError = (error, formElement = null) => {
    // 네트워크 에러 (fetch 실패 등)
    if (!error.code) {
        const networkMsg = '네트워크 오류가 발생했습니다. 서버 연결을 확인해주세요.';
        showToast(networkMsg, 'error');
        return networkMsg;
    }

    // 에러 코드 기반 메시지 조회
    const message = getErrorMessage(error.code, error.message);

    // 인증 오류 처리 (401 Unauthorized 등)
    if (error.code === 'UNAUTHORIZED' || error.code === 'INVALID_SESSION') {
        showToast(message, 'error');
        // 세션 만료 시 로그인 페이지로 리다이렉트
        setTimeout(() => {
            localStorage.removeItem('user');
            window.location.replace('/login.html');
        }, 1500);
        return message;
    }

    // 백엔드 검증 에러 처리 (Pydantic ValidationError 등)
    if (error.details && typeof error.details === 'object' && formElement) {
        Object.entries(error.details).forEach(([field, messages]) => {
            const helperElement = formElement.querySelector(`#${field}-helper`) ||
                                formElement.querySelector(`[data-field="${field}"] .helper-text`);

            if (helperElement) {
                const displayMsg = Array.isArray(messages) ? messages[0] : messages;
                helperElement.textContent = `*${displayMsg}`;
                helperElement.style.color = '#e74c3c';
            }
        });
    }

    // 일반 에러 메시지 토스트 표시
    showToast(message, 'error');
    return message;
};

/**
 * 전역 모달 표시 함수
 * @param {Object} options - 모달 옵션 { title, message, confirmText, onConfirm, type }
 */
export const showModal = ({ title, message, confirmText = '확인', onConfirm = null, type = 'success' }) => {
    // 기존에 생성된 전역 모달이 있다면 제거 (이벤트 리스너 중첩 방지 및 초기화)
    const existingModal = document.getElementById('cursor-global-modal');
    if (existingModal) {
        existingModal.remove();
    }

    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'cursor-global-modal';
    modalOverlay.className = 'modal-overlay';
    modalOverlay.style.cssText = 'display: flex; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.4); justify-content: center; align-items: center; z-index: 9999;';

    modalOverlay.innerHTML = `
        <div class="modal" style="background: white; padding: 40px; border-radius: 20px; width: 90%; max-width: 400px; text-align: center; position: relative;">
            <h3 id="cursor-global-modal-title" style="font-size: 20px; font-weight: 700; margin-bottom: 15px;"></h3>
            <p id="cursor-global-modal-message" style="font-size: 14px; color: #000; margin-bottom: 30px;"></p>
            <div class="modal-buttons" style="display: flex; gap: 10px; justify-content: center;">
                <button type="button" class="btn-modal btn-confirm" id="cursor-global-modal-confirm" style="flex: 1; padding: 12px; border-radius: 10px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; background-color: #ACA0EB; color: white;">확인</button>
            </div>
        </div>
    `;

    document.body.appendChild(modalOverlay);

    const titleEl = modalOverlay.querySelector('#cursor-global-modal-title');
    const messageEl = modalOverlay.querySelector('#cursor-global-modal-message');
    const confirmBtn = modalOverlay.querySelector('#cursor-global-modal-confirm');

    titleEl.textContent = title;
    messageEl.textContent = message;
    confirmBtn.textContent = confirmText;

    // 버튼 클릭 이벤트
    confirmBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        modalOverlay.style.display = 'none'; // 즉시 숨김
        modalOverlay.remove(); // 요소 제거
        if (onConfirm) onConfirm();
    };

    // 오버레이 클릭 시 닫히지 않도록 설정 (중요한 알림이므로)
    modalOverlay.onclick = (e) => {
        if (e.target === modalOverlay) {
            // e.stopPropagation(); // 막아도 되고 안막아도 됨
        }
    };
};

/**
 * 공통 API 성공 처리 함수
 * @param {Object} response - API 응답 객체 { data, code }
 * @param {boolean|string|Object} options - 표시할 메시지(string), 토스트 표시 여부(boolean), 또는 모달 옵션(Object)
 * @returns {string} 매핑된 성공 메시지
 */
export const handleApiSuccess = (response, options = true) => {
    let message;
    const code = response?.code;

    if (typeof options === 'string') {
        message = options;
        showToast(message, 'success');
    } else if (typeof options === 'object' && options !== null && options.modal) {
        // 모달 표시 옵션이 있는 경우
        // options.code가 있으면 해당 코드로 매핑, 없으면 응답의 code 사용
        message = options.message || getSuccessMessage(options.code || code);
        showModal({
            title: options.title || '알림',
            message: message,
            onConfirm: options.onConfirm
        });
    } else {
        message = getSuccessMessage(code);
        if (options === true) {
            showToast(message, 'success');
        }
    }
    return message;
};

// HTTP 메서드별 편의 함수
export const get = (url) => request(url, { method: 'GET' });
export const post = (url, data) => request(url, {
    method: 'POST',
    body: JSON.stringify(data)
});
export const patch = (url, data) => request(url, {
    method: 'PATCH',
    body: JSON.stringify(data)
});
export const del = (url) => request(url, { method: 'DELETE' });

/**
 * 파일 업로드를 위한 유틸리티 함수
 * @param {string} url - API 엔드포인트
 * @param {File} file - 업로드할 파일 객체
 * @param {string} fieldName - 백엔드에서 기대하는 폼 필드 이름
 * @returns {Promise<any>} - 업로드 결과 (StandardResponse.data)
 */
export const uploadFile = async (url, file, fieldName = 'file') => {
    const formData = new FormData();
    formData.append(fieldName, file);

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: 'POST',
            credentials: 'include',
            body: formData,
            // Content-Type 헤더를 설정하지 않아야 브라우저가 자동으로
            // multipart/form-data와 함께 boundary를 설정합니다.
        });

        // 응답 헤더에서 Request ID 추출
        const requestId = response.headers.get('X-Request-ID') || 'LOCAL';

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            const errorMessage = result.message || '파일 업로드에 실패했습니다.';
            const error = new Error(errorMessage);
            error.code = result.code;
            error.requestId = requestId; // 에러 객체에 ID 주입
            throw error;
        }

        return {
            data: result.data || {},
            code: result.code
        };
    } catch (error) {
        // 에러 발생 지점과 ID를 명확히 출력
        const location = error.requestId ? 'Backend/DB' : 'Frontend/Network';
        console.error(`[${error.requestId || 'N/A'}] [${location}] Upload Error:`, {
            message: error.message,
            code: error.code,
            url: `${API_BASE_URL}${url}`,
            stack: error.stack
        });
        throw error;
    }
};
