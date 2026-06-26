// app/static/js/dashboard.js

// ============================================================
// LOAD BOTS
// ============================================================

async function loadBots() {
    try {
        const response = await fetch('/api/bots');
        const data = await response.json();
        
        if (data.ok) {
            renderBots(data.bots);
            updateStats(data.bots);
        } else {
            showError('Không thể tải danh sách bot');
        }
    } catch (error) {
        console.error('Error loading bots:', error);
        showError('Lỗi kết nối đến server');
    }
}

// ============================================================
// RENDER BOTS
// ============================================================

function renderBots(bots) {
    const tbody = document.getElementById('bot-list');
    
    if (!bots || bots.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-secondary py-4">
                    <i class="fas fa-robot fa-2x d-block mb-2"></i>
                    Chưa có bot nào
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = '';
    
    bots.forEach((bot, index) => {
        const status = bot.status ? '🟢 Đang chạy' : '🔴 Đã tắt';
        const statusClass = bot.status ? 'badge-status-on' : 'badge-status-off';
        const type = bot.mainBot 
            ? '<span class="badge badge-main">MAIN</span>' 
            : '<span class="badge badge-sub">SUB</span>';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>
                <strong>${bot.username || 'Unknown'}</strong>
            </td>
            <td>
                <code class="text-secondary" style="font-size:0.75rem;">
                    ${bot.botIntId || bot.imei || 'N/A'}
                </code>
            </td>
            <td>
                <code class="text-accent">${bot.prefix || '?'}</code>
            </td>
            <td>${type}</td>
            <td class="${statusClass}">${status}</td>
            <td>
                <small class="text-secondary">
                    ${bot.expiredTime || 'Vĩnh viễn'}
                </small>
            </td>
            <td>
                <button class="btn-action btn-start" onclick="botAction('${bot.botIntId || bot.imei}', 'start')" title="Start">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn-action btn-stop" onclick="botAction('${bot.botIntId || bot.imei}', 'stop')" title="Stop">
                    <i class="fas fa-stop"></i>
                </button>
                <button class="btn-action btn-restart" onclick="botAction('${bot.botIntId || bot.imei}', 'restart')" title="Restart">
                    <i class="fas fa-sync"></i>
                </button>
                <button class="btn-action btn-delete" onclick="deleteBot('${bot.botIntId || bot.imei}')" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============================================================
// UPDATE STATS
// ============================================================

function updateStats(bots) {
    let total = bots.length;
    let active = bots.filter(b => b.status).length;
    let inactive = total - active;
    let main = bots.filter(b => b.mainBot).length;
    
    document.getElementById('total-bots').textContent = total;
    document.getElementById('active-bots').textContent = active;
    document.getElementById('inactive-bots').textContent = inactive;
    document.getElementById('main-bots').textContent = main;
}

// ============================================================
// BOT ACTIONS
// ============================================================

async function botAction(botId, action) {
    const actionNames = {
        'start': 'khởi động',
        'stop': 'dừng',
        'restart': 'khởi động lại'
    };
    
    if (!confirm(`Xác nhận ${actionNames[action] || action} bot này?`)) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/bot/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bot_id: botId,
                action: action
            })
        });
        
        const data = await response.json();
        
        if (data.ok) {
            showToast(`✅ ${actionNames[action] || action} bot thành công!`, 'success');
            loadBots();
        } else {
            showToast(`❌ Lỗi: ${data.error || 'Không xác định'}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('❌ Lỗi kết nối server', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================================
// DELETE BOT
// ============================================================

async function deleteBot(botId) {
    if (!confirm('⚠️ Xóa bot này? Hành động không thể hoàn tác!')) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/bot/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                bot_id: botId
            })
        });
        
        const data = await response.json();
        
        if (data.ok) {
            showToast('🗑️ Đã xóa bot thành công!', 'success');
            loadBots();
        } else {
            showToast(`❌ Lỗi: ${data.error || 'Không xác định'}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('❌ Lỗi kết nối server', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================================
// TOAST NOTIFICATION
// ============================================================

function showToast(message, type = 'info') {
    const colors = {
        success: '#4caf50',
        error: '#f44336',
        warning: '#ff9800',
        info: '#4dabf7'
    };
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: #1a1f35;
        color: #e8eaf6;
        padding: 16px 24px;
        border-radius: 12px;
        border-left: 4px solid ${colors[type] || colors.info};
        box-shadow: 0 8px 30px rgba(0,0,0,0.5);
        z-index: 9999;
        max-width: 400px;
        animation: slideIn 0.3s ease;
        font-size: 0.95rem;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================================
// LOADING
// ============================================================

function showLoading(show) {
    // Có thể thêm loading spinner nếu cần
}

// ============================================================
// ERROR HANDLER
// ============================================================

function showError(message) {
    showToast(`❌ ${message}`, 'error');
}

// ============================================================
// INIT
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadBots();
    
    // Auto refresh mỗi 30 giây
    setInterval(loadBots, 30000);
});

// ============================================================
// CSS ANIMATION (inject)
// ============================================================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .text-accent {
        color: #4dabf7;
    }
`;
document.head.appendChild(style);