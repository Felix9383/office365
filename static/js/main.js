// API 调用工具函数
const API = {
    async getSubscriptions() {
        const response = await fetch('/api/subscriptions');
        return await response.json();
    },

    async createSubscription(data) {
        const response = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    async updateSubscription(id, data) {
        const response = await fetch(`/api/subscriptions/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    async deleteSubscription(id) {
        const response = await fetch(`/api/subscriptions/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    },

    async checkSubscription(id) {
        const response = await fetch(`/api/subscriptions/${id}/check`, {
            method: 'POST'
        });
        return await response.json();
    }
};

// 工具函数
const Utils = {
    formatDate(dateString) {
        if (!dateString) return '未知';
        return new Date(dateString).toLocaleDateString('zh-CN');
    },

    formatDateTime(dateString) {
        if (!dateString) return '从未检测';
        return new Date(dateString).toLocaleString('zh-CN');
    },

    showLoading(element) {
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.textContent = '处理中...';
    },

    hideLoading(element) {
        element.disabled = false;
        element.textContent = element.dataset.originalText || '确定';
    },

    showAlert(message, type = 'info') {
        alert(message);
    }
};

// 导出供 HTML 使用
window.API = API;
window.Utils = Utils;
