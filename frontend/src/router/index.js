import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/rules',
    name: 'Rules',
    component: () => import('@/views/RulesView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/rules/new',
    name: 'NewRule',
    component: () => import('@/views/NewRuleView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/pricing',
    name: 'Pricing',
    component: () => import('@/views/PricingView.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 如果未登录且访问控制台或模板中心，需要登录
  if (!authStore.isAuthenticated && (to.path === '/dashboard' || to.path.startsWith('/rules'))) {
    next('/login')
    return
  }

  // Only protect routes that explicitly require authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated && !authStore.isGuest) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
