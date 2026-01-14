"""app.py - 股票相关性分析 Web 服务端

Flask 后端，提供以下 API：
1. POST /api/correlation/two - 两只股票相关性分析
2. POST /api/correlation/thirty - 30只股票相关性矩阵、热力图、Top5
3. POST /api/correlation/combined - 30只股票综合相关系数（Pearson + Spearman）
"""

from __future__ import annotations

import sys
import os
import io
import base64
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非GUI后端，用于服务器
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats

from data.get_stock_data import get_stock_return_daily

# ==========================================
# Flask 应用初始化
# ==========================================
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # 允许跨域请求

# ==========================================
# 工具函数
# ==========================================
def setup_matplotlib_font():
    """设置 matplotlib 中文字体"""
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 8
    font_candidates = [
        "PingFang SC", "Heiti SC", "Songti SC",  # Mac
        "SimHei", "Microsoft YaHei",              # Windows
        "WenQuanYi Micro Hei",                    # Linux
        "DejaVu Sans"
    ]
    import matplotlib.font_manager as fm
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    for font in font_candidates:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            return
    plt.rcParams["font.family"] = "DejaVu Sans"

setup_matplotlib_font()


def get_stock_data_dict(stock_codes: List[str], start_date: str, end_date: str):
    """批量获取股票数据，返回 (数据字典, 错误列表)"""
    stock_data_dict: Dict[str, pd.DataFrame] = {}
    errors: List[str] = []
    for code in stock_codes:
        try:
            df = get_stock_return_daily(code, start_date, end_date)
            stock_data_dict[code] = df
        except Exception as e:
            errors.append(f"{code}: {str(e)}")
    return stock_data_dict, errors


