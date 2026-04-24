<template>
  <div class="score-chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { Stats } from '../api/news'

const props = defineProps<{
  stats: Stats | null
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)

  const option: echarts.EChartsOption = {
    title: {
      text: '新闻分类分布',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      data: ['紧急', '重点关注', '一般参考', '已处理噪音'],
    },
    series: [
      {
        name: '新闻分类',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: '{b}: {c}',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        data: [
          { value: props.stats?.urgent_count || 0, name: '紧急', itemStyle: { color: '#FF4D4F' } },
          { value: props.stats?.important_count || 0, name: '重点关注', itemStyle: { color: '#FF7A45' } },
          { value: props.stats?.general_count || 0, name: '一般参考', itemStyle: { color: '#1890FF' } },
          { value: props.stats?.noise_count || 0, name: '已处理噪音', itemStyle: { color: '#8C8C8C' } },
        ],
      },
    ],
  }

  chart.setOption(option)
}

const updateChart = () => {
  if (!chart) return

  chart.setOption({
    series: [
      {
        data: [
          { value: props.stats?.urgent_count || 0, name: '紧急' },
          { value: props.stats?.important_count || 0, name: '重点关注' },
          { value: props.stats?.general_count || 0, name: '一般参考' },
          { value: props.stats?.noise_count || 0, name: '已处理噪音' },
        ],
      },
    ],
  })
}

watch(() => props.stats, updateChart, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => chart?.resize())
  chart?.dispose()
})
</script>

<style scoped>
.score-chart-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.chart {
  width: 100%;
  height: 300px;
}
</style>
