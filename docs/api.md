# 股票行情多源聚合网关 API 文档

> 版本: 1.0.0 | 基础URL: http://localhost:8000

## 目录

- [概述](#概述)
- [实时行情](#实时行情)
- [批量行情](#批量行情)
- [历史K线](#历史k线)
- [配置管理](#配置管理)
- [系统状态](#系统状态)
- [Python 调用示例](#python-调用示例)

---

## 概述

本 API 提供国内股票实时行情、历史K线数据查询，支持多数据源自动降级。

### 数据源

| 数据源 | 状态 | 说明 |
|--------|------|------|
| eastmoney | 主源 | 东方财富 (推荐) |
| tencent | 备源 | 腾讯财经 |
| sina | 备源 | 新浪财经 |
| xueqiu | 备源 | 雪球财经 (需启用) |

### 股票代码格式

- 上海A股: `sh600000`, `600000`
- 深圳A股: `sz000001`, `000001`

---

## 实时行情

获取单只股票实时行情 (带自动降级)

### 请求

```http
POST /api/v1/quote
Content-Type: application/json
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 股票代码，如 `sh600000` |
| interval | string | 否 | 行情周期，默认 `1min` |

### 响应

```json
{
  "success": true,
  "data": {
    "ts": 1772384982315,
    "timestamp": "2026-03-02T01:09:42.315554",
    "symbol": "sh600000",
    "dataSource": "tencent",
    "currentPrice": 9.72,
    "openPrice": 9.73,
    "highPrice": 9.84,
    "lowPrice": 9.7,
    "closePrice": 9.72,
    "prevClose": 9.73,
    "change": -0.01,
    "changePct": -0.1,
    "tradingVolume": 802810.0,
    "tradingAmount": 331625.0,
    "bidPrice1": 9.72,
    "bidVolume1": 471185.0,
    "askPrice1": 9.73,
    "askVolume1": 6729.0,
    "mainNetInflow": 2525.0,
    "turnoverRate": 0.0024,
    "amplitude": 1.44
  },
  "source": "tencent",
  "latency_ms": 466.61
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| currentPrice | float | 当前价格 |
| openPrice | float | 开盘价 |
| highPrice | float | 最高价 |
| lowPrice | float | 最低价 |
| closePrice | float | 收盘价 |
| prevClose | float | 昨收价 |
| change | float | 涨跌额 |
| changePct | float | 涨跌幅(%) |
| tradingVolume | float | 成交量 |
| tradingAmount | float | 成交额 |
| bidPrice1~5 | float | 买一~买五价 |
| bidVolume1~5 | float | 买一~买五量 |
| askPrice1~5 | float | 卖一~卖五价 |
| askVolume1~5 | float | 卖一~卖五量 |
| mainNetInflow | float | 主力净流入 |
| turnoverRate | float | 换手率 |
| amplitude | float | 振幅 |

---

## 批量行情

批量获取多只股票实时行情

### 请求

```http
POST /api/v1/quote/batch?symbols=sh600000&symbols=sh601318
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbols | string[] | 是 | 股票代码列表 (query参数) |

### 响应

```json
{
  "success": true,
  "data": [...],
  "sources": {
    "sh600000": "tencent",
    "sh601318": "eastmoney"
  },
  "totalCount": 2,
  "latency_ms": 523.45
}
```

---

## 历史K线

获取历史K线数据

### 请求

```http
GET /api/v1/history/{symbol}?interval=5min&start_time=2026-01-01T00:00:00&end_time=2026-02-01T00:00:00&aggregation=5
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 股票代码 |
| interval | string | 否 | 时间周期: `1min`, `5min`, `15min`, `30min`, `60min`, `1day` |
| start_time | string | 否 | 开始时间 (ISO格式) |
| end_time | string | 否 | 结束时间 (ISO格式) |
| aggregation | int | 否 | 聚合窗口(分钟) |

### 响应

```json
{
  "success": true,
  "symbol": "sh600000",
  "interval": "5min",
  "data": [
    {
      "ts": 1772384400000,
      "timestamp": "2026-03-02T01:00:00",
      "open": 9.72,
      "high": 9.73,
      "low": 9.71,
      "close": 9.72,
      "volume": 156000.0,
      "amount": 1518720.0,
      "vwap": 9.72,
      "mainNetInflow": -32500.0
    }
  ],
  "count": 100,
  "startTime": "2026-01-26T00:00:00",
  "endTime": "2026-03-02T01:00:00"
}
```

---

## 配置管理

获取当前配置

### 请求

```http
GET /api/v1/config
```

### 响应

```json
{
  "success": true,
  "data": {
    "sources": {
      "primary": [
        {"name": "eastmoney", "enabled": true, "priority": 1}
      ],
      "backup": [
        {"name": "tencent", "enabled": true, "priority": 1}
      ]
    },
    "routing": {
      "failover": true,
      "requestTimeout": 5.0
    }
  }
}
```

### 更新配置

```http
PUT /api/v1/config
Content-Type: application/json
```

```json
{
  "sources": {
    "primary": [
      {"name": "eastmoney", "enabled": true}
    ]
  }
}
```

---

## 系统状态

获取系统运行状态

### 请求

```http
GET /api/v1/system/status
```

### 响应

```json
{
  "status": "running",
  "uptime": 3600.0,
  "todayIngested": 15230,
  "avgLatency": 245.5,
  "sources": [
    {
      "name": "tencent",
      "enabled": true,
      "priority": 1,
      "status": "online",
      "requestCount": 500,
      "successRate": 0.95
    }
  ],
  "storage": {
    "tdengine": "connected",
    "queueSize": 10
  }
}
```

---

## Python 调用示例

### 安装依赖

```bash
pip install requests httpx aiohttp
```

### 1. 获取实时行情 (同步)

```python
import requests

API_BASE = "http://localhost:8000"

def get_quote(symbol: str) -> dict:
    """获取股票实时行情"""
    response = requests.post(
        f"{API_BASE}/api/v1/quote",
        json={"symbol": symbol}
    )
    result = response.json()
    
    if result["success"]:
        data = result["data"]
        print(f"股票: {data['symbol']}")
        print(f"当前价: {data['currentPrice']}")
        print(f"涨跌: {data['change']} ({data['changePct']}%)")
        print(f"数据源: {result['source']}")
        print(f"延迟: {result['latency_ms']}ms")
    else:
        print(f"获取失败: {result['message']}")
    
    return result

# 调用示例
get_quote("sh600000")  # 浦发银行
get_quote("sh601318")  # 中国平安
get_quote("sz000001")  # 平安银行
```

### 2. 获取实时行情 (异步)

```python
import asyncio
import httpx

API_BASE = "http://localhost:8000"

async def get_quote_async(symbol: str) -> dict:
    """异步获取股票实时行情"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{API_BASE}/api/v1/quote",
            json={"symbol": symbol}
        )
        return response.json()

async def get_quotes_batch(symbols: list) -> dict:
    """批量获取多只股票行情"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 方法1: 使用批量接口
        params = [("symbols", s) for s in symbols]
        response = await client.post(
            f"{API_BASE}/api/v1/quote/batch",
            params=params
        )
        return response.json()

async def main():
    # 单只股票
    result = await get_quote_async("sh600000")
    print(result)
    
    # 批量查询
    symbols = ["sh600000", "sh601318", "sz000001"]
    results = await get_quotes_batch(symbols)
    print(f"成功获取 {results['totalCount']} 只股票")

asyncio.run(main())
```

### 3. 获取历史K线

```python
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def get_history(
    symbol: str,
    interval: str = "5min",
    days: int = 7,
    aggregation: int = None
) -> dict:
    """获取历史K线数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    
    if aggregation:
        params["aggregation"] = aggregation
    
    response = requests.get(
        f"{API_BASE}/api/v1/history/{symbol}",
        params=params
    )
    return response.json()

# 调用示例
result = get_history("sh600000", interval="5min", days=7, aggregation=5)

if result["success"]:
    print(f"获取 {result['count']} 条K线数据")
    for kline in result["data"][:5]:
        print(f"{kline['timestamp']}: "
              f"O={kline['open']} H={kline['high']} "
              f"L={kline['low']} C={kline['close']}")
```

### 4. 配置管理

```python
import requests

API_BASE = "http://localhost:8000"

def get_config() -> dict:
    """获取当前配置"""
    response = requests.get(f"{API_BASE}/api/v1/config")
    return response.json()

def update_sources(enabled_sources: dict) -> dict:
    """更新数据源配置"""
    response = requests.put(
        f"{API_BASE}/api/v1/config",
        json={"sources": enabled_sources}
    )
    return response.json()

# 查看当前配置
config = get_config()
print(config["data"]["sources"])

# 禁用腾讯数据源，只用东方财富
update_sources({
    "primary": [
        {"name": "eastmoney", "enabled": True}
    ],
    "backup": [
        {"name": "tencent", "enabled": False},
        {"name": "sina", "enabled": True}
    ]
})
```

### 5. 系统状态监控

```python
import requests
import time

API_BASE = "http://localhost:8000"

def get_system_status() -> dict:
    """获取系统状态"""
    response = requests.get(f"{API_BASE}/api/v1/system/status")
    return response.json()

def monitor_system(interval: int = 60):
    """持续监控系统状态"""
    while True:
        status = get_system_status()
        
        print("=" * 50)
        print(f"系统状态: {status['status']}")
        print(f"运行时间: {status['uptime']:.0f}s")
        print(f"今日入库: {status['todayIngested']} 条")
        print(f"平均延迟: {status['avgLatency']}ms")
        print("\n数据源:")
        
        for src in status["sources"]:
            print(f"  - {src['name']}: "
                  f"{src['status']} "
                  f"(请求: {src['requestCount']}, "
                  f"成功率: {src['successRate']*100:.1f}%)")
        
        print("=" * 50)
        time.sleep(interval)

# 启动监控 (每60秒打印一次)
# monitor_system(60)
```

### 6. 完整示例: 自动选股监控

```python
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000"

class StockMonitor:
    """股票实时监控"""
    
    def __init__(self, symbols: list):
        self.symbols = symbols
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_quotes(self) -> dict:
        """批量获取行情"""
        params = [("symbols", s) for s in self.symbols]
        response = await self.client.post(
            f"{API_BASE}/api/v1/quote/batch",
            params=params
        )
        return response.json()
    
    async def filter_by_change(self, min_change: float = 3.0) -> list:
        """筛选涨跌幅大于某值的股票"""
        result = await self.get_quotes()
        
        filtered = []
        for quote in result["data"]:
            if quote["changePct"] >= min_change:
                filtered.append({
                    "symbol": quote["symbol"],
                    "price": quote["currentPrice"],
                    "change": quote["change"],
                    "changePct": quote["changePct"],
                    "volume": quote["tradingVolume"],
                    "source": result["sources"].get(quote["symbol"])
                })
        
        return filtered
    
    async def close(self):
        await self.client.aclose()

async def main():
    # 监控的股票列表
    symbols = [
        "sh600000",  # 浦发银行
        "sh601318",  # 中国平安
        "sh600036",  # 招商银行
        "sh600519",  # 贵州茅台
        "sz000001",  # 平安银行
    ]
    
    monitor = StockMonitor(symbols)
    
    try:
        # 获取所有行情
        result = await monitor.get_quotes()
        print(f"成功获取 {result['totalCount']} 只股票\n")
        
        # 打印所有股票
        for quote in result["data"]:
            print(f"{quote['symbol']}: "
                  f"{quote['currentPrice']:.2f} "
                  f"{quote['change']:+.2f} ({quote['changePct']:+.2f}%)")
        
        # 筛选涨幅大于3%的
        print("\n涨幅 > 3%:")
        filtered = await monitor.filter_by_change(min_change=3.0)
        for stock in filtered:
            print(f"  {stock['symbol']}: {stock['changePct']:.2f}%")
    
    finally:
        await monitor.close()

asyncio.run(main())
```

### 7. 错误处理

```python
import requests
from requests.exceptions import RequestException

API_BASE = "http://localhost:8000"

def safe_get_quote(symbol: str) -> dict:
    """带错误处理的行情获取"""
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/quote",
            json={"symbol": symbol},
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not result["success"]:
            return {
                "error": True,
                "message": result.get("message", "未知错误"),
                "symbol": symbol
            }
        
        return {
            "error": False,
            "data": result["data"]
        }
    
    except RequestException as e:
        return {
            "error": True,
            "message": f"网络错误: {str(e)}",
            "symbol": symbol
        }

# 使用
result = safe_get_quote("sh600000")

if result["error"]:
    print(f"错误: {result['message']}")
else:
    print(f"价格: {result['data']['currentPrice']}")
```

---

## 注意事项

1. **频率限制**: 建议每次请求间隔 >= 1秒
2. **数据源**: Docker 容器内可能无法访问部分数据源 (网络限制)
3. **历史数据**: 需要 TDengine 数据库中有数据
4. **错误处理**: 生产环境请务必添加重试和错误处理逻辑

---

## 文档版本

- v1.0.0 (2026-03-02) - 初始版本
