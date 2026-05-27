// =============================================================================
// 《带我玩》— 成都一日游 AI 游戏 · 前端脚本
// =============================================================================

// =============================================================================
// 全局状态
// =============================================================================
let gameUid = null;
let gameState = null;
let map = null;
let currentMarkers = [];
let selectedPoi = null;       // 当前选中要去的 POI
let isChatBusy = false;       // 正在等待 AI 回复中
let recordsPage = 1;
let lastActivityTime = null;  // 上次活动时间 (real milliseconds)
let gameTimerInterval = null; // 计时器句柄

// =============================================================================
// 工具函数
// =============================================================================

/** 切换视图 */
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const target = document.getElementById(viewId);
    if (target) target.classList.remove('hidden');
}

/** API 请求封装 (非 SSE) */
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

/** 格式化距离显示 — 后端返回的是 km 数值或 "X.Xkm" 字符串 */
function formatDistance(raw) {
    // 提取数值（处理 "1.5km"、"0.3" 等格式）
    const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''));
    if (isNaN(num)) return String(raw);
    if (num < 1) return Math.round(num * 1000) + 'm';
    return num.toFixed(1) + 'km';
}

// =============================================================================
// 初始化 — 页面加载完成
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    // 开始页
    showView('view-start');
    loadRecords(1);

    // 绑定事件
    document.getElementById('btn-start-game').addEventListener('click', startGame);
    document.getElementById('btn-back-home').addEventListener('click', backToHome);
    document.getElementById('send-btn').addEventListener('click', () => sendMessage());
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    });
    document.getElementById('route-close').addEventListener('click', hideRouteModal);

    // 点击搜索结果以外的地方自动收起
    document.addEventListener('click', (e) => {
        const resultsEl = document.getElementById('search-results');
        const searchPanel = document.getElementById('search-panel');
        if (resultsEl && searchPanel && !searchPanel.contains(e.target)) {
            resultsEl.classList.add('hidden');
        }
    });

    // 交通方式按钮
    document.querySelectorAll('.transport-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            fetchRoutes(mode);
        });
    });
});

