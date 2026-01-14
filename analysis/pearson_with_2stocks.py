"""stock_data_analysis.py

演示：
1) 输入两个股票代码，分别获取指定区间的“日收益率”数据（分开展示）。
2) 计算两只股票相同交易日收益率的皮尔逊相关系数，并用字典展示。

说明
- 数据获取能力统一来自 `data/get_stock_data.py`，本文件不再复制粘贴请求/口径逻辑。
"""

from __future__ import annotations

from typing import Dict

import pandas as pd
import scipy.stats as stats  # 用于计算皮尔逊相关系数

# 统一复用 data/get_stock_data.py 的数据获取逻辑
from data.get_stock_data import get_stock_return_daily

def get_two_stocks_returns_daily(
        ts_code1: str,
        ts_code2: str,
        start_date: str = "20210101",
        end_date: str = "20251231",
        token: str | None = None,
) -> Dict[str, pd.DataFrame]:
    """获取两只股票在指定时间段内的日收益率数据（分开返回，不复用拼接逻辑）。

    参数
    - ts_code1/ts_code2: 两只股票的代码，如 '600519.SH'、'000001.SZ'
    - start_date/end_date: 交易日期，格式 'YYYYMMDD'
    - token: 可选，Tushare Token

    返回
    - Dict[str, pd.DataFrame]：{股票代码: 对应数据}
    """
    # 复用原有单股票获取函数，保证计算逻辑完全一致
    stock1_df = get_stock_return_daily(ts_code1, start_date, end_date, token)
    stock2_df = get_stock_return_daily(ts_code2, start_date, end_date, token)

    # 仅返回字典格式，完全去掉拼接逻辑
    return {ts_code1: stock1_df, ts_code2: stock2_df}


def calculate_returns_correlation(
        ts_code1: str,
        ts_code2: str,
        stock_data_dict: Dict[str, pd.DataFrame],
) -> Dict[str, float]:
    """计算两只股票相同交易日收益率的皮尔逊相关系数。

    参数
    - ts_code1/ts_code2: 两只股票的代码
    - stock_data_dict: 包含两只股票数据的字典（来自 get_two_stocks_returns_daily）

    返回
    - Dict[str, float]：专属字典，包含相关系数及关键信息
    """
    # 提取两只股票的数据
    df1 = stock_data_dict[ts_code1].copy()
    df2 = stock_data_dict[ts_code2].copy()

    # 将trade_date设为索引，方便对齐交易日
    df1 = df1.set_index("trade_date")
    df2 = df2.set_index("trade_date")

    # 只保留相同交易日的数据（内连接）
    merged_df = pd.merge(
        df1[["daily_return"]].rename(columns={"daily_return": f"{ts_code1}_return"}),
        df2[["daily_return"]].rename(columns={"daily_return": f"{ts_code2}_return"}),
        left_index=True,
        right_index=True,
        how="inner"
    )

    if merged_df.empty:
        raise ValueError(f"两只股票 {ts_code1} 和 {ts_code2} 无相同交易日数据，无法计算相关系数")

    # 计算皮尔逊相关系数
    corr_coef, p_value = stats.pearsonr(
        merged_df[f"{ts_code1}_return"],
        merged_df[f"{ts_code2}_return"]
    )

    # 构建专属字典返回，包含核心信息
    correlation_dict = {
        "stock1_code": ts_code1,
        "stock2_code": ts_code2,
        "pearson_correlation": round(corr_coef, 4),  # 保留4位小数，更易读
        "p_value": round(p_value, 6),  # p值（显著性）
        "common_trading_days": len(merged_df)  # 相同交易日数量
    }

    return correlation_dict


if __name__ == "__main__":
    # 演示：输入两只股票代码，获取数据+计算相关系数
    print("请输入两只股票代码（格式如 600519.SH 000001.SZ，用空格分隔）：")
    code_input = input().strip()

    # 分割输入的两个代码
    code_list = code_input.split()
    if len(code_list) != 2:
        print("输入格式错误！请输入两个股票代码，用空格分隔（例如：600519.SH 000001.SZ）")
        raise SystemExit(1)

    code1, code2 = code_list[0], code_list[1]

    try:
        # 1. 获取两只股票的日收益率数据（分开存储）
        stock_data_dict = get_two_stocks_returns_daily(code1, code2)

        # 2. 分别展示每只股票的数据
        print(f"\n===== {code1} 日收益率数据（共 {len(stock_data_dict[code1])} 行） =====")
        print(stock_data_dict[code1].head())

        print(f"\n===== {code2} 日收益率数据（共 {len(stock_data_dict[code2])} 行） =====")
        print(stock_data_dict[code2].head())

        # 3. 计算并展示皮尔逊相关系数（专属字典）
        corr_dict = calculate_returns_correlation(code1, code2, stock_data_dict)
        print("\n===== 两只股票收益率皮尔逊相关系数 =====")
        for key, value in corr_dict.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"执行失败：{e}")
