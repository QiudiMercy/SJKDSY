let gameUid = null;
let gameState = null;
let map = null;
let currentMarkers = [];
let selectedPoi = null;
let isChatBusy = false;
let recordsPage = 1;
let lastActivityTime = null;
let gameTimerInterval = null; // 计时器句柄

document.addEventListener('DOMContentLoaded', () => {
    // 开始页
    showView('view-start');
    loadRecords(1);

    // 绑定事件
    document.getElementById('btn-start-game').addEventListener('click', startGame);
    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    }); 
    document.getElementById('send-btn').addEventListener('click', () => sendMessage());
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    // 弹窗取消
    document.getElementById('route-close').addEventListener('click', hideRouteModal);

    document.addEventListener('click', (e) => {
        const resultsEl = document.getElementById('search-results');
        const searchPanel = document.getElementById('search-panel');
        if (resultsEl && searchPanel && !searchPanel.contains(e.target)) {
            resultsEl.classList.add('hidden');
        }
    });

    document.querySelectorAll('.transport-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            fetchRoutes(mode);
        });
    });
    document.getElementById('btn-back-home').addEventListener('click', backToHome);
});

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
}

async function loadRecords(page) {
    recordsPage = page;
    const listEl = document.getElementById('records-list');
    const paginationEl = document.getElementById('records-pagination');
    listEl.innerHTML = '<p class="loading-text">加载中...</p>';

    try {
        const result = await apiGet('/api/records/list', { page, limit: 10 });
        if (result.code !== 200) {
            listEl.innerHTML = '<p class="empty-text">无法请求历史战绩</p>';
            return;
        }
        const data = result.data;
        if (!data.records || data.records.length === 0) {
            listEl.innerHTML = '<p class="empty-text">还没有游戏记录，快来开始第一局吧！</p>';
            paginationEl.innerHTML = '';
            return;
        }

        listEl.innerHTML = data.records.map(r => `
            <div class="record-item">
                <span class="record-time">${r.start_time}</span>
                <span class="record-score">评分：${r.score}</span>
                <span class="record-money">剩余金币：${r.remain_money}</span>
                <span class="record-eval">${r.evaluation || ''}</span>
            </div>
        `).join('');

        let pagesHtml = '';
        if (data.total_pages > 1) {
            for (let i = 1; i <= data.total_pages; i++) {
                pagesHtml += `<button class="page-btn ${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
            }
        }
        paginationEl.innerHTML = pagesHtml;
        paginationEl.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => loadRecords(parseInt(btn.dataset.page)));
        });
    } catch (err) {
        console.error('加载战绩失败:', err);
        listEl.innerHTML = '<p class="error-text">加载失败，请检查网络</p>';
    }
}

async function apiGet(path, params = {}) {
    const url = new URL(path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
        if (v !== null && v !== undefined) url.searchParams.append(k, v);
    });
    const resp = await fetch(url.toString());
    return resp.json();
}

async function apiPost(path, body = {}) {
    const resp = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return resp.json();
}

// 格式化距离显示 — 后端返回的是 km 数值或 "X.Xkm" 字符串
function formatDistance(raw) {
    const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''));
    if (isNaN(num)) return String(raw);
    if (num < 1) return Math.round(num * 1000) + 'm';
    return num.toFixed(1) + 'km';
}

async function startGame() {
    const btn = document.getElementById('btn-start-game');
    btn.disabled = true;
    btn.textContent = '正在创建游戏...';

    try {
        const result = await apiPost('/api/game/start');
        if (result.code !== 200) {
            alert('游戏创建失败：' + (result.msg || '未知错误'));
            btn.disabled = false;
            btn.textContent = '开始游戏';
            return;
        }

        const data = result.data;
        gameUid = data.game_uid;
        gameState = data.init_state;
        gameState.is_game_over = false;
        
        showView('view-game');

        updateStatusBar(gameState);
        
        initMap(gameState.location.lng, gameState.location.lat);

        setChatEnabled(true);

        addSystemMessage('游戏开始！你在成都东站接到了小爱。带她开启美好的一天吧！');

        // 启动游戏计时器（1:100 时间流逝）
        lastActivityTime = Date.now();
    } catch (err) {
        console.error('游戏开始失败:', err);
        alert('网络错误，请重试');
        btn.disabled = false;
        btn.textContent = '开始游戏';
    }
}

// 状态栏
function updateStatusBar(state) {
    if (!state) return;
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    setVal('stat-money', state.money);
    setVal('stat-time', state.time);
    setVal('stat-mood', state.mood);
    setVal('stat-stamina', state.stamina);
    setVal('stat-fullness', state.fullness);
    if (state.location && state.location.name) {
        setVal('stat-location', state.location.name);
    }
    // 高亮归零项
    ['money', 'stamina', 'mood', 'fullness'].forEach(key => {
        const el = document.getElementById('stat-' + key);
        if (el) {
            if (state[key] <= 0) el.classList.add('stat-critical');
            else if (state[key] < 30) el.classList.add('stat-warning');
            else {
                el.classList.remove('stat-critical', 'stat-warning');
            }
        }
    });

    const timeEl = document.getElementById('stat-time');
    if (timeEl && state.time) {
        const parts = state.time.split(':');
        const hour = parseInt(parts[0]);
        if (hour >= 21) timeEl.classList.add('stat-critical');
        else if (hour >= 20) timeEl.classList.add('stat-warning');
        else timeEl.classList.remove('stat-critical', 'stat-warning');
    }
}

function initMap(lng, lat) {
    const container = document.getElementById('map-container');
    if (!container) return;

    if (map) {
        map.clearOverlays();
        currentMarkers = [];
    }

    const centerLng = lng || 104.0668;
    const centerLat = lat || 30.6598;

    map = new BMap.Map('map-container');
    const point = new BMap.Point(centerLng, centerLat);
    map.centerAndZoom(point, 14);
    map.addControl(new BMap.NavigationControl());
    map.addControl(new BMap.ScaleControl());
    map.enableScrollWheelZoom(true);

    if (lng && lat) {
        addMarker(lng, lat, gameState ? (gameState.location ? gameState.location.name : '当前位置') : '当前位置', true);
    }
}

function addMarker(lng, lat, title, isCenter = false) {
    const point = new BMap.Point(lng, lat);

    let icon;
    if (isCenter) {
        icon = new BMap.Icon(
            'data:image/svg+xml,' + encodeURIComponent(
              '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">' +
              '<circle cx="12" cy="12" r="10" fill="#1890FF" stroke="#fff" stroke-width="3"/>' +
              '<circle cx="12" cy="12" r="4" fill="#fff"/>' +
              '</svg>'),
            new BMap.Size(24, 24),
            { anchor: new BMap.Size(12, 12) }
        );
    } else {
        icon = new BMap.Icon(
            'data:image/svg+xml,' + encodeURIComponent(
              '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="28" viewBox="0 0 20 28">' +
              '<path d="M10 0C4.5 0 0 4.5 0 10c0 7.5 10 18 10 18s10-10.5 10-18C20 4.5 15.5 0 10 0z" fill="#FF6B35" stroke="#fff" stroke-width="1.5"/>' +
              '<circle cx="10" cy="9" r="4" fill="#fff"/>' +
              '</svg>'),
            new BMap.Size(20, 28),
            { anchor: new BMap.Size(10, 28) }
        );
    }

    const marker = new BMap.Marker(point, { icon: icon });
    map.addOverlay(marker);
    currentMarkers.push(marker);

    const label = new BMap.Label(title, {
        offset: new BMap.Size(isCenter ? 16 : 12, isCenter ? -30 : -36),
        position: point
    });
    label.setStyle({
        background: isCenter ? '#1890FF' : '#FF6B35',
        color: '#fff',
        fontSize: '12px',
        padding: '2px 8px',
        borderRadius: '4px',
        border: 'none',
        whiteSpace: 'nowrap',
        fontWeight: 'bold'
    });
    map.addOverlay(label);
    currentMarkers.push(label);

    const infoWindow = new BMap.InfoWindow(title, { width: 120, height: 40 });
    marker.addEventListener('click', () => {
        marker.openInfoWindow(infoWindow);
    });

    return marker;
}

function clearMarkers() {
    if (!map) return;
    currentMarkers.forEach(m => map.removeOverlay(m));
    currentMarkers = [];
}

// 移动地图中心到指定坐标
function panTo(lng, lat) {
    if (!map) return;
    map.panTo(new BMap.Point(lng, lat));
}

// 聊天功能
function setChatEnabled(enabled) {
    document.getElementById('message-input').disabled = !enabled;
    document.getElementById('send-btn').disabled = !enabled;
}
// 发送消息 (SSE 流式)
async function sendMessage(textOverride) {
    const inputEl = document.getElementById('message-input');
    const content = textOverride || inputEl.value.trim();
    if (!content || isChatBusy || !gameUid) return;

    const now = Date.now();
    let timePassedMin = 0;
    if (lastActivityTime) {
        const elapsedRealSec = (now - lastActivityTime) / 1000;
        timePassedMin = Math.floor(elapsedRealSec * 84 / 60);
    }
    lastActivityTime = now;
    addUserMessage(content);
    if (!textOverride) inputEl.value = '';

    const typingBubble = addTypingIndicator();
    setChatEnabled(false);
    isChatBusy = true;

    try {
        const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game_uid: gameUid, content: content, time_passed_min: timePassedMin })
        });

        if (!response.ok) {
            removeElement(typingBubble);
            addSystemMessage('服务器错误，请稍后重试');
            setChatEnabled(true);
            isChatBusy = false;
            return;
        }

        removeElement(typingBubble);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const events = buffer.split('\n\n');
            buffer = events.pop(); // 剩余不完整的事件留在 buffer

            for (const eventStr of events) {
                if (!eventStr.trim()) continue;
                const parsed = parseSSEEvent(eventStr);
                if (!parsed) continue;

                if (parsed.event === 'message') {
                    const segmentText = parsed.data.segment;
                    if (segmentText) {
                        let segmentBubble = createAiMessageBubble();
                        updateAiBubbleContent(segmentBubble, segmentText);
                    }
                } else if (parsed.event === 'status') {
                    if (parsed.data.updates) {
                        if (!gameState) gameState = {};
                        const updates = parsed.data.updates;
                        Object.keys(updates).forEach(k => {
                            gameState[k] = updates[k];
                        });
                        updateStatusBar(gameState);

                        const locUpdate = updates.location;
                        if (locUpdate && locUpdate.lng && locUpdate.lat) {
                            clearMarkers();
                            addMarker(locUpdate.lng, locUpdate.lat, locUpdate.name || '当前位置', true);
                            panTo(locUpdate.lng, locUpdate.lat);
                            document.getElementById('transport-btns').classList.add('hidden');
                            selectedPoi = null;
                        }
                    }
                    if (parsed.data.system_reply) {
                        addSystemMessage(parsed.data.system_reply);
                    }
                } else if (parsed.event === 'done') {
                }
            }
        }

        await checkGameOver();
    } catch (err) {
        console.error('聊天请求失败:', err);
        addSystemMessage('网络连接失败，请检查网络后重试');
    } finally {
        setChatEnabled(true);
        isChatBusy = false;
    }
}

// 解析 SSE 事件字符串
function parseSSEEvent(raw) {
    const lines = raw.split('\n');
    let eventType = '';
    let dataStr = '';

    for (const line of lines) {
        if (line.startsWith('event: ')) {
            eventType = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
            dataStr = line.substring(6).trim();
        }
    }
    if (!eventType || !dataStr) return null;
    try {
        return { event: eventType, data: JSON.parse(dataStr) };
    } catch (e) {
        return null;
    }
}

// 检查游戏是否结束
async function checkGameOver() {
    if (!gameUid) return;
    try {
        const result = await apiGet('/api/game/state', { game_uid: gameUid });
        if (result.code === 200 && result.data) {
            gameState = result.data;
            updateStatusBar(gameState);
            if (gameState.is_game_over) {
                await doSettle();
            }
        }
    } catch (err) {
        console.error('状态检查失败:', err);
    }
}

// 气泡
function addUserMessage(text) {
    const container = document.getElementById('chat-messages');
    hideChatHint();
    const div = document.createElement('div');
    div.className = 'message msg-user';
    div.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
    container.appendChild(div);
    scrollChatBottom();
    return div;
}

function createAiMessageBubble() {
    const container = document.getElementById('chat-messages');
    hideChatHint();
    const div = document.createElement('div');
    div.className = 'message msg-ai';
    div.innerHTML = `<div class="message-bubble"></div>`;
    container.appendChild(div);
    scrollChatBottom();
    return div;
}

function updateAiBubbleContent(bubble, text) {
    if (!bubble) return;
    const content = bubble.querySelector('.message-bubble');
    if (content) content.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    scrollChatBottom();
}

function addSystemMessage(text) {
    const container = document.getElementById('chat-messages');
    hideChatHint();
    const div = document.createElement('div');
    div.className = 'message msg-system';
    div.innerHTML = `<div class="message-system-text">${escapeHtml(text)}</div>`;
    container.appendChild(div);
    scrollChatBottom();
    return div;
}

function addTypingIndicator() {
    const container = document.getElementById('chat-messages');
    hideChatHint();
    const div = document.createElement('div');
    div.className = 'message msg-ai';
    div.innerHTML = `<div class="message-bubble typing-indicator">
        <span></span><span></span><span></span>
    </div>`;
    container.appendChild(div);
    scrollChatBottom();
    return div;
}

function removeElement(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

function hideChatHint() {
    const hint = document.getElementById('chat-hint');
    if (hint) hint.style.display = 'none';
}

function scrollChatBottom() {
    const container = document.getElementById('chat-messages');
    if (container) {
        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });
    }
}

// POI 搜索
async function doSearch() {
    const inputEl = document.getElementById('search-input');
    const keyword = inputEl.value.trim();
    if (!keyword || !gameUid) return;

    const resultsEl = document.getElementById('search-results');
    resultsEl.innerHTML = '<p class="loading-text">搜索中...</p>';
    resultsEl.classList.remove('hidden');

    try {
        const lng = gameState.location ? gameState.location.lng : 104.0668;
        const lat = gameState.location ? gameState.location.lat : 30.6598;
        const result = await apiGet('/api/poi/search', { keyword, lng, lat });

        if (result.code !== 200 || !result.data || !result.data.poi_list || result.data.poi_list.length === 0) {
            resultsEl.innerHTML = '<p class="empty-text">未找到相关地点</p>';
            return;
        }

        const poiList = result.data.poi_list;
        poiList.sort((a, b) => {
            const da = parseFloat(String(a.distance).replace(/[^0-9.]/g, '')) || 0;
            const db = parseFloat(String(b.distance).replace(/[^0-9.]/g, '')) || 0;
            return da - db;
        });
        resultsEl.innerHTML = poiList.map((poi, idx) => `
            <div class="search-result-item" data-index="${idx}">
                <div class="result-info">
                    <span class="result-name">${escapeHtml(poi.name)}</span>
                    <span class="result-type">${escapeHtml(poi.type)}</span>
                </div>
                <span class="result-distance">${formatDistance(poi.distance)}</span>
            </div>
        `).join('');

        resultsEl.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const idx = parseInt(item.dataset.index);
                const poi = poiList[idx];
                selectPoi(poi);
                resultsEl.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
            });
        });
    } catch (err) {
        console.error('POI 搜索失败:', err);
        resultsEl.innerHTML = '<p class="error-text">搜索失败，请重试</p>';
    }
}

// 选中 POI：地图标注 + 显示交通方式按钮
function selectPoi(poi) {
    selectedPoi = poi;

    // 地图标注
    clearMarkers();
    if (gameState && gameState.location) {
        addMarker(gameState.location.lng, gameState.location.lat, gameState.location.name, true);
    }
    addMarker(poi.lng, poi.lat, poi.name, false);
    panTo(poi.lng, poi.lat);

    document.getElementById('transport-btns').classList.remove('hidden');
    document.querySelectorAll('.transport-btn').forEach(btn => {
        btn.title = `${btn.textContent}去${poi.name}`;
    });
}

// 路线预估
async function fetchRoutes(transportMode) {
    if (!selectedPoi || !gameUid) return;

    const modal = document.getElementById('route-modal');
    const optionsEl = document.getElementById('route-options');
    const titleEl = document.getElementById('route-title');

    const modeLabels = { walking: '步行', bicycling: '骑行', driving: '驾车', transit: '公交' };

    titleEl.textContent = `${modeLabels[transportMode] || ''}去 ${selectedPoi.name}`;
    optionsEl.innerHTML = '<p class="loading-text">正在计算路线...</p>';
    modal.classList.remove('hidden');

    try {
        const lng = gameState.location ? gameState.location.lng : 104.0668;
        const lat = gameState.location ? gameState.location.lat : 30.6598;
        const result = await apiPost('/api/action/route', {
            target_poi_uid: selectedPoi.poi_uid,
            current_lng: lng,
            current_lat: lat,
            transport_mode: transportMode
        });

        if (result.code !== 200 || !result.data || !result.data.routes) {
            optionsEl.innerHTML = '<p class="error-text">路线获取失败</p>';
            return;
        }

        const routes = result.data.routes;
        optionsEl.innerHTML = routes.map((route, idx) => {
            const staminaText = route.consume_stamina >= 0
                ? `+${route.consume_stamina}`
                : `${route.consume_stamina}`;
            const staminaClass = route.consume_stamina >= 0 ? 'stamina-gain' : 'stamina-cost';
            return `
                <div class="route-option" data-index="${idx}">
                    <div class="route-method">${escapeHtml(route.label)}</div>
                    <div class="route-details">
                        <span>花费：${route.cost_money} 元</span>
                        <span>耗时：${route.cost_time_min} 分钟</span>
                        <span>体力：<span class="${staminaClass}">${staminaText}</span></span>
                    </div>
                </div>
            `;
        }).join('');

        optionsEl.querySelectorAll('.route-option').forEach(opt => {
            opt.addEventListener('click', () => {
                const idx = parseInt(opt.dataset.index);
                const chosen = routes[idx];
                modal.classList.add('hidden');
                lastActivityTime = Date.now();
                const msg = `我们${chosen.label}去${selectedPoi.name}吧`;
                sendMessage(msg);
                hidePoiDetail();
            });
        });
    } catch (err) {
        console.error('路线获取失败:', err);
        optionsEl.innerHTML = '<p class="error-text">网络错误，请重试</p>';
    }
}

function hideRouteModal() {
    document.getElementById('route-modal').classList.add('hidden');
    document.getElementById('transport-btns').classList.add('hidden');
}

// 游戏结算
async function doSettle() {
    if (!gameUid) return;
    try {
        const result = await apiPost('/api/game/settle', { game_uid: gameUid });
        if (result.code !== 200) {
            console.error('结算失败:', result.msg);
            return;
        }

        const data = result.data;
        document.getElementById('settle-score').textContent = data.score;
        document.getElementById('settle-evaluation').textContent = data.evaluation || '';

        const routeList = document.getElementById('settle-route-list');
        if (data.route_summary && data.route_summary.length > 0) {
            routeList.innerHTML = data.route_summary.map(s => `<li>${escapeHtml(s)}</li>`).join('');
        } else {
            routeList.innerHTML = '<li>暂无路线记录</li>';
        }

        // 添加结束提示到聊天
        addSystemMessage('游戏结束！小爱的一天到此为止。');

        // 延迟切换到结算页
        setTimeout(() => {
            showView('view-settle');
            setChatEnabled(false);
        }, 1500);
    } catch (err) {
        console.error('结算失败:', err);
    }
}

function backToHome() {
    gameUid = null;
    gameState = null;
    selectedPoi = null;
    isChatBusy = false;
    lastActivityTime = null;
    if (map) {
        map.clearOverlays();
        currentMarkers = [];
    }
    document.getElementById('chat-messages').innerHTML = '<p class="chat-hint" id="chat-hint">开始和小爱对话吧~</p>';
    document.getElementById('search-input').value = '';
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('search-results').innerHTML = '';
    document.getElementById('transport-btns').classList.add('hidden');
    document.getElementById('route-modal').classList.add('hidden');
    showView('view-start');
    loadRecords(1);
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}