// =============================================================================
// 历史战绩
// =============================================================================
async function loadRecords(page) {
    recordsPage = page;
    const listEl = document.getElementById('records-list');
    const paginationEl = document.getElementById('records-pagination');
    listEl.innerHTML = '<p class="loading-text">加载中...</p>';

    try {
        const result = await apiGet('/api/records/list', { page, limit: 10 });
        if (result.code !== 200) {
            listEl.innerHTML = '<p class="empty-text">暂无战绩</p>';
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

        // 分页按钮
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

// =============================================================================
// 游戏开始
// =============================================================================
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

        // 更新状态栏
        updateStatusBar(gameState);

        // 切换到游戏视图
        showView('view-game');

        // 初始化地图
        initMap(gameState.location.lng, gameState.location.lat);

        // 加载历史消息
        await loadChatHistory();

        // 启用聊天输入
        setChatEnabled(true);

        // 添加系统欢迎消息
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

// =============================================================================
// 状态栏更新
// =============================================================================
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

    // 更新时间颜色（接近 22:00 变红）
    const timeEl = document.getElementById('stat-time');
    if (timeEl && state.time) {
        const parts = state.time.split(':');
        const hour = parseInt(parts[0]);
        if (hour >= 21) timeEl.classList.add('stat-critical');
        else if (hour >= 20) timeEl.classList.add('stat-warning');
        else timeEl.classList.remove('stat-critical', 'stat-warning');
    }
}

// =============================================================================
// 百度地图初始化
// =============================================================================
function initMap(lng, lat) {
    const container = document.getElementById('map-container');
    if (!container) return;

    // 如果已经初始化过，先清理
    if (map) {
        map.clearOverlays();
        currentMarkers = [];
    }

    // 默认成都中心
    const centerLng = lng || 104.0668;
    const centerLat = lat || 30.6598;

    map = new BMap.Map('map-container');
    const point = new BMap.Point(centerLng, centerLat);
    map.centerAndZoom(point, 14);
    map.addControl(new BMap.NavigationControl());
    map.addControl(new BMap.ScaleControl());
    map.enableScrollWheelZoom(true);

    // 在当前位置添加标记
    if (lng && lat) {
        addMarker(lng, lat, gameState ? (gameState.location ? gameState.location.name : '当前位置') : '当前位置', true);
    }
}

/** 在地图上添加标记 */
function addMarker(lng, lat, title, isCenter = false) {
    const point = new BMap.Point(lng, lat);

    let icon;
    if (isCenter) {
        // 当前位置：大号蓝色圆点
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
        // POI 标记：橙色水滴
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

    // 给标记添加文字标签
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
    currentMarkers.push(label);  // 一并管理，clearMarkers 时清除

    // 点击弹出信息窗
    const infoWindow = new BMap.InfoWindow(title, { width: 120, height: 40 });
    marker.addEventListener('click', () => {
        marker.openInfoWindow(infoWindow);
    });

    return marker;
}

/** 清除所有标记 */
function clearMarkers() {
    if (!map) return;
    currentMarkers.forEach(m => map.removeOverlay(m));
    currentMarkers = [];
}

/** 移动地图中心到指定坐标 */
function panTo(lng, lat) {
    if (!map) return;
    map.panTo(new BMap.Point(lng, lat));
}

// =============================================================================
// 聊天功能
// =============================================================================

/** 启用/禁用聊天输入 */
function setChatEnabled(enabled) {
    document.getElementById('message-input').disabled = !enabled;
    document.getElementById('send-btn').disabled = !enabled;
}

/** 发送消息 (SSE 流式) */
async function sendMessage(textOverride) {
    const inputEl = document.getElementById('message-input');
    const content = textOverride || inputEl.value.trim();
    if (!content || isChatBusy || !gameUid) return;

    // 计算已流逝的游戏时间 (1 真实秒 = 84 游戏秒)
    const now = Date.now();
    let timePassedMin = 0;
    if (lastActivityTime) {
        const elapsedRealSec = (now - lastActivityTime) / 1000;
        timePassedMin = Math.floor(elapsedRealSec * 84 / 60);
    }
    lastActivityTime = now;
    addUserMessage(content);
    if (!textOverride) inputEl.value = '';

    // 显示 AI 正在输入
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

        // 移除"正在输入"
        removeElement(typingBubble);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            // 解析完整的 SSE 事件（以 \n\n 分隔）
            const events = buffer.split('\n\n');
            buffer = events.pop(); // 剩余不完整的事件留在 buffer

            for (const eventStr of events) {
                if (!eventStr.trim()) continue;
                const parsed = parseSSEEvent(eventStr);
                if (!parsed) continue;

                if (parsed.event === 'message') {
                    // 每一个分段独立展示一条消息框
                    const segmentText = parsed.data.segment;
                    if (segmentText) {
                        let segmentBubble = createAiMessageBubble();
                        updateAiBubbleContent(segmentBubble, segmentText);
                    }
                } else if (parsed.event === 'status') {
                    // 状态更新
                    if (parsed.data.updates) {
                        // 更新 gameState 中存在的字段
                        if (!gameState) gameState = {};
                        const updates = parsed.data.updates;
                        Object.keys(updates).forEach(k => {
                            gameState[k] = updates[k];
                        });
                        updateStatusBar(gameState);

                        // 如果位置变化，同步地图
                        const locUpdate = updates.location;
                        if (locUpdate && locUpdate.lng && locUpdate.lat) {
                            clearMarkers();
                            addMarker(locUpdate.lng, locUpdate.lat, locUpdate.name || '当前位置', true);
                            panTo(locUpdate.lng, locUpdate.lat);
                            // 隐藏交通按钮（已经到达新位置）
                            document.getElementById('transport-btns').classList.add('hidden');
                            selectedPoi = null;
                        }
                    }
                    if (parsed.data.system_reply) {
                        addSystemMessage(parsed.data.system_reply);
                    }
                } else if (parsed.event === 'done') {
                    // 对话结束，各个分段已在前文独立生成，无需额外操作
                }
            }
        }

        // 检查游戏是否结束（重新请求状态确认）
        await checkGameOver();
    } catch (err) {
        console.error('聊天请求失败:', err);
        addSystemMessage('网络连接失败，请检查网络后重试');
    } finally {
        setChatEnabled(true);
        isChatBusy = false;
    }
}

/** 解析 SSE 事件字符串 */
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

/** 检查游戏是否结束 */
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

// =============================================================================
// 聊天消息 UI
// =============================================================================

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

// =============================================================================
// 加载历史消息
// =============================================================================
async function loadChatHistory() {
    if (!gameUid) return;
    try {
        const result = await apiGet('/api/chat/history', { game_uid: gameUid });
        if (result.code !== 200 || !result.data || !result.data.messages) return;

        const container = document.getElementById('chat-messages');
        container.innerHTML = ''; // 清空
        if (result.data.messages.length === 0) {
            container.innerHTML = '<p class="chat-hint" id="chat-hint">开始和小爱对话吧~</p>';
            return;
        }
        hideChatHint();

        result.data.messages.forEach(msg => {
            if (msg.role === 'user') {
                addUserMessage(msg.content);
            } else if (msg.role === 'xiaoai') {
                const bubble = createAiMessageBubble();
                updateAiBubbleContent(bubble, msg.content);
            } else if (msg.role === 'system') {
                addSystemMessage(msg.content);
            }
        });
        scrollChatBottom();
    } catch (err) {
        console.error('加载历史消息失败:', err);
    }
}

// =============================================================================
// POI 搜索
// =============================================================================
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
        // 按距离由近及远排序（提取数值比较）
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

        // 点击搜索结果
        resultsEl.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const idx = parseInt(item.dataset.index);
                const poi = poiList[idx];
                selectPoi(poi);
                // 高亮选中项
                resultsEl.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
            });
        });
    } catch (err) {
        console.error('POI 搜索失败:', err);
        resultsEl.innerHTML = '<p class="error-text">搜索失败，请重试</p>';
    }
}

