<template>
  <div class="data-viewer">
    <!-- 查询条件 -->
    <el-card shadow="hover" class="query-card">
      <el-form inline>
        <el-form-item label="股票代码">
          <el-input
            v-model="queryForm.symbol"
            placeholder="sh600000"
            style="width: 150px"
          />
        </el-form-item>
        
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="queryForm.startTime"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 150px"
          />
        </el-form-item>
        
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="queryForm.endTime"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 150px"
          />
        </el-form-item>
        
        <el-form-item label="周期">
          <el-select v-model="queryForm.interval" style="width: 120px">
            <el-option label="1分钟" value="1min" />
            <el-option label="5分钟" value="5min" />
            <el-option label="15分钟" value="15min" />
            <el-option label="30分钟" value="30min" />
            <el-option label="60分钟" value="60min" />
            <el-option label="日线" value="1day" />
          </el-select>
        </el-form-item>
        <el-form-item label="聚合">
          <el-select v-model="queryForm.aggregation" style="width: 100px">
            <el-option label="不聚合" :value="undefined" />
            <el-option label="5分钟" :value="5" />
            <el-option label="15分钟" :value="15" />
            <el-option label="30分钟" :value="30" />
            <el-option label="60分钟" :value="60" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadData" :loading="loading">
            查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- K线图 + 资金流向图 -->
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>{{ queryForm.symbol || 'K线图表' }}</span>
          <span class="data-info" v-if="chartData.length">
            共 {{ chartData.length }} 条数据
          </span>
        </div>
      </template>
      
      <div v-if="!loading && chartData.length" class="charts-container">
        <!-- 上半部分: K线图 + VWAP -->
        <div ref="klineChart" class="chart kline-chart"></div>
        
        <!-- 下半部分: 成交量 + 主力资金 -->
        <div ref="volumeChart" class="chart volume-chart"></div>
      </div>
      
      <el-empty v-else-if="!loading" description="请输入股票代码查询数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getHistory } from '../api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

// -------------------- 数据 --------------------

const loading = ref(false)
const chartData = ref([])
const klineChart = ref(null)
const volumeChart = ref(null)

let klineInstance = null
let volumeInstance = null

const queryForm = ref({
  symbol: 'sh600000',
  startTime: dayjs().subtract(7, 'day').format('YYYY-MM-DD'),
  endTime: dayjs().format('YYYY-MM-DD'),
  interval: '5min',
  aggregation: 5
})

// -------------------- 方法 --------------------

async function loadData() {
  if (!queryForm.value.symbol) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  loading.value = true
  
  try {
    const params = {
      symbol: queryForm.value.symbol,
      interval: queryForm.value.interval,
      aggregation: queryForm.value.aggregation
    }
    
    if (queryForm.value.startTime) {
      params.start_time = queryForm.value.startTime + 'T00:00:00'
    }
    if (queryForm.value.endTime) {
      params.end_time = queryForm.value.endTime + 'T23:59:59'
    }
    
    const result = await getHistory(queryForm.value.symbol, params)
    
    if (result.success) {
      chartData.value = result.data || []
      
      if (chartData.value.length === 0) {
        ElMessage.warning('暂无数据 (TDengine数据库中无历史行情数据)')
      } else {
        // 等待 DOM 更新后渲染图表
        renderCharts()
      }
    } else {
      ElMessage.error('查询失败: ' + (result.message || ''))
    }
  } catch (e) {
    ElMessage.error('查询异常: ' + e.message)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (!chartData.value.length) return
  
  // 准备数据
  const dates = chartData.value.map(d => dayjs(d.timestamp).format('MM-DD HH:mm'))
  const ohlc = chartData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = chartData.value.map(d => d.volume)
  const mainNetInflow = chartData.value.map(d => d.mainNetInflow || 0)
  const vwap = chartData.value.map(d => d.vwap || ((d.high + d.low + d.close) / 3))
  
  // ---------------- K线图 ----------------
  const klineOption = {
    title: {
      text: 'K线图 (VWAP均价)',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: [
      { left: '10%', right: '8%', height: '60%' },
      { left: '10%', right: '8%', top: '72%', height: '18%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLabel: { show: false }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLabel: { fontSize: 10 }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitArea: { show: true }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { fontSize: 10 }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 5 }
    ],
    series: [
      // K线
      {
        name: 'KLine',
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#ef4444',
          borderColor0: '#22c55e'
        }
      },
      // VWAP 均价线
      {
        name: 'VWAP',
        type: 'line',
        data: vwap,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { width: 2, color: '#f59e0b' },
        symbol: 'none'
      },
      // 成交量柱状图
      {
        name: 'Volume',
        type: 'bar',
        data: volumes,
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: {
          color: (params) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return close >= open ? '#ef4444' : '#22c55e'
          }
        }
      }
    ]
  }
  
  // ---------------- 资金流向图 (双轴) ----------------
  const volumeOption = {
    title: {
      text: '成交量 & 主力资金净流入',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: { left: '10%', right: '8%', top: '15%', bottom: '10%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '成交量',
        position: 'left',
        axisLabel: { fontSize: 10 }
      },
      {
        type: 'value',
        name: '主力净流入',
        position: 'right',
        axisLabel: {
          fontSize: 10,
          formatter: (value) => {
            if (value >= 10000) return (value / 10000).toFixed(0) + '万'
            return value
          }
        }
      }
    ],
    dataZoom: [
      { type: 'inside', start: 60, end: 100 }
    ],
    series: [
      // 成交量
      {
        name: '成交量',
        type: 'bar',
        data: volumes,
        yAxisIndex: 0,
        itemStyle: {
          color: (params) => {
            const idx = params.dataIndex
            const open = ohlc[idx][0]
            const close = ohlc[idx][1]
            return close >= open ? '#ef4444' : '#22c55e'
          }
        }
      },
      // 主力资金净流入
      {
        name: '主力净流入',
        type: 'line',
        data: mainNetInflow,
        yAxisIndex: 1,
        smooth: true,
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
          ])
        },
        symbol: 'none'
      }
    ]
  }
  
  // 渲染图表
  if (klineChart.value) {
    if (!klineInstance) {
      klineInstance = echarts.init(klineChart.value)
    }
    klineInstance.setOption(klineOption)
  }
  
  if (volumeChart.value) {
    if (!volumeInstance) {
      volumeInstance = echarts.init(volumeChart.value)
    }
    volumeInstance.setOption(volumeOption)
  }
}

// 响应式调整
function handleResize() {
  klineInstance?.resize()
  volumeInstance?.resize()
}

// 监听数据变化重新渲染
watch(chartData, () => {
  if (chartData.value.length > 0) {
    nextTick(renderCharts)
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  
  // 初始加载示例数据
  loadData()
})
</script>

<style scoped>
.data-viewer {
  max-width: 1600px;
  margin: 0 auto;
}

.query-card {
  margin-bottom: 20px;
}

.chart-card {
  min-height: 700px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-info {
  font-size: 12px;
  color: #718096;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chart {
  width: 100%;
  min-height: 350px;
}

.kline-chart {
  height: 400px;
}

.volume-chart {
  height: 280px;
}
</style>
