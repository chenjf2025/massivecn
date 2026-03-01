<template>
  <div class="config-manager">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>网关配置</span>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 主数据源 -->
        <el-tab-pane label="主数据源" name="primary">
          <el-table :data="localConfig.sources?.primary || []" style="width: 100%">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column label="启用" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" />
              </template>
            </el-table-column>
            <el-table-column label="优先级" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.priority"
                  :min="1"
                  :max="10"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="超时(秒)" width="120">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.timeout"
                  :min="1"
                  :max="30"
                  :step="0.5"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="重试次数" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.retry"
                  :min="0"
                  :max="5"
                  size="small"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <!-- 备用数据源 -->
        <el-tab-pane label="备用数据源" name="backup">
          <el-table :data="localConfig.sources?.backup || []" style="width: 100%">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column label="启用" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" />
              </template>
            </el-table-column>
            <el-table-column label="优先级" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.priority"
                  :min="1"
                  :max="10"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="超时(秒)" width="120">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.timeout"
                  :min="1"
                  :max="30"
                  :step="0.5"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="重试次数" width="100">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.retry"
                  :min="0"
                  :max="5"
                  size="small"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <!-- 路由策略 -->
        <el-tab-pane label="路由策略" name="routing">
          <el-form label-width="150px" style="max-width: 600px">
            <el-form-item label="启用降级">
              <el-switch v-model="localConfig.routing.failover" />
            </el-form-item>
            <el-form-item label="请求超时(秒)">
              <el-input-number
                v-model="localConfig.routing.request_timeout"
                :min="1"
                :max="60"
                :step="0.5"
              />
            </el-form-item>
            <el-form-item label="最大重试次数">
              <el-input-number
                v-model="localConfig.routing.max_retries"
                :min="0"
                :max="10"
              />
            </el-form-item>
            <el-form-item label="降级延迟(毫秒)">
              <el-input-number
                v-model="localConfig.routing.failover_delay"
                :min="0"
                :max="5000"
                :step="100"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 异步任务 -->
        <el-tab-pane label="异步任务" name="async">
          <el-form label-width="150px" style="max-width: 600px">
            <el-form-item label="启用异步落库">
              <el-switch v-model="localConfig.system.async_task.enabled" />
            </el-form-item>
            <el-form-item label="批量大小">
              <el-input-number
                v-model="localConfig.system.async_task.batch_size"
                :min="1"
                :max="1000"
              />
            </el-form-item>
            <el-form-item label="刷新间隔(秒)">
              <el-input-number
                v-model="localConfig.system.async_task.flush_interval"
                :min="1"
                :max="60"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig } from '../api'
import { ElMessage } from 'element-plus'

const activeTab = ref('primary')
const saving = ref(false)
const localConfig = ref({
  sources: {
    primary: [],
    backup: []
  },
  routing: {},
  system: {
    async_task: {}
  }
})

// 加载配置
async function loadConfig() {
  try {
    const data = await getConfig()
    localConfig.value = data.data
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

// 保存配置
async function saveConfig() {
  saving.value = true
  try {
    await updateConfig(localConfig.value)
    ElMessage.success('配置保存成功')
  } catch (e) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config-manager {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
