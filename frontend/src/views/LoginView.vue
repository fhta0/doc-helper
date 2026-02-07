<template>
  <div class="min-h-screen flex items-center justify-center px-6 animate-fadeIn">
    <!-- 背景装饰 - 传统纹样暗示 -->
    <div class="fixed top-1/4 -left-20 w-80 h-80 bg-gradient-to-br from-[#c8102e]/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>
    <div class="fixed bottom-1/4 -right-20 w-80 h-80 bg-gradient-to-bl from-[#b8860b]/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>

    <div class="glass-strong w-full max-w-md p-10 rounded-2xl shadow-xl border border-[#b8860b]/20 relative">
      <!-- 角落装饰 - 传统回纹暗示 -->
      <div class="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-[#b8860b]/30 rounded-tl-lg pointer-events-none"></div>
      <div class="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-[#b8860b]/30 rounded-tr-lg pointer-events-none"></div>
      <div class="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-[#b8860b]/30 rounded-bl-lg pointer-events-none"></div>
      <div class="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-[#b8860b]/30 rounded-br-lg pointer-events-none"></div>

      <!-- 标题区域 -->
      <div class="text-center mb-10">
        <!-- 印章式图标 -->
        <div class="w-16 h-16 bg-gradient-to-br from-[#c8102e] to-[#a00c24] rounded-lg flex items-center justify-center mx-auto mb-6 shadow-lg">
          <span class="text-white font-heading font-bold text-2xl">文</span>
        </div>
        <h2 class="font-heading text-3xl font-bold text-[#1a1a1a] mb-2">{{ isLogin ? '欢迎回来' : '创建新账号' }}</h2>
        <p class="text-[#6b6b6b]">{{ isLogin ? '请输入您的账号信息以访问控制台' : '加入文心雕龙，开启专业学术检测' }}</p>
      </div>

      <!-- 表单 -->
      <form class="space-y-5" @submit.prevent="handleSubmit">
        <!-- 用户名/邮箱 -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-[#2d2d2d] ml-1">用户名或邮箱</label>
          <input
            v-model="form.username"
            type="text"
            class="w-full px-5 py-3.5 bg-[#faf8f3] border-2 border-[#b8860b]/20 rounded-lg focus:ring-0 focus:border-[#b8860b] outline-none transition-all text-[#1a1a1a] placeholder-[#9a9a9a]"
            placeholder="name@example.com"
            required
          />
        </div>

        <!-- 密码 -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-[#2d2d2d] ml-1">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="w-full px-5 py-3.5 bg-[#faf8f3] border-2 border-[#b8860b]/20 rounded-lg focus:ring-0 focus:border-[#b8860b] outline-none transition-all text-[#1a1a1a] placeholder-[#9a9a9a]"
            placeholder="••••••••"
            required
          />
        </div>

        <!-- 确认密码 (仅注册时显示) -->
        <div v-if="!isLogin" class="space-y-2">
          <label class="block text-sm font-medium text-[#2d2d2d] ml-1">确认密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            class="w-full px-5 py-3.5 bg-[#faf8f3] border-2 border-[#b8860b]/20 rounded-lg focus:ring-0 focus:border-[#b8860b] outline-none transition-all text-[#1a1a1a] placeholder-[#9a9a9a]"
            placeholder="••••••••"
          />
        </div>

        <!-- 昵称 (仅注册时显示) -->
        <div v-if="!isLogin" class="space-y-2">
          <label class="block text-sm font-medium text-[#2d2d2d] ml-1">昵称（可选）</label>
          <input
            v-model="form.nickname"
            type="text"
            class="w-full px-5 py-3.5 bg-[#faf8f3] border-2 border-[#b8860b]/20 rounded-lg focus:ring-0 focus:border-[#b8860b] outline-none transition-all text-[#1a1a1a] placeholder-[#9a9a9a]"
            placeholder="请输入昵称"
          />
        </div>

        <!-- 登录时的额外选项 -->
        <div v-if="isLogin" class="flex items-center justify-between text-sm px-1">
          <label class="flex items-center space-x-2 cursor-pointer group">
            <div class="relative">
              <input
                v-model="form.rememberMe"
                type="checkbox"
                class="sr-only"
              />
              <div class="w-5 h-5 border-2 border-[#b8860b]/30 rounded transition-all group-hover:border-[#b8860b]/50"
                   :class="form.rememberMe ? 'bg-[#b8860b] border-[#b8860b]' : ''">
                <svg v-if="form.rememberMe" class="w-3 h-3 text-white absolute top-1 left-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <span class="text-[#6b6b6b]">记住我</span>
          </label>
          <a class="text-[#c8102e] font-medium hover:underline" href="#">忘记密码？</a>
        </div>

        <!-- 提交按钮 -->
        <button
          type="submit"
          class="w-full bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-4 rounded-lg font-heading font-bold text-lg hover:shadow-xl transition-all shadow-lg hover:-translate-y-0.5 flex items-center justify-center space-x-2"
          :disabled="loading"
        >
          <svg v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ isLogin ? '登录' : '注册' }}</span>
        </button>
      </form>

      <!-- 切换登录/注册 -->
      <div class="mt-8 text-center text-sm text-[#6b6b6b] pt-6 border-t border-[#b8860b]/10">
        <span>{{ isLogin ? '没有账号？' : '已经有账号？' }}</span>
        <button
          class="text-[#c8102e] font-heading font-bold hover:underline ml-1"
          @click="toggleMode"
        >
          {{ isLogin ? '立即注册' : '立即登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const loading = ref(false)

const form = reactive({
  username: localStorage.getItem('remembered_username') || '',
  password: '',
  confirmPassword: '',
  nickname: '',
  rememberMe: !!localStorage.getItem('remembered_username')
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  form.nickname = ''
  form.rememberMe = false
}

const handleSubmit = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning({ message: '请填写所有必填项', showClose: true })
    return
  }

  if (!isLogin.value) {
    if (form.password.length < 6) {
      ElMessage.warning({ message: '密码至少需要6个字符', showClose: true })
      return
    }
    if (form.password !== form.confirmPassword) {
      ElMessage.warning({ message: '两次输入的密码不一致', showClose: true })
      return
    }
  }

  loading.value = true
  try {
    if (isLogin.value) {
      const result = await authStore.login(form.username, form.password, form.rememberMe)
      if (result.success) {
        if (form.rememberMe) {
          localStorage.setItem('remembered_username', form.username)
        } else {
          localStorage.removeItem('remembered_username')
        }
        ElMessage.success({ message: '登录成功', showClose: true })
        router.push('/dashboard')
      } else {
        ElMessage.error({ message: result.message || '登录失败', showClose: true })
      }
    } else {
      const result = await authStore.register(
        form.username,
        form.password,
        form.nickname
      )
      if (result.success) {
        ElMessage.success({ message: '注册成功', showClose: true })
        router.push('/dashboard')
      } else {
        ElMessage.error({ message: result.message || '注册失败', showClose: true })
      }
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.5s ease-out forwards;
}

/* 玻璃态效果 */
.glass-strong {
  background: rgba(255, 251, 245, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(184, 134, 11, 0.2);
}
</style>
