// Vue Router 配置
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ConfigManager from '../views/ConfigManager.vue'
import DataViewer from '../views/DataViewer.vue'
import Watchlist from '../views/Watchlist.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/config',
    name: 'Config',
    component: ConfigManager
  },
  {
    path: '/data',
    name: 'DataViewer',
    component: DataViewer
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: Watchlist
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
