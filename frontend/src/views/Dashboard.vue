<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">系统状态</div>
            <div class="stat-value">
              <el-tag :type="statusData.status === 'running' ? 'success' : 'danger'">
                {{ statusData.status === 'running' ? '运行中' : '异常' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">今日入库量</div>
            <div class="stat-value">{{ statusData.todayIngested || 0 }} 条</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">平均延迟</div>
            <div class="stat-value">{{ statusData.avgLatency || 0 }} ms</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-label">运行时间</div>
            <div class="stat-value">{{ formatUptime(statusData.uptime) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 数据源状态 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>数据源状态</span>
              <el-button type="primary" size="small" @click="refreshStatus">
                刷新
              </el-button>
            </div>
          </template>
          
          <el-table :data="statusData.sources || []" style="width: 100%">
            <el-table-column prop="name" label="数据源" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'online' ? 'success' : 'danger'" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="requestCount" label="请求数" width="100" />
            <el-table-column prop="successRate" label="成功率" width="100">
              <template #default="{ row }">
                {{ (row.successRate * 100).toFixed(1) }}%
              </template>
            <el-table-column prop="success_rate" label="成功率" width="100">
              <template #default="{ row }">
                {{ (row.success_rate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快速查询 -->
    <el-row :gutter="20" class="section-row">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>快速查询</span>
          </template>
          
          <el-form inline>
            <el-form-item label="股票代码">
              <el-input
                v-model="quickSymbol"
                placeholder="如: sh600000"
                style="width: 180px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="quickQuery" :loading="queryLoading">
                查询
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="quoteData" class="quote-result">
            <el-descriptions :column="4" border>
              <el-descriptions-item label="股票代码">
                {{ quoteData.symbol }}
              </el-descriptions-item>
              <el-descriptions-item label="数据源">
                <el-tag size="small">{{ quoteData.dataSource }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="当前价">
                <span :class="quoteData.change >= 0 ? 'price-up' : 'price-down'">
                  {{ quoteData.currentPrice }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="涨跌">
                <span :class="quoteData.change >= 0 ? 'price-up' : 'price-down'">
                  {{ quoteData.change > 0 ? '+' : '' }}{{ quoteData.change }}
                  ({{ quoteData.changePct }}%)
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="开盘">{{ quoteData.openPrice }}</el-descriptions-item>
              <el-descriptions-item label="最高">{{ quoteData.highPrice }}</el-descriptions-item>
              <el-descriptions-item label="最低">{{ quoteData.lowPrice }}</el-descriptions-item>
              <el-descriptions-item label="成交量">
                {{ formatVolume(quoteData.tradingVolume) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSystemStatus, getQuote } from '../api'
import { ElMessage } from 'element-plus'

const statusData = ref({})
const quickSymbol = ref('')
const queryLoading = ref(false)
const quoteData = ref(null)

// 刷新状态
async function refreshStatus() {
  try {
    const data = await getSystemStatus()
    statusData.value = data
  } catch (e) {
    ElMessage.error('获取状态失败')
  }
}

// 快速查询
async function quickQuery() {
  if (!quickSymbol.value) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  queryLoading.value = true
  try {
    const result = await getQuote(quickSymbol.value)
    if (result.success) {
      quoteData.value = result.data
      ElMessage.success('查询成功')
    } else {
      ElMessage.error(result.message || '查询失败')
    }
  } catch (e) {
    ElMessage.error('查询异常')
  } finally {
    queryLoading.value = false
  }
}

// 格式化运行时间
function formatUptime(seconds) {
  if (!seconds) return '0s'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

// 格式化成交量
function formatVolume(v) {
  if (!v) return '0'
  if (v >= 100000000) return (v / 100000000).toFixed(2) + '亿'
  if (v >= 10000) return (v / 10000).toFixed(2) + '万'
  return v.toString()
}

onMounted(() => {
  refreshStatus()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-label {
  font-size: 14px;
  color: #718096;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
}

.section-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quote-result {
  margin-top: 20px;
}

.price-up {
  color: #e53e3e;
}

.price-down {
  color: #38a169;
}
</style>
