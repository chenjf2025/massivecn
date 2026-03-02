# Pydantic 数据模型
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class IntervalEnum(str, Enum):
    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    MIN_60 = "60min"
    DAILY = "1day"


class StockQuote(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        serialize_by_alias=True,
    )
    
    # Internal storage (snake_case)
    ts: int
    timestamp: str
    symbol: str
    stock_name: str = Field(default="", serialization_alias="stockName")
    data_source: str = Field(serialization_alias="dataSource")
    ts: int
    timestamp: str
    symbol: str
    data_source: str = Field(serialization_alias="dataSource")
    
    # Price fields - serialized as camelCase
    current_price: float = Field(serialization_alias="currentPrice")
    open_price: float = Field(serialization_alias="openPrice")
    high_price: float = Field(serialization_alias="highPrice")
    low_price: float = Field(serialization_alias="lowPrice")
    close_price: float = Field(serialization_alias="closePrice")
    prev_close: float = Field(serialization_alias="prevClose")
    
    change: float = Field(serialization_alias="change")
    change_pct: float = Field(serialization_alias="changePct")
    
    trading_volume: float = Field(serialization_alias="tradingVolume")
    trading_amount: float = Field(serialization_alias="tradingAmount")
    
    # Bid/Ask fields
    bid_price1: Optional[float] = Field(default=None, serialization_alias="bidPrice1")
    bid_volume1: Optional[float] = Field(default=None, serialization_alias="bidVolume1")
    bid_price2: Optional[float] = Field(default=None, serialization_alias="bidPrice2")
    bid_volume2: Optional[float] = Field(default=None, serialization_alias="bidVolume2")
    bid_price3: Optional[float] = Field(default=None, serialization_alias="bidPrice3")
    bid_volume3: Optional[float] = Field(default=None, serialization_alias="bidVolume3")
    bid_price4: Optional[float] = Field(default=None, serialization_alias="bidPrice4")
    bid_volume4: Optional[float] = Field(default=None, serialization_alias="bidVolume4")
    bid_price5: Optional[float] = Field(default=None, serialization_alias="bidPrice5")
    bid_volume5: Optional[float] = Field(default=None, serialization_alias="bidVolume5")
    
    ask_price1: Optional[float] = Field(default=None, serialization_alias="askPrice1")
    ask_volume1: Optional[float] = Field(default=None, serialization_alias="askVolume1")
    ask_price2: Optional[float] = Field(default=None, serialization_alias="askPrice2")
    ask_volume2: Optional[float] = Field(default=None, serialization_alias="askVolume2")
    ask_price3: Optional[float] = Field(default=None, serialization_alias="askPrice3")
    ask_volume3: Optional[float] = Field(default=None, serialization_alias="askVolume3")
    ask_price4: Optional[float] = Field(default=None, serialization_alias="askPrice4")
    ask_volume4: Optional[float] = Field(default=None, serialization_alias="askVolume4")
    ask_price5: Optional[float] = Field(default=None, serialization_alias="askPrice5")
    ask_volume5: Optional[float] = Field(default=None, serialization_alias="askVolume5")
    
    # Capital flow
    main_net_inflow: float = Field(default=0, serialization_alias="mainNetInflow")
    large_net_inflow: float = Field(default=0, serialization_alias="largeNetInflow")
    medium_net_inflow: float = Field(default=0, serialization_alias="mediumNetInflow")
    small_net_inflow: float = Field(default=0, serialization_alias="smallNetInflow")
    
    # Additional metrics
    turnover_rate: Optional[float] = Field(default=None, serialization_alias="turnoverRate")
    amplitude: Optional[float] = Field(default=None, serialization_alias="amplitude")
    market_cap: Optional[float] = Field(default=None, serialization_alias="marketCap")
    circulating_cap: Optional[float] = Field(default=None, serialization_alias="circulatingCap")


class QuoteRequest(BaseModel):
    symbol: str
    interval: IntervalEnum = IntervalEnum.MIN_1


class HistoryRequest(BaseModel):
    symbol: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    interval: IntervalEnum = IntervalEnum.MIN_1
    aggregation: Optional[int] = None


class QuoteResponse(BaseModel):
    success: bool
    data: Optional[StockQuote] = None
    source: Optional[str] = None
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class QuoteBatchResponse(BaseModel):
    success: bool
    data: List[StockQuote]
    sources: Dict[str, str]
    total_count: int
    latency_ms: float


class HistoryDataPoint(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)
    
    ts: int
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    vwap: Optional[float] = Field(default=None, serialization_alias="vwap")
    main_net_inflow: Optional[float] = Field(default=None, serialization_alias="mainNetInflow")


class HistoryResponse(BaseModel):
    success: bool
    symbol: str
    interval: str
    data: List[HistoryDataPoint]
    count: int
    start_time: str
    end_time: str


class SourceConfig(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 1
    base_url: str = ""
    timeout: float = 3.0
    retry: int = 2
    parser: str = ""


class SourcesConfig(BaseModel):
    primary: List[SourceConfig] = Field(default_factory=list)
    backup: List[SourceConfig] = Field(default_factory=list)


class RoutingConfig(BaseModel):
    failover: bool = True
    request_timeout: float = 5.0
    max_retries: int = 2
    failover_delay: int = 100


class TDengineConfig(BaseModel):
    host: str = "localhost"
    port: int = 6030
    user: str = "root"
    password: str = "taosdata"
    database: str = "market_data"
    pool_size: int = 5
    timeout: int = 30


class SystemConfig(BaseModel):
    api: Dict[str, Any] = Field(default_factory=dict)
    async_task: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    tdengine: TDengineConfig = Field(default_factory=TDengineConfig)
    frontend: Dict[str, Any] = Field(default_factory=dict)
    monitoring: Dict[str, Any] = Field(default_factory=dict)


class ConfigUpdateRequest(BaseModel):
    sources: Optional[Dict[str, Any]] = None
    routing: Optional[Dict[str, Any]] = None
    system: Optional[Dict[str, Any]] = None


class ConfigResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    last_modified: Optional[str] = None
    change_history: List[Dict[str, Any]] = Field(default_factory=list)


class DataSourceStatus(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)
    
    name: str
    enabled: bool
    priority: int
    status: str
    latency_ms: Optional[float] = Field(default=None, serialization_alias="latencyMs")
    last_success: Optional[str] = Field(default=None, serialization_alias="lastSuccess")
    request_count: int = Field(default=0, serialization_alias="requestCount")
    success_count: int = Field(default=0, serialization_alias="successCount")
    success_rate: float = Field(default=0.0, serialization_alias="successRate")


class SystemStatus(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)
    
    status: str
    uptime: float
    today_ingested: int = Field(serialization_alias="todayIngested")
    avg_latency: float = Field(serialization_alias="avgLatency")
    sources: List[DataSourceStatus]
    storage: Dict[str, Any]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: Optional[str] = Field(default=None, serialization_alias="errorCode")
    detail: Optional[str] = None
