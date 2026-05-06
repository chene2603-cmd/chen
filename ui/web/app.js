// OpenOracle Web 前端交互逻辑

const API_BASE = 'http://localhost:8000/api/v1';
let walletAddress = null;
let predictionHistory = [];

// ==================== 标签切换 ====================
function switchTab(tabName) {
    // 隐藏所有标签
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    
    // 显示选中的标签
    document.getElementById(`tab-${tabName}`).classList.add('active');
    document.querySelector(`.nav-btn[onclick="switchTab('${tabName}')"]`).classList.add('active');
    
    // 加载对应数据
    if (tabName === 'leaderboard') loadLeaderboard();
    if (tabName === 'history') renderHistory();
    if (tabName === 'governance') loadProposals();
}

// ==================== 角色计数 ====================
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('questionInput');
    const counter = document.getElementById('charCount');
    
    if (input && counter) {
        input.addEventListener('input', () => {
            counter.textContent = input.value.length;
        });
    }
});

// ==================== 钱包连接 ====================
async function connectWallet() {
    if (typeof window.ethereum !== 'undefined') {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            walletAddress = accounts[0];
            document.getElementById('walletAddress').textContent = 
                `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}`;
            document.getElementById('connectWalletBtn').textContent = '✅ 已连接';
            localStorage.setItem('walletAddress', walletAddress);
        } catch (error) {
            console.error('连接钱包失败:', error);
            alert('无法连接钱包，请检查MetaMask是否安装并授权。');
        }
    } else {
        alert('请安装MetaMask钱包扩展。');
    }
}

// 页面加载时尝试恢复钱包连接
window.addEventListener('load', () => {
    const saved = localStorage.getItem('walletAddress');
    if (saved) walletAddress = saved;
});

// ==================== 提交问题 ====================
async function submitQuestion() {
    const question = document.getElementById('questionInput').value.trim();
    if (!question) {
        alert('请输入预测问题');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('loadingSpinner');
    const result = document.getElementById('predictionResult');
    
    // 显示加载状态
    submitBtn.disabled = true;
    spinner.classList.remove('hidden');
    result.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, source: 'user_submitted' })
        });
        
        const data = await response.json();
        
        if (data.status === 'APPROVED') {
            renderPrediction(data.prediction);
            // 加入历史记录
            predictionHistory.unshift({
                question,
                prediction: data.prediction,
                timestamp: new Date().toISOString()
            });
            saveHistory();
        } else {
            alert(`预测被拒绝: ${data.message}`);
        }
    } catch (error) {
        console.error('请求失败:', error);
        alert('请求失败，请确认后端服务已启动。');
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
    }
}

// ==================== 渲染预测结果 ====================
function renderPrediction(prediction) {
    const result = document.getElementById('predictionResult');
    result.classList.remove('hidden');
    
    // 状态标签
    const statusEl = document.getElementById('predictionStatus');
    statusEl.textContent = '已批准';
    statusEl.className = 'badge approved';
    
    // 概率
    const prob = prediction.calibrated_probability || prediction.probability;
    document.getElementById('probValue').textContent = `${(prob * 100).toFixed(1)}%`;
    
    // 概率条
    document.getElementById('probBar').style.width = `${prob * 100}%`;
    
    // 置信区间
    document.getElementById('confidenceInterval').textContent = 
        `${(prediction.confidence_interval[0] * 100).toFixed(0)}% - ${(prediction.confidence_interval[1] * 100).toFixed(0)}%`;
    
    // 不确定性
    document.getElementById('uncertainty').textContent = 
        `${(prediction.uncertainty * 100).toFixed(1)}%`;
    
    // 推理
    document.getElementById('reasoningText').textContent = prediction.reasoning;
    
    // 智能体列表（模拟数据）
    const agentsHTML = [
        { name: '证据提取', prob: prob + 0.05 },
        { name: '历史类比', prob: prob - 0.03 },
        { name: '因果链', prob: prob + 0.02 },
        { name: '反事实', prob: prob - 0.01 },
        { name: '不确定性量化', prob: prob }
    ].map(a => `
        <div class="agent-card">
            <div class="agent-name">${a.name}</div>
            <div class="agent-prob">${(a.prob * 100).toFixed(0)}%</div>
        </div>
    `).join('');
    document.getElementById('agentsList').innerHTML = agentsHTML;
    
    // 证据链
    if (prediction.evidence_chain) {
        const nodes = prediction.evidence_chain.nodes || [];
        document.getElementById('evidenceChain').innerHTML = nodes.map(n => `
            <div style="padding:8px;margin:4px 0;background:var(--bg-input);border-radius:4px;">
                <strong>📄 ${n.id}</strong>: ${n.content}<br>
                <small>来源: ${n.source} | 可靠性: ${(n.reliability_score * 100).toFixed(0)}%</small>
            </div>
        `).join('');
    }
    
    // 社区校准
    if (prediction.calibration) {
        document.getElementById('calibrationInfo').innerHTML = `
            校准后概率: ${(prediction.calibrated_probability * 100).toFixed(1)}% |
            校准因子: ${prediction.calibration.calibration_factor} |
            反馈数: ${prediction.calibration.feedback_count}
        `;
    }
    
    // 滚动到结果
    result.scrollIntoView({ behavior: 'smooth' });
}

