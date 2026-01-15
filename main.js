/**
 * Stock Correlation Analysis - 前端交互脚本
 * CS61A Project Style
 */

// ==========================================
// 全局配置
// ==========================================
const API_BASE_URL = '';  // 同源，无需前缀

// 示例股票代码（用于演示）
const SAMPLE_STOCKS = [
    '600519.SH', '000001.SZ', '000002.SZ', '600036.SH', '601318.SH',
    '000858.SZ', '600276.SH', '601166.SH', '000333.SZ', '600030.SH',
    '002415.SZ', '601888.SH', '600887.SH', '000651.SZ', '600900.SH',
    '601012.SH', '002594.SZ', '600809.SH', '000568.SZ', '601398.SH',
    '600000.SH', '601288.SH', '600690.SH', '000725.SZ', '601668.SH',
    '600028.SH', '601857.SH', '600048.SH', '000001.SH', '002304.SZ'
];

// ==========================================
// 工具函数
// ==========================================

/**
 * 显示 Toast 通知
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * 显示/隐藏 Loading
 */
function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

/**
 * 解释相关系数
 */
function interpretCorrelation(corr) {
    const absCorr = Math.abs(corr);
    let strength, direction;
    
    if (absCorr >= 0.8) strength = '非常强';
    else if (absCorr >= 0.6) strength = '强';
    else if (absCorr >= 0.4) strength = '中等';
    else if (absCorr >= 0.2) strength = '弱';
    else strength = '极弱或无';
    
    direction = corr >= 0 ? '正' : '负';
    
    return `${strength}${direction}相关`;
}

/**
 * 解析股票代码输入
 */
function parseStockCodes(input) {
    return input
        .split(/[\s,，]+/)
        .map(code => code.trim().toUpperCase())
        .filter(code => code.length > 0);
}

/**
 * 发起 API 请求
 */
async function apiRequest(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '请求失败');
    }
    
    return response.json();
}

// ==========================================
// Tab 切换逻辑
// ==========================================
function initTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');
    
    const titles = {
        'two-stocks': '两只股票相关性分析',
        'thirty-stocks': '30只股票相关性分析',
        'combined': '综合相关系数分析'
    };
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.dataset.tab;
            
            // 更新导航状态
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // 切换内容
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // 更新标题
            pageTitle.textContent = titles[tabId];
        });
    });
}

// ==========================================
// 功能1：两只股票相关性分析
// ==========================================
function initTwoStocksForm() {
    const form = document.getElementById('two-stocks-form');
    const resultCard = document.getElementById('two-stocks-result');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const stock1 = document.getElementById('stock1').value.trim().toUpperCase();
        const stock2 = document.getElementById('stock2').value.trim().toUpperCase();
        const startDate = document.getElementById('start-date-1').value.trim();
        const endDate = document.getElementById('end-date-1').value.trim();
        
        if (!stock1 || !stock2) {
            showToast('请输入两个股票代码', 'error');
            return;
        }
        
        showLoading(true);
        
        try {
            const result = await apiRequest('/api/correlation/two', {
                stock1,
                stock2,
                start_date: startDate,
                end_date: endDate
            });
            
            if (result.success) {
                const data = result.data;
                
                // 更新结果显示
                document.getElementById('result-correlation').textContent = data.pearson_correlation;
                document.getElementById('result-pvalue').textContent = data.p_value;
                document.getElementById('result-days').textContent = `${data.sample_days} 天`;
                document.getElementById('result-interpretation').textContent = 
                    interpretCorrelation(data.pearson_correlation);
                
                resultCard.classList.remove('hidden');
                showToast('分析完成！', 'success');
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            showToast(`分析失败: ${error.message}`, 'error');
            resultCard.classList.add('hidden');
        } finally {
            showLoading(false);
        }
    });
}

