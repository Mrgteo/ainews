<template>
  <div class="news-list">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="news.length === 0" class="empty-container">
      <el-empty description="暂无新闻数据">
        <el-button type="primary" @click="$emit('refresh')">刷新</el-button>
      </el-empty>
    </div>

    <div v-else>
      <div
        v-for="item in news"
        :key="item.id"
        class="news-item"
        @click="$emit('item-click', item)"
      >
        <div class="news-header">
          <el-tag
            v-if="item.news_type"
            :type="getTagType(item.news_type)"
            size="small"
            class="news-type-tag"
          >
            {{ item.news_type }}
          </el-tag>

          <el-tag
            v-if="item.is_incremental"
            type="success"
            size="small"
            effect="plain"
            class="incremental-tag"
          >
            增量
          </el-tag>

          <span class="news-time" v-if="item.pub_time">
            {{ formatTime(item.pub_time) }}
          </span>
        </div>

        <div class="news-title">{{ item.title }}</div>

        <div class="news-meta" v-if="item.source || item.category">
          <span v-if="item.source" class="news-source">{{ item.source }}</span>
          <span v-if="item.category" class="news-category">{{ item.category }}</span>
        </div>

        <div class="news-footer">
          <div class="news-score" v-if="item.final_score">
            <span class="score-label">综合评分</span>
            <span class="score-value" :class="getScoreClass(item.final_score)">
              {{ item.final_score.toFixed(1) }}
            </span>
          </div>

          <div class="news-importance" v-if="item.importance_score">
            <span class="score-label">重要性</span>
            <span class="score-value">{{ item.importance_score }}</span>
          </div>

          <div class="news-expectation" v-if="item.expectation_diff">
            <el-tag
              :type="getExpectationType(item.expectation_diff)"
              size="small"
            >
              {{ item.expectation_diff }}
            </el-tag>
          </div>
        </div>

        <div class="news-keypoints" v-if="item.key_points && item.key_points.length > 0">
          <div class="keypoint" v-for="(point, idx) in item.key_points.slice(0, 2)" :key="idx">
            {{ point }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NewsArticle } from '../api/news'

defineProps<{
  news: NewsArticle[]
  loading: boolean
}>()

defineEmits<{
  'item-click': [news: NewsArticle]
  'load-more': []
  'refresh': []
}>()

const getTagType = (type: string): string => {
  const map: Record<string, string> = {
    '紧急': 'danger',
    '重点关注': 'warning',
    '一般参考': 'primary',
    '已处理噪音': 'info',
  }
  return map[type] || 'info'
}

const getScoreClass = (score: number): string => {
  if (score >= 80) return 'score-urgent'
  if (score >= 60) return 'score-important'
  if (score >= 40) return 'score-general'
  return 'score-noise'
}

const getExpectationType = (diff: string): string => {
  const map: Record<string, string> = {
    '超预期': 'success',
    '符合预期': 'info',
    '低于预期': 'warning',
    '无法判断': 'info',
  }
  return map[diff] || 'info'
}

const formatTime = (timeStr: string): string => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.news-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.news-type-tag {
  font-weight: 500;
}

.news-time {
  margin-left: auto;
  color: var(--text-secondary);
  font-size: 12px;
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.news-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.news-score,
.news-importance {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.score-value {
  font-weight: 600;
  font-size: 14px;
}

.score-urgent {
  color: var(--urgent);
}

.score-important {
  color: var(--important);
}

.score-general {
  color: var(--general);
}

.score-noise {
  color: var(--noise);
}

.news-keypoints {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keypoint {
  background: var(--background);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.incremental-tag {
  margin-left: 4px;
}

.loading-container,
.empty-container {
  padding: 40px;
  text-align: center;
}
</style>
