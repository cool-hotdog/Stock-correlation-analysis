"""get_stock_data.py

提供 Tushare 数据获取函数（建议被其他文件 import 调用）。

功能：
1) 输入两个股票代码，分别获取 2021-01-01~2025-12-31 的“日收益率”数据（分开展示）。
2) 计算两只股票相同交易日收益率的皮尔逊相关系数，并单独用字典展示。
3) 自动获取沪深300成分股代码，并抓取每只成分股 2021-01-01~2025-12-31 的日收益率数据。
"""

from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

import tushare as ts
import pandas as pd
import scipy.stats as stats  # 用于计算皮尔逊相关系数

# ==========================================
# 1. 设置 Tushare Token
# 请务必在这里填入你在 tushare.pro 注册后获取的 Token
# ==========================================
MY_TOKEN = 'f13a323a345f13293426902aff556e099701b4e6725fc5e0b06b308b'


def _get_pro(token: Optional[str] = None):
    """获取 tushare pro 客户端。

    优先级：显式传入 token > 环境变量 TUSHARE_TOKEN > 文件内 MY_TOKEN。
    """
    real_token = token or os.getenv("TUSHARE_TOKEN") or MY_TOKEN
    if not real_token or real_token == '请在这里替换为你的Tushare_Token':
        raise ValueError("Tushare Token 未设置：请传入 token，或设置环境变量 TUSHARE_TOKEN，或修改 MY_TOKEN")

    ts.set_token(real_token)
    return ts.pro_api()


def get_stock_return_daily(
        ts_code: str,
        start_date: str = "20210101",
        end_date: str = "20251231",
        token: Optional[str] = None,
) -> pd.DataFrame:
    """获取单只股票在指定时间段内的“日收益率”数据。

    参数
    - ts_code: 股票代码，如 '600519.SH' 或 '000001.SZ'
    - start_date/end_date: 交易日期，格式 'YYYYMMDD'
    - token: 可选，Tushare Token（不传则使用环境变量/文件内 MY_TOKEN）

    返回
    - DataFrame（按 trade_date 升序），包含至少：trade_date, ts_code, close, pre_close, daily_return

    说明
    - daily_return 定义为： close / pre_close - 1
    """
    pro = _get_pro(token)

    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        raise ValueError(f"获取到的数据为空：{ts_code}，请检查代码是否带 .SH/.SZ 等后缀")

    # 按时间从早到晚
    df = df.sort_values(by="trade_date").reset_index(drop=True)

    # 计算日收益率：用 pre_close 更稳（避免自己 shift，且更符合复权前口径）
    if "pre_close" not in df.columns or "close" not in df.columns:
        raise ValueError("daily 接口返回字段缺失：需要 close 和 pre_close")

    df["daily_return"] = df["close"] / df["pre_close"] - 1

    # 输出字段做一个基础整理（保留原始字段也可以；这里偏向“被别人调用更清爽”）
    keep_cols = [c for c in ["trade_date", "ts_code", "close", "pre_close", "daily_return"] if c in df.columns]
    return df.loc[:, keep_cols]


def get_hs300_returns_daily(
        start_date: str = "20210101",
        end_date: str = "20251231",
        token: Optional[str] = None,
        as_concat: bool = True,
) -> pd.DataFrame | Dict[str, pd.DataFrame]:
    """获取沪深300全部成分股在指定时间段内的“日收益率”数据。

    参数
    - start_date/end_date: 交易日期，格式 'YYYYMMDD'
    - token: 可选，Tushare Token
    - as_concat:
        - True: 返回拼接后的 DataFrame（多股票纵向拼接，含 ts_code）
        - False: 返回 dict：{ts_code: DataFrame}

    返回
    - DataFrame 或 Dict[str, DataFrame]

    说明
    - 成分股用 index_weight 接口获取；不指定 trade_date 时，取最近一期权重。
    """
    pro = _get_pro(token)

    # 取最近一期沪深300成分
    weight_df = pro.index_weight(index_code="399300.SZ")
    if weight_df is None or weight_df.empty:
        raise ValueError("无法获取沪深300成分股：index_weight 返回为空")

    # 去重并保持一个稳定顺序
    codes = (
        weight_df.loc[:, "con_code"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    if not codes:
        raise ValueError("沪深300成分股列表为空")

    if not as_concat:
        out: Dict[str, pd.DataFrame] = {}
        for code in codes:
            out[code] = get_stock_return_daily(code, start_date=start_date, end_date=end_date, token=token)
        return out

    parts = []
    for code in codes:
        df = get_stock_return_daily(code, start_date=start_date, end_date=end_date, token=token)
        parts.append(df)

    # 纵向拼接：trade_date + ts_code 可作为联合键
    return pd.concat(parts, ignore_index=True)


def get_two_stocks_returns_daily(
        ts_code1: str,
        ts_code2: str,
        start_date: str = "20210101",
        end_date: str = "20251231",
        token: Optional[str] = None,
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