// ==========================================
// 功能2：30只股票分析（热力图 + Top5）
// ==========================================
function initThirtyStocksForm() {
    const form = document.getElementById('thirty-stocks-form');
    const resultCard = document.getElementById('thirty-stocks-result');
    const loadSampleBtn = document.getElementById('load-sample');
    
    // 加载示例股票
    loadSampleBtn.addEventListener('click', () => {
        document.getElementById('stock-codes').value = SAMPLE_STOCKS.join(' ');
        showToast('已加载30只示例股票', 'success');
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const codesInput = document.getElementById('stock-codes').value;
        const stockCodes = parseStockCodes(codesInput);
        const startDate = document.getElementById('start-date-2').value.trim();
        const endDate = document.getElementById('end-date-2').value.trim();
        
        if (stockCodes.length < 2) {
            showToast('请至少输入2个股票代码', 'error');
            return;
        }
        
        showLoading(true);
        
        try {
            const result = await apiRequest('/api/correlation/thirty', {
                stock_codes: stockCodes,
                start_date: startDate,
                end_date: endDate
            });
            
            if (result.success) {
                const data = result.data;
                
                // 渲染 Top5
                const top5Container = document.getElementById('top5-list');
                top5Container.innerHTML = data.top5_pairs.map((pair, index) => `
                    <div class="top5-item">
                        <div class="top5-rank">${index + 1}</div>
                        <div class="top5-stocks">
                            <div class="stock-pair">
                                <span class="stock-code">${pair.stock1}</span>
                                <span class="pair-arrow">↔</span>
                                <span class="stock-code">${pair.stock2}</span>
                            </div>
                        </div>
                        <div class="top5-correlation">${pair.correlation}</div>
                    </div>
                `).join('');
                
                // 显示热力图
                document.getElementById('heatmap-img').src = 
                    `data:image/png;base64,${data.heatmap}`;
                
                resultCard.classList.remove('hidden');
                showToast(`分析完成！成功获取 ${data.stock_count} 只股票数据`, 'success');
                
                // 显示警告（如果有获取失败的）
                if (data.errors && data.errors.length > 0) {
                    console.warn('部分股票获取失败:', data.errors);
                }
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            showToast(`分析失败: ${error.message}`, 'error');
            resultCard.classList.add('hidden');
        } finally {
            showLoading(false);
        }
    });
}

// ==========================================
// 功能3：综合相关系数分析
// ==========================================
function initCombinedForm() {
    const form = document.getElementById('combined-form');
    const resultCard = document.getElementById('combined-result');
    const loadSampleBtn = document.getElementById('load-sample-combined');
    
    // 加载示例股票
    loadSampleBtn.addEventListener('click', () => {
        document.getElementById('stock-codes-combined').value = SAMPLE_STOCKS.join(' ');
        showToast('已加载30只示例股票', 'success');
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const codesInput = document.getElementById('stock-codes-combined').value;
        const stockCodes = parseStockCodes(codesInput);
        const startDate = document.getElementById('start-date-3').value.trim();
        const endDate = document.getElementById('end-date-3').value.trim();
        
        if (stockCodes.length < 2) {
            showToast('请至少输入2个股票代码', 'error');
            return;
        }
        
        showLoading(true);
        
        try {
            const result = await apiRequest('/api/correlation/combined', {
                stock_codes: stockCodes,
                start_date: startDate,
                end_date: endDate
            });
            
            if (result.success) {
                const data = result.data;
                
                // 显示综合热力图
                document.getElementById('combined-heatmap-img').src = 
                    `data:image/png;base64,${data.heatmap}`;
                
                resultCard.classList.remove('hidden');
                showToast(`分析完成！成功获取 ${data.stock_count} 只股票数据`, 'success');
                
                // 显示警告（如果有获取失败的）
                if (data.errors && data.errors.length > 0) {
                    console.warn('部分股票获取失败:', data.errors);
                }
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            showToast(`分析失败: ${error.message}`, 'error');
            resultCard.classList.add('hidden');
        } finally {
            showLoading(false);
        }
    });
}

// ==========================================
// 初始化
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // 显示当前日期
    const currentDate = document.getElementById('current-date');
    const now = new Date();
    currentDate.textContent = now.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    });
    
    // 初始化各功能模块
    initTabNavigation();
    initTwoStocksForm();
    initThirtyStocksForm();
    initCombinedForm();
});
