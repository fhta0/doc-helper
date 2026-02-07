<template>
  <NavBar />
  <main class="pt-20 min-h-screen">
    <router-view />
  </main>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import NavBar from '@/components/NavBar.vue'

const authStore = useAuthStore()

// 应用启动时的初始化逻辑
onMounted(async () => {
  // 检查是否有已存储的 token（正式用户或游客）
  const hasToken = authStore.isAuthenticated

  if (hasToken) {
    // 有 token，尝试验证是否有效
    try {
      await authStore.fetchProfile()
    } catch (error) {
      // token 无效，清除所有认证信息
      authStore.clearUser()
      // 同时清除游客 token
      localStorage.removeItem('guest_token')
      localStorage.removeItem('guest_session')
    }
  }
  // 注意：不再自动初始化游客会话
  // 游客模式应该在用户首次上传文件检测时才初始化
})
</script>

<style>
/* Global styles are defined in index.css */
</style>
