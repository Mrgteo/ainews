<template>
  <div id="app">
    <header class="header">
      <h1>舆情监控与汇总系统</h1>
      <div class="header-actions">
        <el-button type="primary" @click="handleScrape" :loading="scrapeLoading">
          <el-icon><Refresh /></el-icon>
          爬取新闻
        </el-button>
        <el-button type="success" @click="handleAnalyze" :loading="analyzeLoading">
          <el-icon><DataAnalysis /></el-icon>
          AI分析
        </el-button>
      </div>
    </header>

    <div class="page-container">
      <Dashboard :stats="stats" />

      <div class="filter-bar">
        <el-radio-group v-model="filterType" size="default" @change="handleFilterChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="紧急">紧急</el-radio-button>
          <el-radio-button label="重点关注">重点关注</el-radio-button>
          <el-radio-button label="一般参考">一般参考</el-radio-button>
          <el-radio-button label="已处理噪音">已处理噪音</el-radio-button>
          <el-radio-button label="incremental">增量信息</el-radio-button>
        </el-radio-group>

        <el-select v-model="timeRange" size="default" style="width: 120px" @change="handleFilterChange">
          <el-option label="近1天" value="1d" />
          <el-option label="近3天" value="3d" />
          <el-option label="近7天" value="7d" />
          <el-option label="近30天" value="30d" />
        </el-select>

        <el-select v-model="sortBy" size="default" style="width: 140px" @change="handleFilterChange">
          <el-option label="综合评分" value="final_score" />
          <el-option label="发布时间" value="pub_time" />
          <el-option label="重要性" value="importance_score" />
        </el-select>
      </div>

      <NewsList :news="newsList" :loading="loading" @load-more="loadMore" @item-click="handleItemClick" />

      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper, total"
        style="margin-top: 20px; justify-content: center"
        @current-change="handlePageChange"
      />

      <NewsDetail
        v-model:visible="detailVisible"
        :news="currentNews"
        @update="handleNewsUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DataAnalysis } from '@element-plus/icons-vue'
import Dashboard from './components/Dashboard.vue'
import NewsList from './components/NewsList.vue'
import NewsDetail from './components/NewsDetail.vue'
import { getNewsList, getStats, scrapeNews, analyzeNews, analyzeAllNews } from './api/news'
import type { NewsArticle, Stats } from './api/news'

const newsList = ref<NewsArticle[]>([])
const stats = ref<Stats | null>(null)
const loading = ref(false)
const scrapeLoading = ref(false)
const analyzeLoading = ref(false)

const filterType = ref('')
const timeRange = ref('1d')
const sortBy = ref('final_score')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const currentNews = ref<NewsArticle | null>(null)

const fetchNews = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
      time_range: timeRange.value,
      sort_by: sortBy.value,
    }

    if (filterType.value === 'incremental') {
      params.is_incremental = true
    } else if (filterType.value) {
      params.news_type = filterType.value
    }

    const res = await getNewsList(params)
    newsList.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('获取新闻列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await getStats()
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchNews()
}

const handlePageChange = () => {
  fetchNews()
}

const handleScrape = async () => {
  scrapeLoading.value = true
  try {
    await scrapeNews({ days: 3 })
    ElMessage.success('爬虫任务已启动')
    setTimeout(() => {
      fetchNews()
      fetchStats()
    }, 5000)
  } catch (error) {
    ElMessage.error('启动爬虫失败')
  } finally {
    scrapeLoading.value = false
  }
}

const handleAnalyze = async () => {
  analyzeLoading.value = true
  try {
    await analyzeAllNews({ unprocessed_only: true })
    ElMessage.success('分析任务已启动')
    setTimeout(() => {
      fetchNews()
      fetchStats()
    }, 10000)
  } catch (error) {
    ElMessage.error('启动分析失败')
  } finally {
    analyzeLoading.value = false
  }
}

const handleItemClick = (news: NewsArticle) => {
  currentNews.value = news
  detailVisible.value = true
}

const handleNewsUpdate = () => {
  fetchNews()
  fetchStats()
}

const loadMore = () => {
  if (currentPage.value * pageSize.value < total.value) {
    currentPage.value++
    fetchNews()
  }
}

onMounted(() => {
  fetchNews()
  fetchStats()
})
</script>

<style scoped>
</style>