def build_correlation_matrix(stock_data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """构建相关性矩阵"""
    return_series_dict = {}
    for code, df in stock_data_dict.items():
        return_series = df.set_index("trade_date")["daily_return"]
        return_series.name = code
        return_series_dict[code] = return_series
    return_df = pd.DataFrame(return_series_dict).fillna(0)
    return return_df.corr()


def generate_heatmap_base64(corr_matrix: pd.DataFrame) -> str:
    """生成热力图并返回 Base64 编码"""
    n = len(corr_matrix)
    figsize = (max(10, n * 0.6), max(8, n * 0.5))
    
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        corr_matrix,
        ax=ax,
        annot=True,
        annot_kws={"size": max(6, 12 - n // 5), "weight": "bold"},
        cmap="RdYlGn_r",
        vmin=-1, vmax=1, center=0,
        linewidths=0.2, linecolor="white",
        cbar_kws={"shrink": 0.8, "label": "皮尔逊相关系数"},
        fmt=".2f"
    )
    ax.set_title("股票收益率相关性矩阵热力图", fontsize=14, pad=15, weight="bold")
    ax.set_xlabel("股票代码", fontsize=10)
    ax.set_ylabel("股票代码", fontsize=10)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    # 转换为 Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def get_top_pairs(corr_matrix: pd.DataFrame, top_n: int = 5) -> List[Dict]:
    """获取相关性最高的股票对"""
    corr_upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    corr_pairs = corr_upper.stack().reset_index()
    corr_pairs.columns = ["stock1", "stock2", "correlation"]
    corr_pairs = corr_pairs.dropna().sort_values(by="correlation", ascending=False)
    
    return [
        {"stock1": row["stock1"], "stock2": row["stock2"], "correlation": round(row["correlation"], 4)}
        for _, row in corr_pairs.head(top_n).iterrows()
    ]


def calculate_combined_correlation(stock_data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """计算综合相关系数（Pearson + Spearman 平均）"""
    return_series_dict = {}
    for code, df in stock_data_dict.items():
        return_series = df.set_index("trade_date")["daily_return"]
        return_series_dict[code] = return_series
    
    return_df = pd.DataFrame(return_series_dict).fillna(0)
    
    # Pearson 和 Spearman 相关矩阵
    pearson_matrix = return_df.corr(method='pearson')
    spearman_matrix = return_df.corr(method='spearman')
    
    # 综合相关矩阵（取平均）
    combined_matrix = (pearson_matrix + spearman_matrix) / 2
    
    return {
        "pearson": pearson_matrix.round(4).to_dict(),
        "spearman": spearman_matrix.round(4).to_dict(),
        "combined": combined_matrix.round(4).to_dict()
    }


# ==========================================
# API 路由
# ==========================================
@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/correlation/two', methods=['POST'])
def correlation_two_stocks():
    """两只股票相关性分析 API"""
    try:
        data = request.get_json()
        stock1 = data.get('stock1', '').strip()
        stock2 = data.get('stock2', '').strip()
        start_date = data.get('start_date', '20210101')
        end_date = data.get('end_date', '20251231')

        if not stock1 or not stock2:
            return jsonify({"success": False, "error": "请输入两个股票代码"}), 400

        # 获取数据
        df1 = get_stock_return_daily(stock1, start_date, end_date)
        df2 = get_stock_return_daily(stock2, start_date, end_date)

        # 对齐交易日
        df1 = df1.set_index("trade_date")
        df2 = df2.set_index("trade_date")
        merged = pd.merge(
            df1[["daily_return"]].rename(columns={"daily_return": "return1"}),
            df2[["daily_return"]].rename(columns={"daily_return": "return2"}),
            left_index=True, right_index=True, how="inner"
        )

        if merged.empty:
            return jsonify({"success": False, "error": "两只股票无相同交易日数据"}), 400

        # 计算 Pearson 相关系数
        corr, p_value = stats.pearsonr(merged["return1"], merged["return2"])

        return jsonify({
            "success": True,
            "data": {
                "stock1": stock1,
                "stock2": stock2,
                "pearson_correlation": round(float(corr), 4),
                "p_value": round(float(p_value), 6),
                "sample_days": len(merged),
                "start_date": start_date,
                "end_date": end_date
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/correlation/thirty', methods=['POST'])
def correlation_thirty_stocks():
    """30只股票相关性分析 API（矩阵 + 热力图 + Top5）"""
    try:
        data = request.get_json()
        stock_codes = data.get('stock_codes', [])
        start_date = data.get('start_date', '20250101')
        end_date = data.get('end_date', '20251231')

        if not stock_codes:
            return jsonify({"success": False, "error": "请输入股票代码列表"}), 400

        # 获取数据
        stock_data_dict, errors = get_stock_data_dict(stock_codes, start_date, end_date)
        
        if not stock_data_dict:
            return jsonify({"success": False, "error": "所有股票获取失败", "details": errors}), 400

        # 构建相关性矩阵
        corr_matrix = build_correlation_matrix(stock_data_dict)
        
        # 生成热力图
        heatmap_base64 = generate_heatmap_base64(corr_matrix)
        
        # 获取 Top5
        top_pairs = get_top_pairs(corr_matrix, 5)

        return jsonify({
            "success": True,
            "data": {
                "stock_count": len(stock_data_dict),
                "correlation_matrix": corr_matrix.round(4).to_dict(),
                "heatmap": heatmap_base64,
                "top5_pairs": top_pairs,
                "errors": errors if errors else None
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/correlation/combined', methods=['POST'])
def correlation_combined():
    """综合相关系数分析 API（Pearson + Spearman）"""
    try:
        data = request.get_json()
        stock_codes = data.get('stock_codes', [])
        start_date = data.get('start_date', '20250101')
        end_date = data.get('end_date', '20251231')

        if not stock_codes:
            return jsonify({"success": False, "error": "请输入股票代码列表"}), 400

        # 获取数据
        stock_data_dict, errors = get_stock_data_dict(stock_codes, start_date, end_date)
        
        if not stock_data_dict:
            return jsonify({"success": False, "error": "所有股票获取失败", "details": errors}), 400

        # 计算综合相关系数
        result = calculate_combined_correlation(stock_data_dict)
        
        # 生成综合矩阵热力图
        combined_df = pd.DataFrame(result["combined"])
        heatmap_base64 = generate_heatmap_base64(combined_df)

        return jsonify({
            "success": True,
            "data": {
                "stock_count": len(stock_data_dict),
                "pearson_matrix": result["pearson"],
                "spearman_matrix": result["spearman"],
                "combined_matrix": result["combined"],
                "heatmap": heatmap_base64,
                "errors": errors if errors else None
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# 启动服务
# ==========================================
if __name__ == '__main__':
    print("=" * 50)
    print("📈 股票相关性分析 Web 服务")
    print("=" * 50)
    print("访问地址: http://localhost:5001")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
