<template>
  <el-dialog
    v-model="visible"
    :title="news?.title"
    width="800px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div v-if="news" class="news-detail">
      <div class="detail-header">
        <div class="detail-tags">
          <el-tag
            v-if="news.news_type"
            :type="getTagType(news.news_type)"
            size="small"
          >
            {{ news.news_type }}
          </el-tag>

          <el-tag
            v-if="news.is_incremental"
            type="success"
            size="small"
            effect="plain"
          >
            增量信息
          </el-tag>

          <el-tag
            v-if="news.expectation_diff"
            :type="getExpectationType(news.expectation_diff)"
            size="small"
          >
            {{ news.expectation_diff }}
          </el-tag>

          <el-tag v-if="news.category" type="info" size="small">
            {{ news.category }}
          </el-tag>
        </div>

        <div class="detail-meta">
          <span v-if="news.source">来源: {{ news.source }}</span>
          <span v-if="news.pub_time">发布时间: {{ formatDateTime(news.pub_time) }}</span>
        </div>
      </div>

      <div class="detail-scores">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="score-box">
              <div class="score-label">综合评分</div>
              <div class="score-number" :class="getScoreClass(news.final_score || 0)">
                {{ news.final_score?.toFixed(1) || '-' }}
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-box">
              <div class="score-label">重要性</div>
              <div class="score-number">
                {{ news.importance_score ?? '-' }}
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-box">
              <div class="score-label">状态</div>
              <div class="score-number">
                {{ news.is_processed ? '已处理' : '待处理' }}
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div class="detail-keypoints" v-if="news.key_points && news.key_points.length > 0">
        <div class="section-title">核心要点</div>
        <ul class="keypoints-list">
          <li v-for="(point, idx) in news.key_points" :key="idx">{{ point }}</li>
        </ul>
      </div>

      <div class="detail-content" v-if="news.content">
        <div class="section-title">完整内容</div>
        <div class="content-text">{{ news.content }}</div>
      </div>

      <div class="detail-notes" v-if="news.notes">
        <div class="section-title">备注</div>
        <div class="notes-text">{{ news.notes }}</div>
      </div>

      <div class="detail-actions">
        <el-button @click="handleOpenUrl" type="primary" plain>
          <el-icon><Link /></el-icon>
          访问原文
        </el-button>

        <el-button @click="handleChangeType">
          <el-icon><Edit /></el-icon>
          修改分类
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" @click="handleReanalyze" :disabled="!news">
          重新分析
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Link, Edit } from '@element-plus/icons-vue'
import type { NewsArticle } from '../api/news'
import { updateNewsType, analyzeNews } from '../api/news'

const props = defineProps<{
  visible: boolean
  news: NewsArticle | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update': []
}>()

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const handleClosed = () => {
  // 清理操作
}

const getTagType = (type: string): string => {
  const map: Record<string, string> = {
    '紧急': 'danger',
    '重点关注': 'warning',
    '一般参考': 'primary',
    '已处理噪音': 'info',
  }
  return map[type] || 'info'
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

const getScoreClass = (score: number): string => {
  if (score >= 80) return 'score-urgent'
  if (score >= 60) return 'score-important'
  if (score >= 40) return 'score-general'
  return 'score-noise'
}

const formatDateTime = (timeStr: string): string => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

const handleOpenUrl = () => {
  if (props.news?.url) {
    window.open(props.news.url, '_blank')
  }
}

const handleChangeType = () => {
  if (!props.news) return

  const types = [
    { label: '紧急', value: '紧急', type: 'danger' },
    { label: '重点关注', value: '重点关注', type: 'warning' },
    { label: '一般参考', value: '一般参考', type: 'primary' },
    { label: '已处理噪音', value: '已处理噪音', type: 'info' },
  ]
  const currentType = props.news.news_type || ''

  // 创建选项按钮的HTML
  const optionsHtml = `
    <div style="display: flex; flex-direction: column; gap: 10px; padding: 10px 0;">
      <div style="color: #606266; margin-bottom: 5px;">当前分类: ${currentType || '未分类'}</div>
      ${types.map(t => `
        <button
          id="type-option-${t.value}"
          style="
            width: 100%;
            padding: 10px 15px;
            border: 1px solid ${currentType === t.value ? '#409eff' : '#dcdfe6'};
            background: ${currentType === t.value ? '#ecf5ff' : '#fff'};
            color: ${currentType === t.value ? '#409eff' : '#303133'};
            border-radius: 4px;
            cursor: pointer;
            text-align: left;
            font-size: 14px;
            ${currentType === t.value ? 'font-weight: 600;' : ''}
          "
          onclick="window.__selectType && window.__selectType('${t.value}')"
        >
          ${t.label}${currentType === t.value ? ' (当前)' : ''}
        </button>
      `).join('')}
    </div>
  `

  ElMessageBox({
    title: '修改分类',
    message: optionsHtml,
    dangerouslyUseHTMLString: true,
    showConfirmButton: false,
    showCancelButton: true,
    cancelButtonText: '关闭',
    closeOnClickModal: true,
    closeOnPressEscape: true,
  })

  // 设置选择回调
  window.__selectType = async (selectedType: string) => {
    ElMessageBox.close()
    if (selectedType && selectedType !== currentType) {
      try {
        await updateNewsType(props.news!.id, { news_type: selectedType })
        ElMessage.success(`已修改分类为: ${selectedType}`)
        emit('update')
      } catch {
        ElMessage.error('修改失败')
      }
    }
  }
}

const handleReanalyze = async () => {
  if (!props.news) {
    ElMessage.warning('没有选中的新闻')
    return
  }

  try {
    ElMessage.info('开始分析...')
    await analyzeNews(props.news.id)
    ElMessage.success('分析完成')
    emit('update')
  } catch (error) {
    ElMessage.error('分析失败')
    console.error(error)
  }
}
</script>

<style scoped>
.news-detail {
  padding: 0 8px;
}

.detail-header {
  margin-bottom: 20px;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.detail-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.detail-scores {
  background: var(--background);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.score-box {
  text-align: center;
}

.score-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.score-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
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

.detail-keypoints {
  margin-bottom: 20px;
}

.keypoints-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.keypoints-list li {
  padding: 8px 12px;
  background: #E6F7FF;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 14px;
}

.keypoints-list li:last-child {
  margin-bottom: 0;
}

.detail-content {
  margin-bottom: 20px;
}

.content-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
  background: var(--background);
  border-radius: 4px;
}

.detail-notes {
  margin-bottom: 20px;
}

.notes-text {
  font-size: 14px;
  color: var(--text-secondary);
  padding: 12px;
  background: var(--background);
  border-radius: 4px;
}

.detail-actions {
  display: flex;
  gap: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
