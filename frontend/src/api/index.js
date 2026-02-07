import axios from 'axios'
import { ElMessage } from 'element-plus'

// 如果设置了 VITE_API_URL，使用它；否则使用相对路径
// - 开发：相对路径由 Vite devServer 代理到后端
// - 生产：相对路径走同源，由 Nginx 把 /api/ 代理到 backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000
})

// Request interceptor - add auth token if available
api.interceptors.request.use(
  (config) => {
    // Try regular token from session/local storage first, then guest token
    const token = sessionStorage.getItem('token') || localStorage.getItem('token') || localStorage.getItem('guest_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      if (status === 401) {
        ElMessage.error({ message: '登录已过期，请重新登录', showClose: true })
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('guest_token')
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
        window.location.href = '/login'
      } else if (data?.message) {
        ElMessage.error({ message: data.message, showClose: true })
      } else {
        ElMessage.error({ message: '请求失败，请稍后重试', showClose: true })
      }
    } else {
      ElMessage.error({ message: '网络连接失败', showClose: true })
    }

    return Promise.reject(error)
  }
)

export default api

// API functions
export const checkApi = {
  upload: (file, checkType = 'basic') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('check_type', checkType)
    return api.post('/api/check/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  submit: (fileId, checkType = 'basic', filename = null, ruleTemplateId = null) => api.post('/api/check', {
    file_id: fileId,
    check_type: checkType,
    filename: filename,
    rule_template_id: ruleTemplateId
  }, {
    timeout: checkType === 'full' ? 180000 : 60000  // 全面检测3分钟，基础检测1分钟
  }),
  getResult: (checkId) => api.get(`/api/check/${checkId}`),
  generateRevised: (checkId) => api.post(`/api/check/${checkId}/revise`),
  getRecent: (limit = 5, offset = 0) => api.get('/api/check/recent', { params: { limit, offset } }),
  getStats: () => api.get('/api/check/stats')
}

export const purchaseApi = {
  getPackages: () => api.get('/api/purchase/packages'),
  createOrder: (data) => api.post('/api/purchase/order', data),
  queryOrder: (orderNo) => api.get(`/api/purchase/order/${orderNo}`),
  closeOrder: (orderNo) => api.post(`/api/purchase/order/${orderNo}/close`)
}

export const userApi = {
  getOrders: (page = 1, pageSize = 10) => api.get('/api/auth/user/orders', { params: { page, page_size: pageSize } })
}

export const ruleTemplateApi = {
  // 获取格式模板列表
  getTemplates: (templateType = null) => {
    const params = templateType ? { template_type: templateType } : {}
    return api.get('/api/rule-templates', { params })
  },
  // 获取单个格式模板
  getTemplate: (templateId) => api.get(`/api/rule-templates/${templateId}`),
  // 创建格式模板
  createTemplate: (name, description, config) => {
    return api.post('/api/rule-templates', { name, description, config })
  },
  // 更新格式模板
  updateTemplate: (templateId, name, description, config) => {
    return api.put(`/api/rule-templates/${templateId}`, { name, description, config })
  },
  // 删除格式模板
  deleteTemplate: (templateId) => api.delete(`/api/rule-templates/${templateId}`),
  // AI解析文本
  parseText: (text) => {
    return api.post('/api/rule-templates/parse/text', null, { params: { text } })
  },
  // 解析docx范文
  parseDocx: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/rule-templates/parse/docx', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
