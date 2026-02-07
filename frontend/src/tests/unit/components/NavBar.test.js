/**
 * Unit tests for NavBar component
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import { useAuthStore } from '@/stores/auth'

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', () => ({
  User: { template: '<div data-testid="user-icon"></div>' },
  LogOut: { template: '<div data-testid="logout-icon"></div>' }
}))

// Mock UserCenterModal
vi.mock('@/components/UserCenterModal.vue', () => ({
  default: {
    name: 'UserCenterModal',
    props: ['modelValue'],
    template: '<div v-if="modelValue" data-testid="user-center-modal">User Center</div>'
  }
}))

describe('NavBar Component', () => {
  let router
  let pinia

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()

    // Create router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/dashboard', component: { template: '<div>Dashboard</div>' } },
        { path: '/rules', component: { template: '<div>Rules</div>' } },
        { path: '/pricing', component: { template: '<div>Pricing</div>' } },
        { path: '/login', component: { template: '<div>Login</div>' } }
      ]
    })

    // Create pinia
    pinia = createPinia()
    setActivePinia(pinia)
  })

  const mountNavBar = (options = {}) => {
    return mount(NavBar, {
      global: {
        plugins: [router, pinia]
      },
      ...options
    })
  }

  describe('rendering', () => {
    it('should render navigation menu items', () => {
      const wrapper = mountNavBar()

      expect(wrapper.text()).toContain('首页')
      expect(wrapper.text()).toContain('控制台')
      expect(wrapper.text()).toContain('模板中心')
      expect(wrapper.text()).toContain('检测包')
    })

    it('should render brand name and logo', () => {
      const wrapper = mountNavBar()

      expect(wrapper.text()).toContain('文心雕龙·AI')
      expect(wrapper.text()).toContain('DOCUMENT AI')
      expect(wrapper.find('.text-white.font-heading').text()).toBe('文')
    })

    it('should show login button when not authenticated', () => {
      const wrapper = mountNavBar()

      expect(wrapper.text()).toContain('登录 / 注册')
    })
  })

  describe('authenticated user', () => {
    beforeEach(() => {
      // Clear and create fresh pinia for each test
      vi.clearAllMocks()
      localStorage.clear()
      sessionStorage.clear()

      const freshPinia = createPinia()
      setActivePinia(freshPinia)

      // Set up authenticated state
      const authStore = useAuthStore()
      authStore.setUser({ id: 1, username: 'testuser', nickname: 'Test User' }, 'test_token', false)
    })

    it('should show user avatar when authenticated', () => {
      const wrapper = mountNavBar()

      expect(wrapper.text()).toContain('T') // First letter of username
      expect(wrapper.text()).not.toContain('登录 / 注册')
    })

    it('should show user menu when avatar is clicked', async () => {
      const wrapper = mountNavBar()

      // Find and click the avatar button
      const avatarButton = wrapper.find('.rounded.bg-gradient-to-br')
      await avatarButton.trigger('click')

      expect(wrapper.text()).toContain('个人中心')
      expect(wrapper.text()).toContain('退出登录')
    })
  })

  describe('navigation', () => {
    it('should navigate to home when logo is clicked', async () => {
      const wrapper = mountNavBar()
      const logo = wrapper.find('.cursor-pointer.group')

      await logo.trigger('click')

      expect(router.currentRoute.value.path).toBe('/')
    })

    it('should highlight active menu item', async () => {
      await router.push('/dashboard')
      const wrapper = mountNavBar()

      // Check if dashboard menu item is highlighted
      const menuItems = wrapper.findAll('a')
      const dashboardItem = menuItems.find(item => item.text().includes('控制台'))

      // Active item should have active classes
      expect(dashboardItem.classes()).toContain('text-[#c8102e]')
    })

    it('should redirect to login when guest tries to access dashboard', async () => {
      // Create fresh pinia
      const freshPinia = createPinia()
      setActivePinia(freshPinia)

      const authStore = useAuthStore()

      // Set up guest mode
      authStore.setUser({ id: 1, username: 'guest_abc123' }, 'guest_token', true)
      localStorage.setItem('guest_token', 'guest_token')

      const wrapper = mountNavBar()

      // Find dashboard menu item and click
      const menuItems = wrapper.findAll('a')
      const dashboardItem = menuItems.find(item => item.text().includes('控制台'))

      await dashboardItem.trigger('click')

      expect(router.currentRoute.value.path).toBe('/login')
    })
  })

  describe('user actions', () => {
    beforeEach(() => {
      // Clear and create fresh pinia for each test
      vi.clearAllMocks()
      localStorage.clear()
      sessionStorage.clear()

      const freshPinia = createPinia()
      setActivePinia(freshPinia)

      const authStore = useAuthStore()
      authStore.setUser({ id: 1, username: 'testuser', nickname: 'Test User' }, 'test_token', false)
    })

    it('should open user center when profile is clicked', async () => {
      const wrapper = mountNavBar()

      // Open user menu
      const avatarButton = wrapper.find('.rounded.bg-gradient-to-br')
      await avatarButton.trigger('click')

      // Click profile button
      const profileButton = wrapper.findAll('button').find(btn => btn.text().includes('个人中心'))
      await profileButton.trigger('click')

      // Check if user center modal is shown
      expect(wrapper.find('[data-testid="user-center-modal"]').exists()).toBe(true)
    })

    it('should logout and redirect to login', async () => {
      const wrapper = mountNavBar()

      // Open user menu
      const avatarButton = wrapper.find('.rounded.bg-gradient-to-br')
      await avatarButton.trigger('click')

      // Click logout button
      const logoutButton = wrapper.findAll('button').find(btn => btn.text().includes('退出登录'))
      await logoutButton.trigger('click')

      // Check redirect
      expect(router.currentRoute.value.path).toBe('/login')

      // Check auth store is cleared
      const authStore = useAuthStore()
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('user initial calculation', () => {
    it('should display first letter of username in uppercase', () => {
      // Create fresh pinia
      const freshPinia = createPinia()
      setActivePinia(freshPinia)

      const authStore = useAuthStore()
      authStore.setUser({ id: 1, username: 'johnny' }, 'test_token', false)

      const wrapper = mountNavBar()

      expect(wrapper.find('.rounded.bg-gradient-to-br').text()).toBe('J')
    })

    it('should show U when username is not available', () => {
      // Create fresh pinia
      const freshPinia = createPinia()
      setActivePinia(freshPinia)

      const authStore = useAuthStore()
      authStore.setUser({ id: 1, username: '' }, 'test_token', false)

      const wrapper = mountNavBar()

      expect(wrapper.find('.rounded.bg-gradient-to-br').text()).toBe('U')
    })
  })
})
