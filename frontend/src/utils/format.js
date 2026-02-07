import dayjs from 'dayjs'

// 格式化为 "MM-DD HH:mm"
export const formatTimeShort = (time) => {
  if (!time) return ''
  return dayjs(time).format('MM-DD HH:mm')
}

// 格式化为 "YYYY-MM-DD HH:mm"
export const formatTimeFull = (time) => {
  if (!time) return ''
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 格式化文件大小
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 根据问题数计算分数
export const calculateScore = (issues) => {
  if (issues === 0) return 100
  // Simple scoring logic: deduct 5 points per issue, min 60
  return Math.max(60, 100 - issues * 5)
}

// 获取分数颜色样式
export const getScoreColorClass = (issues) => {
  const score = calculateScore(issues)
  if (score >= 90) return 'text-green-600'
  if (score >= 80) return 'text-blue-600'
  if (score >= 60) return 'text-orange-600'
  return 'text-red-600'
}