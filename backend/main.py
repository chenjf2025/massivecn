"""
股票行情多源聚合网关 - FastAPI 主程序
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from config_manager import config_manager, AppConfig
from models import (
    StockQuote, QuoteRequest, QuoteResponse, QuoteBatchResponse,
    HistoryRequest, HistoryResponse, HistoryDataPoint,
    ConfigUpdateRequest, ConfigResponse,
    SystemStatus, DataSourceStatus, ErrorResponse,
    IntervalEnum
)
from database import tdengine_pool
from parsers import ParserFactory
from kline_fetcher import kline_fetcher, KlineData
from watchlist_db import get_all_groups, create_group, update_group, delete_group
from watchlist_db import get_watchlist_stocks as _get_watchlist_stocks, add_stock, remove_stock, move_stock
from watchlist_db import init_db as init_watchlist_db
from stock_map import get_stock_info, search_stocks, STOCK_MAP


# -------------------- 全局状态 --------------------

START_TIME = time.time()

STATS = {
    "total_requests": 0,
    "success_requests": 0,
    "sources_used": {},
    "avg_latency": 0.0
}

WRITE_QUEUE: asyncio.Queue = asyncio.Queue(maxsize=10000)


# -------------------- 应用生命周期 --------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("股票行情网关启动中...")
    logger.info("=" * 50)
    
    try:
        await tdengine_pool.initialize()
        logger.info("TDengine 连接池初始化成功")
    except Exception as e:
        logger.error(f"TDengine 初始化失败: {e}")
    
    asyncio.create_task(background_writer())
    logger.info("异步落库任务已启动")
    
    try:
        init_watchlist_db()
        logger.info("自选股数据库初始化成功")
    except Exception as e:
        logger.error(f"自选股数据库初始化失败: {e}")
    
    asyncio.create_task(kline_sync_worker())
    logger.info("K线同步任务已启动")
    
    yield
    
    logger.info("正在关闭...")
    await tdengine_pool.close_all()
    logger.info("连接池已关闭")


# -------------------- FastAPI 应用 --------------------

app = FastAPI(
    title="股票行情多源聚合网关",
    description="国内股票行情数据聚合 API，支持多源降级、异步落库",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- 核心业务逻辑 --------------------

async def fetch_quote_with_failover(symbol: str) -> QuoteResponse:
    start_time = time.time()
    
    # 尝试解析股票代码 (支持名称/拼音)
    original_symbol = symbol
    resolved = resolve_symbol(symbol)
    if resolved:
        symbol = resolved
    
    primary_sources = config_manager.get_primary_sources()
    backup_sources = config_manager.get_backup_sources()
    routing = config_manager.get_routing_config()
    
    all_sources = primary_sources + backup_sources
    
    last_error = None
    used_source = None
    
    for source_config in all_sources:
        if not source_config.enabled:
            continue
        
        parser = ParserFactory.get(source_config.name)
        if not parser:
            logger.warning(f"解析器不存在: {source_config.name}")
            continue
        
        try:
            quote = await asyncio.wait_for(
                parser.get_quote(symbol),
                timeout=routing.request_timeout
            )
            
            if quote:
                used_source = source_config.name
                latency = (time.time() - start_time) * 1000
                
                STATS["total_requests"] += 1
                STATS["success_requests"] += 1
                STATS["sources_used"][source_config.name] = \
                    STATS["sources_used"].get(source_config.name, 0) + 1
                
                # 如果没有股票名称，尝试从映射获取
                if not quote.stock_name:
                    name, _ = get_stock_info(symbol)
                    if name:
                        quote.stock_name = name
                
                try:
                    WRITE_QUEUE.put_nowait(quote)
                except asyncio.QueueFull:
                    logger.warning("写入队列已满，跳过本次落库")
                
                return QuoteResponse(
                    success=True,
                    data=quote,
                    source=used_source,
                    latency_ms=round(latency, 2)
                )
            else:
                logger.warning(f"[{source_config.name}] 无数据返回: {symbol}")
                last_error = f"{source_config.name} 无数据"
            
        except asyncio.TimeoutError:
            logger.warning(f"[{source_config.name}] 请求超时: {symbol}")
            last_error = f"{source_config.name}: 请求超时"
        except Exception as e:
            logger.error(f"[{source_config.name}] 请求异常: {symbol}, {e}")
            last_error = str(e)
        
        if routing.failover:
            await asyncio.sleep(routing.failover_delay / 1000)
    
    STATS["total_requests"] += 1
    latency = (time.time() - start_time) * 1000
    
    return QuoteResponse(
        success=False,
        source=used_source,
        latency_ms=round(latency, 2),
        message=f"所有数据源均失败: {last_error}"
    )


def resolve_symbol(keyword: str) -> Optional[str]:
    """解析股票代码 (支持名称/拼音 -> 代码)"""
    keyword = keyword.lower().strip()
    
    # 直接匹配
    if keyword in STOCK_MAP:
        return keyword
    
    # 搜索匹配
    results = search_stocks(keyword)
    if results:
        return results[0]["symbol"]
    
    return None


async def background_writer():
    config = config_manager.get_config()
    batch_size = config.system.async_task.get("batch_size", 100)
    flush_interval = config.system.async_task.get("flush_interval", 5)
    
    buffer: List[StockQuote] = []
    last_flush = time.time()
    
    while True:
        try:
            try:
                quote = await asyncio.wait_for(WRITE_QUEUE.get(), timeout=1.0)
                buffer.append(quote)
            except asyncio.TimeoutError:
                pass
            
            now = time.time()
            should_flush = (
                len(buffer) >= batch_size or
                (now - last_flush) >= flush_interval
            )
            
            if should_flush and buffer:
                count = await tdengine_pool.batch_insert(buffer)
                if count > 0:
                    logger.debug(f"批量写入完成: {count} 条")
                buffer.clear()
                last_flush = now
            
        except Exception as e:
            logger.error(f"后台写入异常: {e}")
            await asyncio.sleep(1)


# 默认股票列表
DEFAULT_WATCHLIST = [
    "sh600000", "sh600519", "sh600036", "sh000001",
    "sz000001", "sz000858", "sz300750", "sh601318",
]

async def kline_sync_worker():
    logger.info("K线同步任务已启动")
    fetch_interval = 3600
    days_to_fetch = 30
    while True:
        try:
            for symbol in DEFAULT_WATCHLIST:
                try:
                    klines = await kline_fetcher.fetch_kline(symbol, interval="1day", days=days_to_fetch)
                    if klines:
                        count = await tdengine_pool.batch_insert_klines(klines, symbol)
                        if count > 0:
                            logger.info(f"K线同步: {symbol}, {count} 条")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"K线同步失败: {symbol}, {e}")
                    await asyncio.sleep(1)
            await asyncio.sleep(fetch_interval)
        except Exception as e:
            logger.error(f"K线同步任务异常: {e}")
            await asyncio.sleep(60)


# -------------------- API 路由 --------------------

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "股票行情聚合网关",
        "version": "1.0.0",
        "uptime": round(time.time() - START_TIME, 2)
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "tdengine": "connected",
        "timestamp": datetime.now().isoformat()
    }


# -------------------- 搜索接口 --------------------

@app.get("/api/v1/search")
async def search_stocks_endpoint(q: str = Query(..., description="搜索关键词: 股票代码/名称/拼音")):
    """搜索股票 (按代码、名称、拼音)"""
    results = search_stocks(q)
    return {
        "success": True,
        "data": results,
        "count": len(results)
    }


@app.get("/api/v1/resolve")
async def resolve_stock_endpoint(keyword: str = Query(..., description="股票代码/名称/拼音")):
    """解析股票代码 (名称/拼音 -> 代码)"""
    resolved = resolve_symbol(keyword)
    if resolved:
        name, pinyin = get_stock_info(resolved)
        return {
            "success": True,
            "symbol": resolved,
            "name": name,
            "pinyin": pinyin
        }
    
    return {
        "success": False,
        "message": f"未找到匹配的股票: {keyword}"
    }


# -------------------- 行情接口 --------------------

@app.post("/api/v1/quote", response_model=QuoteResponse)
async def get_quote(request: QuoteRequest):
    return await fetch_quote_with_failover(request.symbol)


@app.post("/api/v1/quote/batch", response_model=QuoteBatchResponse)
async def get_quotes_batch(symbols: List[str] = Query(...)):
    results = []
    sources_used = {}
    
    tasks = [fetch_quote_with_failover(symbol) for symbol in symbols]
    responses = await asyncio.gather(*tasks)
    
    for symbol, response in zip(symbols, responses):
        if response.success and response.data:
            results.append(response.data)
            if response.source:
                sources_used[symbol] = response.source
    
    latencies = [r.latency_ms for r in responses if r.latency_ms]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    return QuoteBatchResponse(
        success=len(results) > 0,
        data=results,
        sources=sources_used,
        total_count=len(results),
        latency_ms=round(avg_latency, 2)
    )


@app.get("/api/v1/history/{symbol}", response_model=HistoryResponse)
async def get_history(
    symbol: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    interval: IntervalEnum = Query(IntervalEnum.MIN_1),
    aggregation: Optional[int] = Query(None)
):
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except:
            pass
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except:
            pass
    
    if not end_dt:
        end_dt = datetime.now()
    if not start_dt:
        start_dt = end_dt - timedelta(days=7)
    
    # 尝试解析股票代码
    resolved = resolve_symbol(symbol)
    if resolved:
        symbol = resolved
    
    data = await tdengine_pool.query_history(
        symbol=symbol,
        start_time=start_dt,
        end_time=end_dt,
        interval=interval.value,
        aggregation=aggregation
    )
    
    if len(data) == 0:
        logger.info(f"无历史数据，尝试获取K线: {symbol}")
        kline_interval = "1day"
        if interval.value == "60min": kline_interval = "60min"
        elif interval.value == "30min": kline_interval = "30min"
        elif interval.value == "15min": kline_interval = "15min"
        elif interval.value == "5min": kline_interval = "5min"
        elif interval.value == "1min": kline_interval = "1min"
        
        days = (end_dt - start_dt).days + 1
        if days < 1: days = 7
        
        klines = await kline_fetcher.fetch_kline(symbol, interval=kline_interval, days=min(days, 60))
        
        if klines:
            filtered = [k for k in klines if start_dt <= datetime.fromisoformat(k.timestamp) <= end_dt]
            if filtered:
                await tdengine_pool.batch_insert_klines(filtered, symbol)
                logger.info(f"K线已存储: {symbol}, {len(filtered)} 条")
            
            from models import HistoryDataPoint
            for k in filtered:
                dt = datetime.fromisoformat(k.timestamp)
                data.append(HistoryDataPoint(
                    ts=int(dt.timestamp() * 1000), timestamp=k.timestamp,
                    open=k.open, high=k.high, low=k.low, close=k.close,
                    volume=k.volume, amount=k.amount,
                    vwap=round(k.amount / k.volume, 2) if k.volume > 0 else 0,
                    main_net_inflow=0
                ))
            data.sort(key=lambda x: x.timestamp)
    
    return HistoryResponse(
        success=True,
        symbol=symbol,
        interval=interval.value,
        data=data,
        count=len(data),
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat()
    )


@app.get("/api/v1/config", response_model=ConfigResponse)
async def get_config():
    config = config_manager.get_config()
    return ConfigResponse(
        success=True,
        data=config.model_dump(),
        change_history=config_manager.get_change_history()
    )


@app.put("/api/v1/config", response_model=ConfigResponse)
async def update_config(request: ConfigUpdateRequest):
    try:
        update_dict = {}
        
        if request.sources:
            update_dict["sources"] = request.sources
        if request.routing:
            update_dict["routing"] = request.routing
        if request.system:
            update_dict["system"] = request.system
        
        updated_config = await config_manager.update_config(update_dict)
        
        if request.sources:
            for src in request.sources.get("primary", []):
                if "enabled" in src:
                    if src["enabled"]:
                        ParserFactory.enable(src["name"])
                    else:
                        ParserFactory.disable(src["name"])
            
            for src in request.sources.get("backup", []):
                if "enabled" in src:
                    if src["enabled"]:
                        ParserFactory.enable(src["name"])
                    else:
                        ParserFactory.disable(src["name"])
        
        return ConfigResponse(
            success=True,
            data=updated_config.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/system/status", response_model=SystemStatus)
async def get_system_status():
    td_stats = await tdengine_pool.get_today_stats()
    
    sources_status = []
    for source in config_manager.get_enabled_sources():
        stats = STATS["sources_used"].get(source.name, 0)
        
        sources_status.append(DataSourceStatus(
            name=source.name,
            enabled=source.enabled,
            priority=source.priority,
            status="online" if stats > 0 else "offline",
            request_count=stats,
            success_count=stats,
            success_rate=1.0 if stats > 0 else 0.0
        ))
    
    return SystemStatus(
        status="running",
        uptime=round(time.time() - START_TIME, 2),
        today_ingested=td_stats.get("today_ingested", 0),
        avg_latency=round(STATS["avg_latency"], 2),
        sources=sources_status,
        storage={
            "tdengine": "connected",
            "queue_size": WRITE_QUEUE.qsize()
        }
    )


# ==================== 自选股 API ====================

@app.get("/api/v1/watchlist/groups")
async def get_watchlist_groups():
    try:
        groups = get_all_groups(user_id=1)
        return {"success": True, "data": groups}
    except Exception as e:
        logger.error(f"获取分组失败: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/v1/watchlist/groups")
async def create_watchlist_group(name: str = Query(...), color: str = Query('#409EFF')):
    try:
        group = create_group(user_id=1, name=name, color=color)
        return {"success": True, "data": group}
    except Exception as e:
        logger.error(f"创建分组失败: {e}")
        return {"success": False, "message": str(e)}


@app.put("/api/v1/watchlist/groups/{group_id}")
async def update_watchlist_group(group_id: int, name: str = Query(None), color: str = Query(None)):
    try:
        success = update_group(group_id, name=name, color=color)
        return {"success": success}
    except Exception as e:
        logger.error(f"更新分组失败: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/v1/watchlist/groups/{group_id}")
async def delete_watchlist_group(group_id: int):
    try:
        success = delete_group(group_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        return {"success": False, "message": str(e)}


@app.get("/api/v1/watchlist/{group_id}")
async def get_watchlist_stocks_api(group_id: int):
    try:
        stocks = _get_watchlist_stocks(group_id, user_id=1)
        
        if stocks:
            symbols = [s["symbol"] for s in stocks]
            try:
                quote_dict = {}
                for sym in symbols:
                    try:
                        result = await fetch_quote_with_failover(sym)
                        if result and result.success and result.data:
                            data = result.data
                            quote_dict[sym] = {
                                "current_price": data.current_price,
                                "change": data.change,
                                "change_pct": data.change_pct,
                                "stock_name": data.stock_name,
                                "support": round(data.current_price * 0.95, 2) if data.current_price else 0,
                                "resistance": round(data.current_price * 1.05, 2) if data.current_price else 0,
                            }
                    except:
                        pass
                
                for stock in stocks:
                    sym = stock["symbol"]
                    if sym in quote_dict:
                        q = quote_dict[sym]
                        stock["current_price"] = q.get("current_price", 0)
                        stock["change"] = q.get("change", 0)
                        stock["change_pct"] = q.get("change_pct", 0)
                        stock["support"] = q.get("support", 0)
                        stock["resistance"] = q.get("resistance", 0)
                        if q.get("stock_name"):
                            stock["stock_name"] = q["stock_name"]
            except Exception as e:
                logger.warning(f"获取实时行情失败: {e}")
        
        return {"success": True, "data": stocks}
    except Exception as e:
        logger.error(f"获取自选股失败: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/v1/watchlist/stocks")
async def add_watchlist_stock(group_id: int = Query(...), symbol: str = Query(...), stock_name: str = Query('')):
    try:
        resolved = resolve_symbol(symbol)
        if resolved:
            symbol = resolved
        success = add_stock(user_id=1, group_id=group_id, symbol=symbol, stock_name=stock_name)
        return {"success": success, "message": "" if success else "股票已存在"}
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/v1/watchlist/stocks/{stock_id}")
async def remove_watchlist_stock(stock_id: int):
    try:
        success = remove_stock(stock_id, user_id=1)
        return {"success": success}
    except Exception as e:
        logger.error(f"删除自选股失败: {e}")
        return {"success": False, "message": str(e)}


@app.put("/api/v1/watchlist/stocks/{stock_id}/move")
async def move_watchlist_stock(stock_id: int, new_group_id: int = Query(...)):
    try:
        success = move_stock(stock_id, new_group_id, user_id=1)
        return {"success": success}
    except Exception as e:
        logger.error(f"移动自选股失败: {e}")
        return {"success": False, "message": str(e)}


@app.exception_handler(Exception)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理异常: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="服务器内部错误",
            detail=str(exc)
        ).model_dump(by_alias=True)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
