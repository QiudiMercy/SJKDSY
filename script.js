function updateChatTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const timeString = `${hours}:${minutes}`;
    const chatTimeElement = document.getElementById('chat-time');
    if (chatTimeElement) {
        chatTimeElement.textContent = timeString;
    }
}

// 当DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        updateChatTime();
        setInterval(updateChatTime, 1000);
    });
} else {
    updateChatTime();
    setInterval(updateChatTime, 1000);
}

// 聊天功能
function initChat() {
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.querySelector('.chat-messages');

    // 发送消息函数
    function sendMessage() {
        const messageText = messageInput.value.trim();
        if (messageText) {
            // 创建用户消息元素
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = `
                <div class="message-avatar">
                    <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20simple%20design&image_size=square" alt="用户头像">
                </div>
                <div class="message-content">
                    <p>${messageText}</p>
                </div>
            `;
            
            // 添加到聊天消息容器
            chatMessages.appendChild(messageElement);
            
            // 清空输入框
            messageInput.value = '';
            
            // 滚动到最新消息
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // 发送按钮点击事件
    sendBtn.addEventListener('click', sendMessage);
    
    // 输入框回车键事件
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// 初始化聊天功能
window.addEventListener('DOMContentLoaded', initChat);

// 全局变量
let map;

// 初始化百度地图
function initBaiduMap() {
    // 创建地图实例
    map = new BMap.Map("map");
    // 设置成都市中心点坐标
    const point = new BMap.Point(104.0668, 30.6598);
    // 初始化地图，设置中心点和缩放级别
    map.centerAndZoom(point, 15);
    // 添加缩放控件
    map.addControl(new BMap.NavigationControl());
    // 添加比例尺控件
    map.addControl(new BMap.ScaleControl());
    // 添加地图类型控件
    map.addControl(new BMap.MapTypeControl());
    // 启用滚轮缩放
    map.enableScrollWheelZoom(true);
    // 添加成都市标记
    const marker = new BMap.Marker(point);
    map.addOverlay(marker);
    // 添加信息窗口
    const infoWindow = new BMap.InfoWindow("成都市中心", {
        width: 100,
        height: 50,
        title: "天府广场"
    });
    marker.addEventListener("click", function() {
        this.openInfoWindow(infoWindow);
    });
}

// 页面加载完成后初始化地图
window.addEventListener('DOMContentLoaded', initBaiduMap);

// 初始化搜索功能
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    
    // 搜索按钮点击事件
    searchBtn.addEventListener('click', function() {
        const keyword = searchInput.value.trim();
        if (keyword) {
            searchPlace(keyword);
        }
    });
    
    // 输入框回车键事件
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const keyword = searchInput.value.trim();
            if (keyword) {
                searchPlace(keyword);
            }
        }
    });
}

// 搜索地点
function searchPlace(keyword) {
    // 清除地图上的标记
    map.clearOverlays();
    
    // 创建本地搜索实例
    const local = new BMap.LocalSearch(map, {
        renderOptions: {
            map: map,
            autoViewport: true,
            selectFirstResult: true
        }
    });
    
    // 执行搜索
    local.search(keyword);
}

// 页面加载完成后初始化搜索功能
window.addEventListener('DOMContentLoaded', initSearch);
