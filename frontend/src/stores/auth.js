import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import { GUEST_TOKEN_KEY } from '@/constants/guest'

export const useAuthStore = defineStore('auth', () => {
  // 优先从 sessionStorage 读取，如果没有再从 localStorage 读取
  const token = ref(
    sessionStorage.getItem('token') ||
    localStorage.getItem('token') ||
    localStorage.getItem(GUEST_TOKEN_KEY) ||
    ''
  )
  const user = ref(
    JSON.parse(sessionStorage.getItem('user') || localStorage.getItem('user') || 'null')
  )

  // 判断是否为游客模式：token 来自 guest_token 且没有正式 token
  // 直接通过当前 token 与 guest_token 比较来判断，更可靠
  const isGuest = computed(() => {
    const guestToken = localStorage.getItem(GUEST_TOKEN_KEY)
    const regularToken = localStorage.getItem('token') || sessionStorage.getItem('token')
    // 如果有 guest_token，且当前 token 等于 guest_token，且没有正式 token，则是游客
    return !!(guestToken && token.value === guestToken && !regularToken)
  })

  const isAuthenticated = computed(() => !!token.value)

  const setUser = (userData, accessToken, rememberMe = false) => {
    user.value = userData
    token.value = accessToken

    // 根据记住我选择存储位置
    if (rememberMe) {
      localStorage.setItem('token', accessToken)
      localStorage.setItem('user', JSON.stringify(userData))
      // 清除 sessionStorage
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
    } else {
      sessionStorage.setItem('token', accessToken)
      sessionStorage.setItem('user', JSON.stringify(userData))
      // 清除 localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }

    // 立即清除游客 token，避免 isGuest 状态判断延迟
    localStorage.removeItem(GUEST_TOKEN_KEY)

    // Migrate guest data after successful login
    _migrateGuestData()
  }

  const clearUser = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    localStorage.removeItem(GUEST_TOKEN_KEY)
  }

  const login = async (username, password, rememberMe = false) => {
    // Get guest username if currently in guest mode
    // 修复：必须在调用 login 之前获取 guestUsername，因为 isGuest 可能会在登录过程中变化
    // 但更重要的是，isGuest 依赖于 token，而 token 在 login 之前是 guest token
    const currentIsGuest = isGuest.value
    const guestUsername = currentIsGuest && user.value?.username?.startsWith('guest_') ? user.value.username : null

    const response = await api.post('/api/auth/login', {
      username,
      password,
      guest_username: guestUsername
    })

    if (response.data.code === 200) {
      setUser(response.data.data.user, response.data.data.access_token, rememberMe)
      // 确保 token 已保存后再返回
      return { success: true }
    }
    return { success: false, message: response.data.message }
  }

  const logout = () => {
    clearUser()
  }

  const register = async (username, password, nickname) => {
    // Get guest username if currently in guest mode
    const currentIsGuest = isGuest.value
    const guestUsername = currentIsGuest && user.value?.username?.startsWith('guest_') ? user.value.username : null

    const response = await api.post('/api/auth/register', {
      username,
      password,
      nickname,
      guest_username: guestUsername
    })

    if (response.data.code === 200) {
      // Auto-login after registration
      setUser(response.data.data.user, response.data.data.access_token, false)
      return { success: true }
    }
    return { success: false, message: response.data.message }
  }

  const fetchProfile = async () => {
    const response = await api.get('/api/auth/user/profile')
    if (response.data.code === 200) {
      user.value = response.data.data
      // 使用当前 token 所在的存储位置
      const storage = localStorage.getItem('token') === token.value ? localStorage : sessionStorage
      storage.setItem('user', JSON.stringify(response.data.data))
      return response.data.data
    }
    return null
  }

  // Initialize guest session
  const initGuestSession = async () => {
    // Check if guest token already exists
    const existingGuestToken = localStorage.getItem(GUEST_TOKEN_KEY)
    if (existingGuestToken) {
      // Validate existing token by checking user data
      const existingUser = JSON.parse(localStorage.getItem('user') || 'null')
      // If user is a guest but username doesn't start with 'guest_', it's an old invalid token
      if (existingUser && existingUser.username && !existingUser.username.startsWith('guest_')) {
        // Invalid/corrupted guest data, clear and reinitialize
        localStorage.removeItem(GUEST_TOKEN_KEY)
        localStorage.removeItem('user')
      } else {
        token.value = existingGuestToken
        user.value = existingUser
        return { success: true, hasExisting: true }
      }
    }

    // Create new guest session
    try {
      const response = await api.post('/api/guest/init')
      if (response.data.code === 200) {
        const guestAccessToken = response.data.data.access_token
        const guestUser = response.data.data.user

        token.value = guestAccessToken
        user.value = guestUser

        localStorage.setItem(GUEST_TOKEN_KEY, guestAccessToken)
        localStorage.setItem('user', JSON.stringify(guestUser))

        return { success: true, hasExisting: false }
      }
      return { success: false, message: response.data.message }
    } catch (error) {
      console.error('Failed to initialize guest session:', error)
      return { success: false, message: '初始化游客会话失败' }
    }
  }

  // Private: Clean up guest session after login
  const _migrateGuestData = async () => {
    try {
      const { useGuestStore } = await import('./guest')
      const guestStore = useGuestStore()
      guestStore.clearSession()
      guestStore.clearGuestToken()
    } catch (error) {
      console.error('Failed to clean up guest session:', error)
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    isGuest,
    login,
    logout,
    register,
    fetchProfile,
    initGuestSession,
    setUser,
    clearUser
  }
})
