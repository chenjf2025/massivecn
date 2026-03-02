// API 服务层
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

// -------------------- 行情接口 --------------------

// 获取实时行情
export async function getQuote(symbol) {
  const response = await api.post('/api/v1/quote', { symbol })
  return response.data
}

// 批量获取行情
export async function getQuotesBatch(symbols) {
  const response = await api.post('/api/v1/quote/batch', null, {
    params: { symbols }
  })
  return response.data
}

// 获取历史数据
export async function getHistory(symbol, options = {}) {
  const params = { symbol, ...options }
  const response = await api.get(`/api/v1/history/${symbol}`, { params })
  return response.data
}

// -------------------- 配置接口 --------------------

// 获取配置
export async function getConfig() {
  const response = await api.get('/api/v1/config')
  return response.data
}

// 更新配置
export async function updateConfig(config) {
  const response = await api.put('/api/v1/config', config)
  return response.data
}

// -------------------- 系统接口 --------------------

// 获取系统状态
export async function getSystemStatus() {
  const response = await api.get('/api/v1/system/status')
  return response.data
}

// 健康检查
export async function healthCheck() {
  const response = await api.get('/health')
  return response.data
}

// 搜索股票
export async function searchStocks(keyword) {
  const response = await api.get('/api/v1/search', { params: { q: keyword } })
  return response.data
}

// 解析股票代码 (名称/拼音 -> 代码)
export async function resolveStock(keyword) {
  const response = await api.get('/api/v1/resolve', { params: { keyword } })
  return response.data
}

// -------------------- 自选股接口 --------------------

// 获取自选分组
export async function getWatchlistGroups() {
  const response = await api.get('/api/v1/watchlist/groups')
  return response.data
}

// 创建分组
export async function createWatchlistGroup(name, color = '#409EFF') {
  const response = await api.post('/api/v1/watchlist/groups', null, { params: { name, color } })
  return response.data
}

// 更新分组
export async function updateWatchlistGroup(groupId, name, color) {
  const params = {}
  if (name) params.name = name
  if (color) params.color = color
  const response = await api.put(`/api/v1/watchlist/groups/${groupId}`, { params })
  return response.data
}

// 删除分组
export async function deleteWatchlistGroup(groupId) {
  const response = await api.delete(`/api/v1/watchlist/groups/${groupId}`)
  return response.data
}

// 获取自选股列表
export async function getWatchlistStocks(groupId) {
  const response = await api.get(`/api/v1/watchlist/${groupId}`)
  return response.data
}

// 添加自选股
export async function addWatchlistStock(groupId, symbol, stockName = '') {
  const response = await api.post('/api/v1/watchlist/stocks', null, {
    params: { group_id: groupId, symbol, stock_name: stockName }
  })
  return response.data
}

// 删除自选股
export async function removeWatchlistStock(stockId) {
  const response = await api.delete(`/api/v1/watchlist/stocks/${stockId}`)
  return response.data
}

// 移动自选股到其他分组
export async function moveWatchlistStock(stockId, newGroupId) {
  const response = await api.put(`/api/v1/watchlist/stocks/${stockId}/move`, null, {
    params: { new_group_id: newGroupId }
  })
  return response.data
}

export default api
