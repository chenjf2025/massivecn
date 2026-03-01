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

export default api
