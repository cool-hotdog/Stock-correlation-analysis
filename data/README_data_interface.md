# 数据接口（get_stock_data.py）

面向项目其他模块的调用说明：给定股票代码或沪深300成分股，获取 **2021-01-01 ~ 2025-12-31** 的**日收益率**数据。

---

## 依赖

- Python 3
- `pandas`
- `tushare`

---

## Token 配置

Tushare Pro 必须配置 Token。优先级：

1. 函数参数 `token=...`
2. 环境变量 `TUSHARE_TOKEN`
3. `get_stock_data.py` 内的 `MY_TOKEN`

推荐使用环境变量：

```bash
export TUSHARE_TOKEN="你的token"
```

---

## 导入

```python
from get_stock_data import get_stock_return_daily, get_hs300_returns_daily
```

---

## API

### `get_stock_return_daily`

获取单只股票日收益率。

**签名**

```python
get_stock_return_daily(
    ts_code: str,
    start_date: str = "20210101",
    end_date: str = "20251231",
    token: Optional[str] = None,
) -> pandas.DataFrame
```

**参数**

- `ts_code`：股票代码（必须带后缀），如 `600519.SH` / `000001.SZ`
- `start_date`：起始日期，`YYYYMMDD`
- `end_date`：结束日期，`YYYYMMDD`
- `token`：可选，显式传入 Tushare Token

**输出**：`pandas.DataFrame`（按 `trade_date` 升序）

| 列名 | 类型 | 说明 |
|---|---|---|
| `trade_date` | str | 交易日期 `YYYYMMDD` |
| `ts_code` | str | 股票代码 |
| `close` | float | 收盘价 |
| `pre_close` | float | 昨收价 |
| `daily_return` | float | 日收益率：`close / pre_close - 1` |

**示例**

```python
df = get_stock_return_daily("600519.SH")
print(df.head())
```

---

### `get_hs300_returns_daily`

获取沪深300成分股的日收益率（拼接为一张长表）。

**签名**

```python
get_hs300_returns_daily(
    start_date: str = "20210101",
    end_date: str = "20251231",
    token: Optional[str] = None,
    as_concat: bool = True,
) -> pandas.DataFrame
```

**参数**

- `start_date`：起始日期，`YYYYMMDD`
- `end_date`：结束日期，`YYYYMMDD`
- `token`：可选，显式传入 Tushare Token

**输出**：`pandas.DataFrame`（长表，包含多只股票）

| 列名 | 类型 | 说明 |
|---|---|---|
| `trade_date` | str | 交易日期 `YYYYMMDD` |
| `ts_code` | str | 股票代码 |
| `close` | float | 收盘价 |
| `pre_close` | float | 昨收价 |
| `daily_return` | float | 日收益率 |

**示例**

```python
df_all = get_hs300_returns_daily()
print(df_all.head())
```

---

## 异常与注意事项

- Token 未设置/无效：抛出 `ValueError`
- `ts_code` 必须包含 `.SH` / `.SZ`，否则可能返回空数据并抛出 `ValueError`
- 沪深300全量抓取约 300 只股票，可能较慢且可能触发调用频率限制（建议先小样本验证流程）
