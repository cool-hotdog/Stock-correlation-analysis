# 📈 股票相关性分析 Web 应用

## 项目简介

这是一个基于 Flask 的股票相关性分析 Web 应用，通过 Tushare API 获取股票数据，计算股票间的相关性系数，并以可视化方式展示结果。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🔢 两只股票相关性 | 输入两只股票代码，计算皮尔逊相关系数、P值及显著性解读 |
| 🔥 30只股票分析 | 输入多只股票，生成相关性矩阵热力图 + Top5 最相关股票对 |
| 🧮 综合相关系数 | 同时计算 Pearson 和 Spearman 相关系数，输出综合分析结果 |

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip 包管理器
- 有效的 Tushare Token（[注册获取](https://tushare.pro/register?reg=7)）

### 2. 安装依赖

```bash
# 进入 web 目录
cd /Users/james/Downloads/Stock-correlation-analysis-main/web

# 安装 Python 依赖
pip3 install -r requirements.txt
```

### 3. 配置 Tushare Token

在 `data/get_stock_data.py` 中配置你的 Token：

```python
MY_TOKEN = '你的Tushare_Token'
```

或设置环境变量：

```bash
export TUSHARE_TOKEN='你的Tushare_Token'
```

### 4. 启动服务

```bash
# 方式1：直接运行
cd /Users/james/Downloads/Stock-correlation-analysis-main/web
python3 app.py

# 方式2：使用启动脚本
./run.sh
```

### 5. 访问应用

启动成功后，在浏览器中访问：

```
http://localhost:5001
```

---

## 📖 使用指南

### 功能1：两只股票相关性分析

1. 点击左侧导航 **"📊 两股票相关性"**
2. 输入两只股票代码（格式如 `600519.SH`、`000001.SZ`）
3. 设置日期范围（默认 2021-01-01 至 2025-12-31）
4. 点击 **"开始分析"**
5. 查看结果：
   - **皮尔逊相关系数**：-1 到 1 之间，越接近 1 表示正相关越强
   - **P值**：< 0.05 表示统计显著
   - **相关性解读**：自动判断相关强度

### 功能2：30只股票分析

1. 点击左侧导航 **"🔥 30股票分析"**
2. 在文本框中输入多只股票代码（用空格或逗号分隔）
   - 或点击 **"加载示例股票"** 快速填充 30 只示例股票
3. 设置日期范围
4. 点击 **"生成热力图分析"**
5. 查看结果：
   - **Top5 相关股票对**：相关性最高的 5 组股票
   - **热力图**：所有股票间的相关性矩阵可视化

### 功能3：综合相关系数分析

1. 点击左侧导航 **"🧮 综合相关系数"**
2. 输入股票代码列表
3. 点击 **"计算综合系数"**
4. 查看结果：
   - **Pearson 相关系数**：衡量线性相关
   - **Spearman 相关系数**：衡量单调相关（抗异常值）
   - **综合系数**：两者平均值

---

## 📁 项目结构（CS61A Style）

```
Stock-correlation-analysis-main/
│
├── analysis/                        # 分析模块（核心算法）
│   ├── pearson_with_2stocks.py      # 两股票 Pearson 相关性
│   ├── pearson_with_30stocks.py     # 多股票相关性 + 热力图
│   └── pearson_and_spearman.py      # Pearson + Spearman 综合分析
│
├── data/                            # 数据模块
│   ├── get_stock_data.py            # Tushare 数据获取接口
│   └── README_data_interface.md     # 数据接口文档
│
├── web/                             # Web 应用（本目录）
│   ├── app.py                       # Flask 后端服务（API）
│   ├── requirements.txt             # Python 依赖清单
│   ├── run.sh                       # 一键启动脚本
│   ├── README.md                    # 本文件
│   └── static/                      # 前端静态资源
│       ├── index.html               # 主页面
│       ├── css/
│       │   └── style.css            # 样式表
│       └── js/
│           └── main.js              # 前端交互逻辑
│
└── __pycache__/                     # Python 缓存（可忽略）
```

---

## 🔌 API 接口文档

### 1. 两只股票相关性

**POST** `/api/correlation/two`

**请求体：**
```json
{
    "stock1": "600519.SH",
    "stock2": "000001.SZ",
    "start_date": "20210101",
    "end_date": "20251231"
}
```

**响应：**
```json
{
    "success": true,
    "data": {
        "stock1": "600519.SH",
        "stock2": "000001.SZ",
        "pearson_correlation": 0.3245,
        "p_value": 0.000012,
        "sample_days": 1000,
        "start_date": "20210101",
        "end_date": "20251231"
    }
}
```

### 2. 多股票分析（热力图 + Top5）

**POST** `/api/correlation/thirty`

**请求体：**
```json
{
    "stock_codes": ["600519.SH", "000001.SZ", "000002.SZ", ...],
    "start_date": "20250101",
    "end_date": "20251231"
}
```

**响应：**
```json
{
    "success": true,
    "data": {
        "stock_count": 30,
        "correlation_matrix": {...},
        "heatmap": "<base64_encoded_png>",
        "top5_pairs": [
            {"stock1": "600519.SH", "stock2": "000858.SZ", "correlation": 0.9523},
            ...
        ],
        "errors": null
    }
}
```

### 3. 综合相关系数

**POST** `/api/correlation/combined`

**请求体：**
```json
{
    "stock_codes": ["600519.SH", "000001.SZ", ...],
    "start_date": "20250101",
    "end_date": "20251231"
}
```

**响应：**
```json
{
    "success": true,
    "data": {
        "stock_count": 30,
        "pearson_matrix": {...},
        "spearman_matrix": {...},
        "combined_matrix": {...},
        "heatmap": "<base64_encoded_png>",
        "errors": null
    }
}
```

---

## 🛠 常见问题

### Q1: 端口 5000 被占用怎么办？

macOS 上端口 5000 通常被 AirPlay Receiver 占用。解决方案：

**方案1：** 使用其他端口（已默认改为 5001）

**方案2：** 关闭 AirPlay Receiver
- 打开 **系统设置** → **通用** → **隔空播放与接力**
- 关闭 **隔空播放接收器**

### Q2: 提示 `command not found: python`

macOS 默认使用 `python3`，请使用：

```bash
python3 app.py
```

### Q3: 提示缺少依赖包

```bash
pip3 install -r requirements.txt
```

### Q4: Tushare 获取数据失败

1. 检查 Token 是否有效
2. 检查股票代码格式是否正确（需带后缀 `.SH` 或 `.SZ`）
3. Tushare 免费账户有频率限制，稍后重试

---

## 📊 股票代码格式说明

| 市场 | 格式 | 示例 |
|------|------|------|
| 上海证券交易所 | `代码.SH` | `600519.SH`（贵州茅台） |
| 深圳证券交易所 | `代码.SZ` | `000001.SZ`（平安银行） |

### 常用示例股票

```
600519.SH  贵州茅台    000001.SZ  平安银行
000858.SZ  五粮液      601318.SH  中国平安
600036.SH  招商银行    000333.SZ  美的集团
002415.SZ  海康威视    600276.SH  恒瑞医药
```

---

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask |
| 数据处理 | Pandas, NumPy |
| 统计计算 | SciPy |
| 可视化 | Matplotlib, Seaborn |
| 数据源 | Tushare API |
| 前端 | HTML5, CSS3, JavaScript |

---

## 📜 许可证

MIT License

---

## 👨‍💻 作者

PKU经济学院 梁舜哲
PKU外国语学院 罗苏梦 郑家祺
