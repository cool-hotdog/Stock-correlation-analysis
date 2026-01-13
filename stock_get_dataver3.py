"""get_stock_data.py

提供 Tushare 数据获取函数（建议被其他文件 import 调用）。

功能：
1) 输入30支股票代码，获取 2025-01-01~2025-12-31 的日收益率数据。
2) 计算所有两两组合的皮尔逊相关系数，输出相关性最高的5组股票对。
3) 生成带数值标注的相关性矩阵热力图并保存为图片，解决字体警告问题。
"""

from __future__ import annotations

import os
import itertools
import numpy as np
from typing import Dict, Optional, List, Tuple

import tushare as ts
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================
# 1. 修复字体问题（兼容Windows/Mac/Linux）
# ==========================================
def setup_matplotlib_font():
    """设置matplotlib字体，解决中文乱码和字体缺失警告"""
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
    plt.rcParams["font.size"] = 8  # 基础字体大小，适配30支股票的标注

    # 按系统优先级设置字体（避免指定不存在的字体）
    font_candidates = [
        # Windows 常见中文字体
        "SimHei", "Microsoft YaHei", "SimSun", "FangSong",
        # Mac 常见中文字体
        "PingFang SC", "Heiti SC", "Songti SC",
        # Linux 常见中文字体
        "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
        # 兜底字体
        "DejaVu Sans"
    ]

    # 自动检测可用字体
    import matplotlib.font_manager as fm
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    for font in font_candidates:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            print(f"✅ 已设置字体：{font}")
            return

    # 如果都没找到，使用默认字体（仅警告，不影响运行）
    print("⚠️ 未找到中文字体，可能出现中文乱码，但不影响数值显示")


# 初始化字体设置
setup_matplotlib_font()

# ==========================================
# 2. Tushare Token 设置
# ==========================================
MY_TOKEN = 'f13a323a345f13293426902aff556e099701b4e6725fc5e0b06b308b'


def _get_pro(token: Optional[str] = None):
    """获取 tushare pro 客户端。"""
    real_token = token or os.getenv("TUSHARE_TOKEN") or MY_TOKEN
    if not real_token or real_token == '请在这里替换为你的Tushare_Token':
        raise ValueError("Tushare Token 未设置：请传入 token，或设置环境变量 TUSHARE_TOKEN，或修改 MY_TOKEN")

    ts.set_token(real_token)
    return ts.pro_api()


def get_stock_return_daily(
        ts_code: str,
        start_date: str = "20250101",
        end_date: str = "20251231",
        token: Optional[str] = None,
) -> pd.DataFrame:
    """获取单只股票在2025年的日收益率数据。"""
    pro = _get_pro(token)

    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        raise ValueError(f"获取到的数据为空：{ts_code}，请检查代码是否带 .SH/.SZ 等后缀")

    df = df.sort_values(by="trade_date").reset_index(drop=True)

    if "pre_close" not in df.columns or "close" not in df.columns:
        raise ValueError("daily 接口返回字段缺失：需要 close 和 pre_close")

    df["daily_return"] = df["close"] / df["pre_close"] - 1

    keep_cols = [c for c in ["trade_date", "ts_code", "close", "pre_close", "daily_return"] if c in df.columns]
    return df.loc[:, keep_cols]


