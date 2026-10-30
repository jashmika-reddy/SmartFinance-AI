// SmartFinance AI - Main UI Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss flash messages after 6 seconds
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });

    // Mobile sidebar toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }
});

// Modal Helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = 'auto';
    }
}

// AI Advisor Interactive Consultation Chat
function sendAdvisorMessage(promptText = null) {
    const input = document.getElementById('advisor-chat-input');
    const msg = promptText || (input ? input.value.trim() : '');
    if (!msg) return;

    if (input) input.value = '';

    const chatWindow = document.getElementById('advisor-chat-messages');
    if (!chatWindow) return;

    // Append User Message
    const userBubble = document.createElement('div');
    userBubble.className = 'flex justify-end mb-4';
    userBubble.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-lg shadow-md text-sm">
            ${escapeHtml(msg)}
        </div>
    `;
    chatWindow.appendChild(userBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Loading indicator
    const loadingBubble = document.createElement('div');
    loadingBubble.id = 'chat-loading-indicator';
    loadingBubble.className = 'flex justify-start mb-4';
    loadingBubble.innerHTML = `
        <div class="bg-slate-800 text-gray-300 rounded-2xl rounded-tl-none px-4 py-3 max-w-lg border border-slate-700/60 shadow-md text-sm flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
            <span>Analyzing financial risk parameters...</span>
        </div>
    `;
    chatWindow.appendChild(loadingBubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    fetch('/advisor/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
        const loader = document.getElementById('chat-loading-indicator');
        if (loader) loader.remove();

        // Format bot response
        let pointsHtml = '';
        if (data.key_points && data.key_points.length > 0) {
            pointsHtml = `
                <div class="mt-3 pt-3 border-t border-slate-700/60 text-xs text-indigo-300 space-y-1">
                    ${data.key_points.map(pt => `<div class="flex items-start space-x-1.5"><span class="text-indigo-400 font-bold">•</span><span>${escapeHtml(pt)}</span></div>`).join('')}
                </div>
            `;
        }

        const botBubble = document.createElement('div');
        botBubble.className = 'flex justify-start mb-4';
        botBubble.innerHTML = `
            <div class="bg-slate-800 text-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-lg border border-slate-700/80 shadow-md text-sm">
                <div class="font-semibold text-indigo-400 text-xs mb-1 flex items-center space-x-1.5">
                    <i class="fa-solid fa-robot"></i>
                    <span>SmartFinance AI Advisor</span>
                </div>
                <div class="prose prose-invert prose-sm leading-relaxed">${formatMarkdown(data.answer)}</div>
                ${pointsHtml}
            </div>
        `;
        chatWindow.appendChild(botBubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    })
    .catch(err => {
        const loader = document.getElementById('chat-loading-indicator');
        if (loader) loader.remove();
        console.error('Advisor chat error:', err);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';
    // Basic bold and list rendering
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n- /g, '<br>• ');
    return html;
}

