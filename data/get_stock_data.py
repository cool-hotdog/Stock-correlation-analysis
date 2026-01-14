"""get_stock_data.py

提供 Tushare 数据获取函数（建议被其他文件 import 调用）。

功能：
1) 输入股票代码，获取 2021-01-01~2025-12-31 的“日收益率”数据。
2) 自动获取沪深300成分股代码，并抓取每只成分股 2021-01-01~2025-12-31 的日收益率数据。
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import tushare as ts
import pandas as pd

# ==========================================
# 1. 设置 Tushare Token
# 请务必在这里填入你在 tushare.pro 注册后获取的 Token
# ==========================================
MY_TOKEN = 'your_token'

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

if __name__ == "__main__":
    # 演示：保留一个简单交互，但不影响被 import 使用
    code_input = input("请输入股票代码 (格式如 600519.SH 或 000001.SZ): ").strip()
    if not code_input:
        raise SystemExit(0)

    try:
        df = get_stock_return_daily(code_input)
        print(f"\n成功获取 {code_input} 的日收益率数据：{len(df)} 行")
        print(df.head())
    except Exception as e:
        print(f"获取失败：{e}")