def get_multi_stocks_returns_daily(
        stock_codes: List[str],
        start_date: str = "20250101",
        end_date: str = "20251231",
        token: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """获取多只股票2025年的日收益率数据（支持30支）。"""
    stock_data_dict = {}
    for code in stock_codes:
        try:
            df = get_stock_return_daily(code, start_date, end_date, token)
            stock_data_dict[code] = df
            print(f"✅ 成功获取 {code} 数据（{len(df)} 行）")
        except Exception as e:
            print(f"❌ 获取 {code} 数据失败：{e}")

    if not stock_data_dict:
        raise ValueError("所有股票代码均获取数据失败，请检查代码格式")

    return stock_data_dict


def build_correlation_matrix(
        stock_data_dict: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """构建股票池的相关性矩阵（用于热力图）。"""
    return_series_dict = {}
    for code, df in stock_data_dict.items():
        return_series = df.set_index("trade_date")["daily_return"]
        return_series.name = code
        return_series_dict[code] = return_series

    return_df = pd.DataFrame(return_series_dict).fillna(0)
    corr_matrix = return_df.corr()

    return corr_matrix


def plot_correlation_heatmap(
        corr_matrix: pd.DataFrame,
        save_path: str = "stock_correlation_heatmap.png",
        figsize: Tuple[int, int] = (20, 18),  # 放大尺寸适配30支股票+数值标注
        cmap: str = "RdYlGn_r"
):
    """生成带数值标注的相关性矩阵热力图（解决字体问题）。

    参数
    - corr_matrix: 相关性矩阵
    - save_path: 图片保存路径
    - figsize: 图片尺寸（30支股票建议20×18）
    - cmap: 颜色映射（高相关红色，低相关绿色）
    """
    # 创建画布
    fig, ax = plt.subplots(figsize=figsize)

    # 绘制热力图（开启数值标注）
    sns.heatmap(
        corr_matrix,
        ax=ax,
        annot=True,  # 显示数值标注（核心修改）
        annot_kws={
            "size": 6,  # 标注字体大小（适配30支股票）
            "weight": "bold"
        },
        cmap=cmap,
        vmin=-1,
        vmax=1,
        center=0,
        linewidths=0.2,
        linecolor="white",  # 格子边框白色，更清晰
        cbar_kws={
            "shrink": 0.8,
            "label": "皮尔逊相关系数（关联度）",
            "orientation": "vertical"
        },
        fmt=".2f"  # 数值保留2位小数，更简洁
    )

    # 设置标题和标签
    ax.set_title(
        "30支股票收益率相关性矩阵热力图（2025年）",
        fontsize=16,
        pad=20,
        weight="bold"
    )
    ax.set_xlabel("股票代码", fontsize=12, weight="bold")
    ax.set_ylabel("股票代码", fontsize=12, weight="bold")

    # 优化标签显示（旋转+对齐）
    plt.xticks(
        rotation=45,
        ha="right",
        rotation_mode="anchor"  # 旋转锚点，避免标签偏移
    )
    plt.yticks(rotation=0)

    # 调整布局（关键：防止数值标注被截断）
    plt.tight_layout()

    # 高分辨率保存
    plt.savefig(
        save_path,
        dpi=300,
        bbox_inches="tight",  # 自动裁剪空白
        facecolor="white"  # 背景白色，避免透明
    )
    plt.close()

    print(f"\n✅ 带数值标注的热力图已保存至：{os.path.abspath(save_path)}")


def get_top_correlation_pairs(
        corr_matrix: pd.DataFrame,
        top_n: int = 5
) -> List[Tuple[str, str, float]]:
    """从相关性矩阵中提取相关性最高的N组股票对（去重）。"""
    # 提取上三角矩阵（排除对角线和重复对）
    corr_matrix_upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    # 转换为长格式并排序
    corr_pairs = corr_matrix_upper.stack().reset_index()
    corr_pairs.columns = ["stock1", "stock2", "correlation"]
    corr_pairs = corr_pairs.dropna()
    corr_pairs = corr_pairs.sort_values(by="correlation", ascending=False)

    # 取前top_n组
    top_pairs = []
    for _, row in corr_pairs.head(top_n).iterrows():
        top_pairs.append(
            (row["stock1"], row["stock2"], round(row["correlation"], 4))
        )

    return top_pairs


if __name__ == "__main__":
    # 演示：30支股票池分析+带数值标注的热力图
    print("===== 30支股票池相关性分析（2025年）+ 带数值热力图 =====")
    print("请输入30个股票代码（格式如 600519.SH 000001.SZ ...，用空格分隔）：")
    code_input = input().strip()

    stock_codes = [code.strip() for code in code_input.split() if code.strip()]

    if len(stock_codes) != 30:
        print(f"⚠️ 输入的股票代码数量为 {len(stock_codes)}，不是30个！是否继续分析？(y/n)")
        confirm = input().strip().lower()
        if confirm != 'y':
            raise SystemExit("用户取消分析")

    try:
        # 1. 获取数据
        print("\n开始获取2025年股票收益率数据...")
        stock_data_dict = get_multi_stocks_returns_daily(stock_codes)

        # 2. 构建相关性矩阵
        print("\n开始构建相关性矩阵...")
        corr_matrix = build_correlation_matrix(stock_data_dict)

        # 3. 生成带数值的热力图
        print("\n开始生成带数值标注的热力图...")
        plot_correlation_heatmap(corr_matrix)

        # 4. 输出TOP5
        print("\n===== 相关性最高的5组股票对（2025年） =====")
        top_pairs = get_top_correlation_pairs(corr_matrix, top_n=5)
        for idx, (code1, code2, corr) in enumerate(top_pairs, 1):
            print(f"第{idx}名：{code1} ↔ {code2} | 皮尔逊相关系数：{corr}")

    except Exception as e:
        print(f"\n❌ 分析失败：{e}")
        import traceback

        traceback.print_exc()