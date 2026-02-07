/**
 * Unit tests for auth store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

// Mock the API module
vi.mock('@/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
}))

// Mock import for guest store
vi.mock('@/stores/guest', () => ({
  useGuestStore: () => ({
    clearSession: vi.fn(),
    clearGuestToken: vi.fn()
  })
}))

describe('Auth Store', () => {
  beforeEach(() => {
    // Clear all mocks and storage
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()

    // Create new pinia instance for each test
    const pinia = createPinia()
    setActivePinia(pinia)
  })

  describe('initialization', () => {
    it('should initialize with empty state', () => {
      const authStore = useAuthStore()
      expect(authStore.token).toBe('')
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.isGuest).toBe(false)
    })

    it('should read from sessionStorage first', () => {
      // Set storage BEFORE creating store
      sessionStorage.setItem('token', 'session_token_123')
      sessionStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }))

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      expect(authStore.token).toBe('session_token_123')
      expect(authStore.user).toEqual({ id: 1, username: 'test' })
    })

    it('should fallback to localStorage if sessionStorage is empty', () => {
      // Set storage BEFORE creating store
      localStorage.setItem('token', 'local_token_456')
      localStorage.setItem('user', JSON.stringify({ id: 2, username: 'local' }))

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      expect(authStore.token).toBe('local_token_456')
      expect(authStore.user).toEqual({ id: 2, username: 'local' })
    })
  })

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            user: { id: 1, username: 'testuser', nickname: 'Test User' },
            access_token: 'login_token_789'
          }
        }
      }
      api.post.mockResolvedValue(mockResponse)

      const authStore = useAuthStore()
      const result = await authStore.login('testuser', 'password123')

      expect(result.success).toBe(true)
      expect(authStore.token).toBe('login_token_789')
      expect(authStore.user).toEqual({ id: 1, username: 'testuser', nickname: 'Test User' })
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('should store token in sessionStorage when rememberMe is false', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            user: { id: 1, username: 'testuser' },
            access_token: 'session_token'
          }
        }
      }
      api.post.mockResolvedValue(mockResponse)

      const authStore = useAuthStore()
      await authStore.login('testuser', 'password', false)

      expect(sessionStorage.getItem('token')).toBe('session_token')
      expect(localStorage.getItem('token')).toBeNull()
    })

    it('should store token in localStorage when rememberMe is true', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            user: { id: 1, username: 'testuser' },
            access_token: 'local_token'
          }
        }
      }
      api.post.mockResolvedValue(mockResponse)

      const authStore = useAuthStore()
      await authStore.login('testuser', 'password', true)

      expect(localStorage.getItem('token')).toBe('local_token')
      expect(sessionStorage.getItem('token')).toBeNull()
    })

    it('should handle login failure', async () => {
      const mockResponse = {
        data: {
          code: 1001,
          message: '用户名或密码错误'
        }
      }
      api.post.mockResolvedValue(mockResponse)

      const authStore = useAuthStore()
      const result = await authStore.login('wronguser', 'wrongpass')

      expect(result.success).toBe(false)
      expect(result.message).toBe('用户名或密码错误')
    })
  })

  describe('register', () => {
    it('should successfully register and auto-login', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            user: { id: 1, username: 'newuser', nickname: 'New User' },
            access_token: 'register_token'
          }
        }
      }
      api.post.mockResolvedValue(mockResponse)

      const authStore = useAuthStore()
      const result = await authStore.register('newuser', 'password123', 'New User')

      expect(result.success).toBe(true)
      expect(authStore.token).toBe('register_token')
      expect(authStore.user).toEqual({ id: 1, username: 'newuser', nickname: 'New User' })
    })
  })

  describe('logout', () => {
    it('should clear user data and tokens', async () => {
      // Setup logged in state
      sessionStorage.setItem('token', 'test_token')
      sessionStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }))

      // Create fresh pinia and store with logged in state
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      // Verify logged in
      expect(authStore.isAuthenticated).toBe(true)

      // Logout
      authStore.logout()

      expect(authStore.token).toBe('')
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(sessionStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  describe('setUser', () => {
    it('should set user data with rememberMe=true', () => {
      const authStore = useAuthStore()
      const userData = { id: 1, username: 'test', nickname: 'Test' }

      authStore.setUser(userData, 'test_token', true)

      expect(authStore.user).toEqual(userData)
      expect(authStore.token).toBe('test_token')
      expect(localStorage.getItem('token')).toBe('test_token')
      expect(localStorage.getItem('user')).toBe(JSON.stringify(userData))
    })

    it('should set user data with rememberMe=false', () => {
      const authStore = useAuthStore()
      const userData = { id: 1, username: 'test', nickname: 'Test' }

      authStore.setUser(userData, 'test_token', false)

      expect(authStore.user).toEqual(userData)
      expect(authStore.token).toBe('test_token')
      expect(sessionStorage.getItem('token')).toBe('test_token')
      expect(sessionStorage.getItem('user')).toBe(JSON.stringify(userData))
    })

    it('should clear guest token when setting user', () => {
      localStorage.setItem('guest_token', 'guest_123')

      const authStore = useAuthStore()
      authStore.setUser({ id: 1, username: 'test' }, 'user_token', true)

      expect(localStorage.getItem('guest_token')).toBeNull()
    })
  })

  describe('isGuest', () => {
    it('should return true when in guest mode', () => {
      localStorage.setItem('guest_token', 'guest_123')
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'guest_abc123' }))

      // Create fresh pinia and store with guest state
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      expect(authStore.isGuest).toBe(true)
    })

    it('should return false when logged in with regular account', () => {
      localStorage.setItem('token', 'regular_token')
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'regularuser' }))

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      expect(authStore.isGuest).toBe(false)
    })
  })

  describe('fetchProfile', () => {
    it('should fetch and update user profile', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            id: 1,
            username: 'testuser',
            nickname: 'Updated Name',
            quota: { basic: { total: 10, used: 2 } }
          }
        }
      }
      api.get.mockResolvedValue(mockResponse)

      // Set initial state
      sessionStorage.setItem('token', 'test_token')
      sessionStorage.setItem('user', JSON.stringify({ id: 1, username: 'testuser' }))

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      const profile = await authStore.fetchProfile()

      expect(profile).toEqual(mockResponse.data.data)
      expect(authStore.user).toEqual(mockResponse.data.data)
    })
  })

  describe('initGuestSession', () => {
    it('should return existing guest session if available', async () => {
      const existingToken = 'existing_guest_token'
      const existingUser = { id: 1, username: 'guest_abc123' }

      localStorage.setItem('guest_token', existingToken)
      localStorage.setItem('user', JSON.stringify(existingUser))

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      const result = await authStore.initGuestSession()

      expect(result.success).toBe(true)
      expect(result.hasExisting).toBe(true)
      expect(authStore.token).toBe(existingToken)
    })

    it('should create new guest session if none exists', async () => {
      const mockResponse = {
        data: {
          code: 200,
          data: {
            access_token: 'new_guest_token',
            user: { id: 1, username: 'guest_xyz789' }
          }
        }
      }
      api.post.mockResolvedValue(mockResponse)

      // Create fresh pinia and store
      const pinia = createPinia()
      setActivePinia(pinia)
      const authStore = useAuthStore()

      const result = await authStore.initGuestSession()

      expect(result.success).toBe(true)
      expect(result.hasExisting).toBe(false)
      expect(authStore.token).toBe('new_guest_token')
      // After initGuestSession, isGuest should be true because:
      // 1. guest_token is set in localStorage
      // 2. current token equals guest_token
      // 3. no regular token in localStorage or sessionStorage
      expect(authStore.isGuest).toBe(true)
    })
  })
})
