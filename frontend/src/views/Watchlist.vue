<template>
  <div class="watchlist-container">
    <el-row :gutter="20">
      <!-- 左侧分组列表 -->
      <el-col :span="6">
        <el-card shadow="hover" class="group-card">
          <template #header>
            <div class="group-header">
              <span>自选分组</span>
              <el-button type="primary" size="small" text @click="showAddGroupDialog">
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="group-list">
            <div 
              v-for="group in groups" 
              :key="group.id"
              :class="['group-item', { active: currentGroupId === group.id }]"
              @click="selectGroup(group.id)"
            >
              <div class="group-info">
                <span class="group-color" :style="{ backgroundColor: group.color }"></span>
                <span class="group-name">{{ group.name }}</span>
                <span class="group-count">({{ group.stock_count }})</span>
              </div>
              <el-dropdown trigger="click" @command="handleGroupCommand($event, group)">
                <el-button size="small" text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧自选股列表 -->
      <el-col :span="18">
        <el-card shadow="hover" class="stock-card">
          <template #header>
            <div class="stock-header">
              <div class="stock-title">
                <span>{{ currentGroupName }}</span>
                <el-tag size="small" type="info">{{ stocks.length }} 只股票</el-tag>
              </div>
              <div class="stock-actions">
                <el-select 
                  v-model="sortBy" 
                  size="small" 
                  style="width: 120px; margin-right: 10px"
                  @change="loadStocks"
                >
                  <el-option label="默认排序" value="default" />
                  <el-option label="涨跌幅" value="change" />
                  <el-option label="最新价" value="price" />
                </el-select>
                <el-button type="primary" @click="showAddStockDialog">
                  <el-icon><Plus /></el-icon>
                  添加股票
                </el-button>
              </div>
            </div>
          </template>

          <el-table 
            :data="stocks" 
            style="width: 100%"
            :row-class-name="tableRowClassName"
            @row-click="handleRowClick"
          >
            <el-table-column prop="stock_name" label="股票" min-width="120">
              <template #default="{ row }">
                <div class="stock-cell">
                  <span class="stock-name">{{ row.stock_name || row.symbol }}</span>
                  <span class="stock-code">{{ row.symbol }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="current_price" label="最新价" width="100" align="right">
              <template #default="{ row }">
                <span :class="['price', getPriceClass(row)]">
                  {{ row.current_price > 0 ? row.current_price.toFixed(2) : '-' }}
                </span>
              </template>
            </el-table-column>
            
            <el-table-column prop="change" label="涨跌额" width="100" align="right">
              <template #default="{ row }">
                <span :class="['change', getPriceClass(row)]">
                  {{ row.change > 0 ? '+' : '' }}{{ row.change.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            
            <el-table-column prop="change_pct" label="涨跌幅" width="100" align="right">
              <template #default="{ row }">
                <span :class="['change-pct', getPriceClass(row)]">
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="support" label="支撑位" width="90" align="right">
              <template #default="{ row }">
                <span class="support">{{ row.support > 0 ? row.support.toFixed(2) : '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="resistance" label="压力位" width="90" align="right">
              <template #default="{ row }">
                <span class="resistance">{{ row.resistance > 0 ? row.resistance.toFixed(2) : '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-dropdown trigger="click" @command="handleStockCommand($event, row)" @click.stop>
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="move">移动到...</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="stocks.length === 0" description="暂无自选股，点击添加" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加分组对话框 -->
    <el-dialog v-model="groupDialogVisible" title="分组管理" width="400px">
      <el-form :model="groupForm" label-width="60px">
        <el-form-item label="名称">
          <el-input v-model="groupForm.name" placeholder="分组名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="groupForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGroup">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加股票对话框 -->
    <el-dialog v-model="stockDialogVisible" title="添加自选股" width="500px">
      <div class="add-stock-search">
        <el-input
          v-model="searchKeyword"
          placeholder="输入股票代码/名称/拼音搜索"
          @input="handleSearch"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <div v-if="searchResults.length > 0" class="search-results">
          <div 
            v-for="item in searchResults" 
            :key="item.symbol"
            class="search-result-item"
            @click="selectStock(item)"
          >
            <span class="result-name">{{ item.name }}</span>
            <span class="result-code">{{ item.symbol }}</span>
          </div>
        </div>
        
        <div v-else-if="searchKeyword && searchResults.length === 0" class="no-results">
          未找到匹配的股票
        </div>
      </div>
    </el-dialog>

    <!-- 移动股票对话框 -->
    <el-dialog v-model="moveDialogVisible" title="移动到分组" width="400px">
      <el-radio-group v-model="targetGroupId">
        <el-radio 
          v-for="group in groups" 
          :key="group.id" 
          :value="group.id"
          :disabled="group.id === currentGroupId"
          style="display: block; margin-bottom: 10px"
        >
          <span :style="{ color: group.color }">●</span> {{ group.name }}
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmMove">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, MoreFilled, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { 
  getWatchlistGroups, 
  createWatchlistGroup, 
  updateWatchlistGroup, 
  deleteWatchlistGroup,
  getWatchlistStocks,
  addWatchlistStock,
  removeWatchlistStock,
  moveWatchlistStock,
  resolveStock
} from '../api'

const router = useRouter()

// 数据
const groups = ref([])
const stocks = ref([])
const currentGroupId = ref(null)
const sortBy = ref('default')

// 对话框
const groupDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const moveDialogVisible = ref(false)
const groupForm = ref({ id: null, name: '', color: '#409EFF' })
const isEditGroup = ref(false)

// 搜索
const searchKeyword = ref('')
const searchResults = ref([])
const selectedStock = ref(null)
const targetStockId = ref(null)
const targetGroupId = ref(null)

// 计算属性
const currentGroupName = computed(() => {
  const group = groups.value.find(g => g.id === currentGroupId.value)
  return group?.name || '请选择分组'
})

// 方法
async function loadGroups() {
  try {
    const result = await getWatchlistGroups()
    if (result.success) {
      groups.value = result.data
      // 默认选择第一个分组
      if (groups.value.length > 0 && !currentGroupId.value) {
        currentGroupId.value = groups.value[0].id
        await loadStocks()
      }
    }
  } catch (e) {
    ElMessage.error('加载分组失败')
  }
}

async function loadStocks() {
  if (!currentGroupId.value) return
  
  try {
    const result = await getWatchlistStocks(currentGroupId.value)
    if (result.success) {
      stocks.value = result.data || []
      // 排序
      if (sortBy.value === 'change') {
        stocks.value.sort((a, b) => (b.change_pct || 0) - (a.change_pct || 0))
      } else if (sortBy.value === 'price') {
        stocks.value.sort((a, b) => (b.current_price || 0) - (a.current_price || 0))
      }
    }
  } catch (e) {
    ElMessage.error('加载自选股失败')
  }
}

function selectGroup(groupId) {
  currentGroupId.value = groupId
  loadStocks()
}

function showAddGroupDialog() {
  groupForm.value = { id: null, name: '', color: '#409EFF' }
  isEditGroup.value = false
  groupDialogVisible.value = true
}

async function saveGroup() {
  if (!groupForm.value.name) {
    ElMessage.warning('请输入分组名称')
    return
  }
  
  try {
    if (isEditGroup.value) {
      await updateWatchlistGroup(groupForm.value.id, groupForm.value.name, groupForm.value.color)
      ElMessage.success('分组已更新')
    } else {
      await createWatchlistGroup(groupForm.value.name, groupForm.value.color)
      ElMessage.success('分组已创建')
    }
    groupDialogVisible.value = false
    await loadGroups()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

function handleGroupCommand(command, group) {
  if (command === 'edit') {
    groupForm.value = { id: group.id, name: group.name, color: group.color }
    isEditGroup.value = true
    groupDialogVisible.value = true
  } else if (command === 'delete') {
    if (groups.value.length <= 1) {
      ElMessage.warning('至少保留一个分组')
      return
    }
    deleteWatchlistGroup(group.id).then(() => {
      ElMessage.success('分组已删除')
      if (currentGroupId.value === group.id) {
        currentGroupId.value = groups.value[0]?.id
      }
      loadGroups()
    })
  }
}

function showAddStockDialog() {
  searchKeyword.value = ''
  searchResults.value = []
  selectedStock.value = null
  stockDialogVisible.value = true
}

let searchTimer = null
function handleSearch(keyword) {
  if (searchTimer) clearTimeout(searchTimer)
  
  if (!keyword) {
    searchResults.value = []
    return
  }
  
  searchTimer = setTimeout(async () => {
    try {
      const result = await resolveStock(keyword)
      if (result.success) {
        searchResults.value = [result]
      } else {
        searchResults.value = []
      }
    } catch (e) {
      searchResults.value = []
    }
  }, 300)
}

function selectStock(item) {
  addWatchlistStock(currentGroupId.value, item.symbol, item.name).then(result => {
    if (result.success) {
      ElMessage.success('已添加到自选')
      stockDialogVisible.value = false
      loadStocks()
      loadGroups()
    } else {
      ElMessage.warning(result.message || '添加失败')
    }
  })
}

function handleStockCommand(command, stock) {
  if (command === 'delete') {
    removeWatchlistStock(stock.id).then(() => {
      ElMessage.success('已从自选删除')
      loadStocks()
      loadGroups()
    })
  } else if (command === 'move') {
    targetStockId.value = stock.id
    targetGroupId.value = null
    moveDialogVisible.value = true
  }
}

function confirmMove() {
  if (!targetGroupId.value) {
    ElMessage.warning('请选择目标分组')
    return
  }
  moveWatchlistStock(targetStockId.value, targetGroupId.value).then(() => {
    ElMessage.success('已移动到新分组')
    moveDialogVisible.value = false
    loadStocks()
    loadGroups()
  })
}

function getPriceClass(row) {
  if (row.change_pct > 0) return 'up'
  if (row.change_pct < 0) return 'down'
  return ''
}

function formatVolume(vol) {
  if (!vol) return '-'
  if (vol >= 100000000) return (vol / 100000000).toFixed(1) + '亿'
  if (vol >= 10000) return (vol / 10000).toFixed(1) + '万'
  return vol.toString()
}

function tableRowClassName({ row }) {
  return row.change_pct > 0 ? 'up-row' : row.change_pct < 0 ? 'down-row' : ''
}

function handleRowClick(row) {
  router.push({ path: '/data', query: { symbol: row.symbol } })
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.watchlist-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.group-card {
  height: calc(100vh - 140px);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.group-item:hover {
  background-color: #f5f7fa;
}

.group-item.active {
  background-color: #ecf5ff;
}

.group-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.group-name {
  font-weight: 500;
}

.group-count {
  color: #909399;
  font-size: 12px;
}

.stock-card {
  min-height: calc(100vh - 140px);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
}

.stock-actions {
  display: flex;
  align-items: center;
}

.stock-cell {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: 500;
}

.stock-code {
  font-size: 12px;
  color: #909399;
}

.price {
  font-weight: 600;
}

.change, .change-pct {
  font-weight: 500;
}

.up {
  color: #f56c6c;
}

.down {
  color: #67c23a;
}

.up-row {
  background-color: #fef0f0;
}

.down-row {
  background-color: #f0f9eb;
}

.add-stock-search {
  padding: 10px 0;
}

.search-results {
  margin-top: 15px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: #f5f7fa;
}

.result-name {
  font-weight: 500;
}

.result-code {
  color: #909399;
  font-size: 12px;
}

.no-results {
  text-align: center;
  padding: 30px;
  color: #909399;
}
</style>
