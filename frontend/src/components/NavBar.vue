<template>
  <nav class="fixed top-0 w-full z-50 glass-strong border-b border-amber-900/10">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center space-x-3 cursor-pointer group" @click="navigateTo('/')">
        <!-- 传统印章式 Logo -->
        <div class="relative">
          <div class="w-10 h-10 bg-gradient-to-br from-[#c8102e] to-[#9c0b22] rounded flex items-center justify-center shadow-md group-hover:shadow-lg transition-all">
            <span class="text-white font-heading font-bold text-lg">文</span>
          </div>
          <!-- 金色边框装饰 -->
          <div class="absolute inset-0 border border-[#b8860b]/30 rounded pointer-events-none"></div>
        </div>
        <!-- 品牌名称 - 使用衬线体 -->
        <div class="flex flex-col">
          <span class="text-lg font-heading font-bold text-[#1a1a1a] tracking-wide">文心雕龙·AI</span>
          <span class="text-[10px] text-[#6b6b6b] tracking-widest font-mono">DOCUMENT AI</span>
        </div>
      </div>

      <!-- Menu Items -->
      <div class="hidden md:flex items-center space-x-1">
        <a
          v-for="item in menuItems"
          :key="item.path"
          class="relative px-4 py-2 text-sm font-medium transition-all cursor-pointer rounded-lg"
          :class="currentPath === item.path ? 'text-[#c8102e] bg-[#e8d5d9]' : 'text-[#6b6b6b] hover:text-[#1a1a1a] hover:bg-[#faf8f3]'"
          @click="navigateTo(item.path)"
        >
          {{ item.label }}
          <!-- 活动状态下的小装饰 -->
          <span v-if="currentPath === item.path" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-[#c8102e] rounded-full"></span>
        </a>
      </div>

      <!-- Right Actions -->
      <div class="flex items-center space-x-3">
        <template v-if="authStore.isAuthenticated && !authStore.isGuest">
          <div class="flex items-center space-x-3">
            <!-- 用户头像 - 印章风格 -->
            <div class="relative" @click.stop="toggleUserMenu">
              <button class="w-10 h-10 rounded bg-gradient-to-br from-[#b8860b] to-[#d4a84b] flex items-center justify-center text-white font-heading font-bold cursor-pointer hover:opacity-90 transition-all shadow-md">
                {{ userInitial }}
              </button>
              <!-- 金色装饰框 -->
              <div class="absolute inset-0 -m-0.5 border border-[#b8860b]/40 rounded pointer-events-none"></div>

              <!-- 下拉菜单 -->
              <div
                v-if="showUserMenu"
                class="absolute right-0 mt-3 w-52 bg-[#fffbf5] rounded-xl shadow-xl border border-[#b8860b]/20 py-2 z-50 animate-scaleIn"
                style="box-shadow: 0 8px 32px rgba(26, 26, 26, 0.12);"
                @click.stop
              >
                <button
                  class="w-full px-4 py-2.5 text-left text-sm text-[#2d2d2d] hover:bg-[#f5edd7] flex items-center space-x-3 transition-colors"
                  @click="handleProfile"
                >
                  <div class="w-8 h-8 rounded bg-[#f5edd7] flex items-center justify-center">
                    <User class="w-4 h-4 text-[#b8860b]" />
                  </div>
                  <span class="font-medium">个人中心</span>
                </button>
                <button
                  class="w-full px-4 py-2.5 text-left text-sm text-[#c8102e] hover:bg-[#e8d5d9] flex items-center space-x-3 transition-colors"
                  @click="handleLogout"
                >
                  <div class="w-8 h-8 rounded bg-[#e8d5d9] flex items-center justify-center">
                    <LogOut class="w-4 h-4" />
                  </div>
                  <span class="font-medium">退出登录</span>
                </button>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <button
            class="bg-[#1a1a1a] text-white px-5 py-2.5 rounded-lg text-sm font-heading font-medium hover:bg-[#2d2d2d] transition-all shadow-md hover:shadow-lg"
            @click="navigateTo('/login')"
          >
            登录 / 注册
          </button>
        </template>
      </div>
    </div>

    <!-- User Center Modal -->
    <UserCenterModal v-model="showUserCenter" />
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, LogOut } from 'lucide-vue-next'
import UserCenterModal from './UserCenterModal.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const showUserMenu = ref(false)
const showUserCenter = ref(false)

const menuItems = [
  { path: '/', label: '首页' },
  { path: '/dashboard', label: '控制台' },
  { path: '/rules', label: '模板中心' },
  { path: '/pricing', label: '检测包' }
]

const currentPath = computed(() => route.path)

const userInitial = computed(() => {
  const username = authStore.user?.username
  return username ? username.charAt(0).toUpperCase() : 'U'
})

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleProfile = () => {
  showUserMenu.value = false
  showUserCenter.value = true
}

const handleLogout = () => {
  showUserMenu.value = false
  authStore.logout()
  router.push('/login')
}

const closeMenu = () => {
  showUserMenu.value = false
}

onMounted(() => {
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})

const navigateTo = (path) => {
  if ((path === '/dashboard' || path.startsWith('/rules')) && authStore.isGuest) {
    router.push('/login')
    return
  }
  if (route.path !== path) {
    router.push(path)
  }
}
</script>

<style scoped>
/* 确保玻璃态效果正确应用 */
.glass-strong {
  background: rgba(255, 251, 245, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(184, 134, 11, 0.15);
}
</style>
