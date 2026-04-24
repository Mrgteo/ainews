<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card urgent">
          <div class="stat-value" style="color: var(--urgent)">
            {{ stats?.urgent_count || 0 }}
          </div>
          <div class="stat-label">
            紧急新闻
            <span class="trend" v-if="stats && stats.urgent_count > 0">
              <el-icon><Top /></el-icon>
            </span>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card important">
          <div class="stat-value" style="color: var(--important)">
            {{ stats?.important_count || 0 }}
          </div>
          <div class="stat-label">重点关注</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card general">
          <div class="stat-value" style="color: var(--general)">
            {{ stats?.general_count || 0 }}
          </div>
          <div class="stat-label">一般参考</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card noise">
          <div class="stat-value" style="color: var(--noise)">
            {{ stats?.noise_count || 0 }}
          </div>
          <div class="stat-label">已处理噪音</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-value" style="color: var(--primary)">
            {{ stats?.total || 0 }}
          </div>
          <div class="stat-label">新闻总数</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-value" style="color: #67C23A">
            {{ stats?.incremental_count || 0 }}
          </div>
          <div class="stat-label">增量信息</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-value">
            {{ stats?.avg_score?.toFixed(1) || '0.0' }}
          </div>
          <div class="stat-label">平均综合评分</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <ScoreChart :stats="stats" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { Top } from '@element-plus/icons-vue'
import type { Stats } from '../api/news'
import ScoreChart from './ScoreChart.vue'

defineProps<{
  stats: Stats | null
}>()
</script>

<style scoped>
.trend {
  color: #67C23A;
  margin-left: 4px;
}
</style>