/** 选中 POI：地图标注 + 显示交通方式按钮 */
function selectPoi(poi) {
    selectedPoi = poi;

    // 地图标注
    clearMarkers();
    // 重新添加当前位置标记
    if (gameState && gameState.location) {
        addMarker(gameState.location.lng, gameState.location.lat, gameState.location.name, true);
    }
    // 添加 POI 标记
    addMarker(poi.lng, poi.lat, poi.name, false);
    panTo(poi.lng, poi.lat);

    // 显示交通方式按钮
    document.getElementById('transport-btns').classList.remove('hidden');
    // 更新按钮文字，标注目的地
    document.querySelectorAll('.transport-btn').forEach(btn => {
        btn.title = `${btn.textContent}去${poi.name}`;
    });

    // 隐藏旧的详情卡片
    document.getElementById('poi-detail-card').classList.add('hidden');
}

function hidePoiDetail() {
    document.getElementById('poi-detail-card').classList.add('hidden');
    document.getElementById('transport-btns').classList.add('hidden');
    selectedPoi = null;
}

// =============================================================================
// 路线预估
// =============================================================================
async function fetchRoutes(transportMode) {
    if (!selectedPoi || !gameUid) return;

    const modal = document.getElementById('route-modal');
    const optionsEl = document.getElementById('route-options');
    const titleEl = document.getElementById('route-title');

    // 交通方式中文标签映射
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

        // 点击路线确认出行
        optionsEl.querySelectorAll('.route-option').forEach(opt => {
            opt.addEventListener('click', () => {
                const idx = parseInt(opt.dataset.index);
                const chosen = routes[idx];
                modal.classList.add('hidden');
                // 重置计时器（因为即将发送消息，sendMessage 会计算时间）
                lastActivityTime = Date.now();
                // 自动发送出行消息
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

// =============================================================================
// 游戏结算
// =============================================================================
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

// =============================================================================
// 返回首页
// =============================================================================
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
    document.getElementById('poi-detail-card').classList.add('hidden');
    document.getElementById('transport-btns').classList.add('hidden');
    document.getElementById('route-modal').classList.add('hidden');
    showView('view-start');
    loadRecords(1);
}

// =============================================================================
// HTML 转义
// =============================================================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}