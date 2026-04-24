import { ElMessage } from 'element-plus'
import { ref } from 'vue'

export const useNewsFilter = () => {
  const filterType = ref('')
  const timeRange = ref('3d')
  const sortBy = ref('final_score')

  const handleFilterChange = () => {
    // 触发筛选变化
  }

  const resetFilters = () => {
    filterType.value = ''
    timeRange.value = '3d'
    sortBy.value = 'final_score'
  }

  return {
    filterType,
    timeRange,
    sortBy,
    handleFilterChange,
    resetFilters,
  }
}
