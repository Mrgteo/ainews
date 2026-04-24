import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export interface NewsArticle {
  id: number
  title: string
  content?: string
  summary?: string
  pub_time?: string
  source?: string
  url: string
  created_at: string
  importance_score?: number
  is_incremental?: boolean
  expectation_diff?: string
  key_points?: string[]
  category?: string
  final_score?: number
  news_type?: string
  is_processed: boolean
  processed_at?: string
  notes?: string
}

export interface NewsListResponse {
  total: number
  page: number
  page_size: number
  items: NewsArticle[]
}

export interface Stats {
  total: number
  urgent_count: number
  important_count: number
  general_count: number
  noise_count: number
  unprocessed_count: number
  incremental_count: number
  avg_score?: number
}

export interface ScrapeRequest {
  days: number
}

export const getNewsList = async (params: {
  page?: number
  page_size?: number
  news_type?: string
  time_range?: string
  sort_by?: string
  is_incremental?: boolean
}): Promise<NewsListResponse> => {
  const response = await api.get('/news', { params })
  return response.data
}

export const getNewsDetail = async (id: number): Promise<NewsArticle> => {
  const response = await api.get(`/news/${id}`)
  return response.data
}

export const getStats = async (): Promise<Stats> => {
  const response = await api.get('/news/stats/summary')
  return response.data
}

export const scrapeNews = async (data: ScrapeRequest): Promise<void> => {
  await api.post('/news/scrape', data)
}

export const analyzeNews = async (id: number): Promise<void> => {
  await api.post(`/news/analyze/${id}`)
}

export const analyzeAllNews = async (params: { unprocessed_only?: boolean }): Promise<void> => {
  await api.post('/news/analyze-all', null, { params })
}

export const updateNewsType = async (
  id: number,
  data: { news_type?: string; is_processed?: boolean; notes?: string }
): Promise<void> => {
  await api.put(`/news/${id}/type`, data)
}

export const deleteNews = async (id: number): Promise<void> => {
  await api.delete(`/news/${id}`)
}