// ==================== 清空输入 ====================
function clearInput() {
    document.getElementById('questionInput').value = '';
    document.getElementById('charCount').textContent = '0';
    document.getElementById('predictionResult').classList.add('hidden');
}

// ==================== 历史记录 ====================
function saveHistory() {
    localStorage.setItem('predictionHistory', JSON.stringify(predictionHistory.slice(0, 50)));
}

function loadHistory() {
    const saved = localStorage.getItem('predictionHistory');
    if (saved) predictionHistory = JSON.parse(saved);
}

function renderHistory() {
    const container = document.getElementById('historyList');
    if (predictionHistory.length === 0) {
        container.innerHTML = '<p class="empty-state">暂无预测记录</p>';
        return;
    }
    
    container.innerHTML = predictionHistory.map((h, i) => `
        <div style="padding:12px;border-bottom:1px solid var(--border);cursor:pointer;" 
             onclick="document.getElementById('questionInput').value='${h.question}';switchTab('predict');">
            <strong>Q:</strong> ${h.question}<br>
            <small style="color:var(--text-muted)">
                概率: ${((h.prediction.calibrated_probability || h.prediction.probability) * 100).toFixed(0)}% | 
                时间: ${new Date(h.timestamp).toLocaleString()}
            </small>
        </div>
    `).join('');
}

// ==================== 排行榜 ====================
async function loadLeaderboard() {
    // 模拟数据
    const mockData = [
        { rank: 1, address: '0x1234...5678', brier: 0.02, count: 45 },
        { rank: 2, address: '0xabcd...ef01', brier: 0.05, count: 32 },
        { rank: 3, address: '0x9876...5432', brier: 0.08, count: 28 },
    ];
    
    document.getElementById('leaderboardBody').innerHTML = mockData.map(d => `
        <tr>
            <td>#${d.rank}</td>
            <td>${d.address}</td>
            <td>${d.brier.toFixed(4)}</td>
            <td>${d.count}</td>
        </tr>
    `).join('');
}

// ==================== 治理 ====================
function switchGovTab(tab) {
    document.querySelectorAll('.gov-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.gov-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.gov-tab[onclick="switchGovTab('${tab}')"]`).classList.add('active');
    document.getElementById(`gov-${tab}`).classList.add('active');
}

async function loadProposals() {
    // 模拟提案数据
    document.getElementById('proposalsList').innerHTML = `
        <div style="padding:16px;border:1px solid var(--border);border-radius:8px;margin-bottom:10px;">
            <h4>PROP-001: 增加新的预测智能体</h4>
            <p style="color:var(--text-muted)">状态: 投票中 | 通过率: 72%</p>
        </div>
    `;
}

async function createProposal() {
    const title = document.getElementById('proposalTitle').value.trim();
    const desc = document.getElementById('proposalDesc').value.trim();
    if (!title || !desc) {
        alert('请填写完整信息');
        return;
    }
    alert('提案已提交（开发环境，实际将调用链上合约）');
}

// ==================== 辅助功能 ====================
function sharePrediction() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => alert('链接已复制'));
}

function submitFeedback() {
    const feedback = prompt('请输入你的反馈：');
    if (feedback) alert('感谢你的反馈！（开发环境，实际将提交到社区校准回路）');
}

function verifyOnChain() {
    alert('正在跳转到区块链浏览器验证...（开发环境模拟）');
}

// 页面加载初始化
window.addEventListener('load', () => {
    loadHistory();
    renderHistory();
});