<template>
  <div class="radar-chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface SubScores {
  importance?: number
  incremental?: number
  expectation?: number
  scope?: number
  source_confidence?: number
  market_reaction?: number
}

const props = defineProps<{
  scores: SubScores | null
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const scoreLabels: Record<string, string> = {
  importance: '重要性',
  incremental: '增量属性',
  expectation: '预期差',
  scope: '影响范围',
  source_confidence: '来源可信度',
  market_reaction: '行情反应',
}

const getChartData = () => {
  if (!props.scores) {
    return {
      indicators: Object.values(scoreLabels).map(name => ({ name, max: 100 })),
      values: [0, 0, 0, 0, 0, 0],
    }
  }

  const keys = Object.keys(scoreLabels)
  const indicators = keys.map(key => ({ name: scoreLabels[key], max: 100 }))
  const values = keys.map(key => props.scores[key] ?? 0)

  return { indicators, values }
}

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chart) return

  const { indicators, values } = getChartData()

  const option: echarts.EChartsOption = {
    title: {
      text: '多维度评分',
      left: 'center',
      top: 5,
      textStyle: {
        fontSize: 14,
        fontWeight: 600,
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}',
    },
    radar: {
      indicator: indicators,
      radius: '60%',
      splitNumber: 4,
      axisName: {
        color: '#666',
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: '#E8E8E8',
        },
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['#F8F8F8', '#F0F0F0', '#E8E8E8', '#E0E0E0'],
        },
      },
      axisLine: {
        lineStyle: {
          color: '#CCC',
        },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: '评分',
            areaStyle: {
              color: 'rgba(24, 144, 255, 0.3)',
            },
            lineStyle: {
              color: '#1890FF',
              width: 2,
            },
            itemStyle: {
              color: '#1890FF',
            },
            label: {
              show: true,
              formatter: '{c}',
              fontSize: 10,
            },
          },
        ],
      },
    ],
  }

  chart.setOption(option)
}

watch(() => props.scores, updateChart, { deep: true })

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
.radar-chart-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart {
  width: 100%;
  height: 280px;
}
</style>
