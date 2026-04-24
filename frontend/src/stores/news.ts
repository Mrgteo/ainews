import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { NewsArticle, Stats } from '../api/news'
import { getNewsList, getStats } from '../api/news'

export const useNewsStore = defineStore('news', () => {
  const newsList = ref<NewsArticle[]>([])
  const stats = ref<Stats | null>(null)
  const loading = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)

  const urgentNews = computed(() => newsList.value.filter(n => n.news_type === '紧急'))
  const importantNews = computed(() => newsList.value.filter(n => n.news_type === '重点关注'))
  const generalNews = computed(() => newsList.value.filter(n => n.news_type === '一般参考'))
  const noiseNews = computed(() => newsList.value.filter(n => n.news_type === '已处理噪音'))
  const incrementalNews = computed(() => newsList.value.filter(n => n.is_incremental === true))

  const fetchNews = async (params: any = {}) => {
    loading.value = true
    try {
      const res = await getNewsList({
        page: currentPage.value,
        page_size: pageSize.value,
        ...params,
      })
      newsList.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      stats.value = await getStats()
    } catch (error) {
      console.error('获取统计失败:', error)
    }
  }

  return {
    newsList,
    stats,
    loading,
    currentPage,
    pageSize,
    total,
    urgentNews,
    importantNews,
    generalNews,
    noiseNews,
    incrementalNews,
    fetchNews,
    fetchStats,
  }
})
