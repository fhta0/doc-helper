<template>
  <div class="relative min-h-screen flex flex-col items-center px-6 py-12 overflow-hidden">
    <!-- 传统装饰背景 - 祥云纹样暗示 -->
    <div class="absolute top-1/4 -left-32 w-96 h-96 bg-gradient-to-br from-[#c8102e]/8 to-transparent rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-gradient-to-bl from-[#b8860b]/8 to-transparent rounded-full blur-3xl pointer-events-none"></div>

    <!-- 主内容区 -->
    <div class="w-full flex flex-col items-center space-y-8 max-w-4xl relative z-10">
      <!-- 标题和特性区域 -->
      <div class="text-center space-y-8 max-w-3xl w-full animate-fadeIn">

        <!-- 主标题 - 书法风格 -->
        <div class="space-y-4">
          <h1 class="font-heading text-4xl md:text-5xl font-bold text-[#1a1a1a] leading-tight">
            文档格式检查
            <span class="text-gradient">智能修正</span>
          </h1>
          <p class="text-[#6b6b6b] text-lg font-light">
            融合传统学术规范与现代 AI 技术
          </p>
        </div>

        <!-- 特性标签 - 印章风格 -->
        <div class="flex flex-wrap justify-center gap-3">
          <div
            v-for="feature in features"
            :key="feature.label"
            class="flex items-center space-x-2 px-4 py-2.5 rounded-lg border transition-all hover:shadow-md"
            :class="feature.borderClass"
            :style="{ backgroundColor: feature.bgColor, borderColor: feature.borderColor }"
          >
            <component :is="feature.icon" class="w-5 h-5" :class="feature.iconColor" />
            <span class="text-sm font-medium" :class="feature.textColor">{{ feature.label }}</span>
          </div>
        </div>
      </div>

      <!-- 上传区域 / 快捷工作面板 -->
      <transition
        mode="out-in"
        enter-active-class="transition-all duration-500 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-300 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <!-- 游客或未登录 - 大文件上传区 -->
        <div v-if="!authStore.isAuthenticated || authStore.isGuest" key="upload" class="flex justify-center w-full">
          <!-- 检测中状态 -->
          <div v-if="checking" class="w-full max-w-2xl glass-strong p-12 rounded-2xl text-center space-y-6 border-2 border-[#b8860b]/20">
            <div class="relative w-20 h-20 mx-auto">
              <!-- 传统风格加载器 - 模拟太极 -->
              <div class="absolute inset-0 border-4 border-[#f5edd7] rounded-full"></div>
              <div class="absolute inset-0 border-4 border-transparent border-t-[#c8102e] rounded-full animate-spin"></div>
              <div class="absolute inset-2 border-4 border-transparent border-r-[#b8860b] rounded-full animate-spin" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
            </div>
            <h3 class="font-heading text-xl font-bold text-[#1a1a1a]">正在检查文档格式...</h3>
            <p class="text-[#6b6b6b]">请稍候，这可能需要几秒钟</p>
            <div class="max-w-md mx-auto">
              <div class="w-full bg-[#f5edd7] h-2 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-[#c8102e] to-[#b8860b]" :style="{ width: progress + '%' }"></div>
              </div>
              <p class="text-sm text-[#6b6b6b] mt-2 font-mono">{{ progress }}%</p>
            </div>
          </div>

          <!-- 试用次数用完 - 引导登录卡片 -->
          <div
            v-else-if="authStore.isGuest && !guestStore.hasTrialsRemaining"
            class="w-full max-w-2xl glass-strong p-12 rounded-2xl text-center space-y-6 border-2 border-[#b8860b]/30"
          >
            <div class="w-20 h-20 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto">
              <Lock class="w-10 h-10 text-[#b8860b]" />
            </div>
            <div class="space-y-2">
              <h4 class="font-heading text-2xl font-bold text-[#1a1a1a]">试用次数已用完</h4>
              <p class="text-[#6b6b6b]">登录后可享受更多功能</p>
            </div>
            <ul class="text-left text-[#4a4a4d] space-y-3 max-w-sm mx-auto">
              <li v-for="benefit in loginBenefits" :key="benefit" class="flex items-center">
                <div class="w-5 h-5 rounded-full bg-[#d7e8e3] flex items-center justify-center mr-3 flex-shrink-0">
                  <CheckCircle2 class="w-3 h-3 text-[#2d5a4a]" />
                </div>
                <span class="text-sm">{{ benefit }}</span>
              </li>
            </ul>
            <button
              @click="router.push('/login')"
              class="bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white px-10 py-4 rounded-xl font-heading font-bold text-lg hover:shadow-xl transition-all shadow-lg hover:-translate-y-0.5"
            >
              立即登录
            </button>
          </div>

          <!-- 上传区域 -->
          <div
            v-else
            @click="handleFileSelect"
            class="w-full max-w-2xl glass-strong p-12 rounded-2xl border-2 border-dashed transition-all cursor-pointer group"
            :class="isDragging ? 'border-[#c8102e] bg-[#e8d5d9]/30' : 'border-[#b8860b]/40 hover:border-[#b8860b] hover:bg-[#f5edd7]/20'"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
          >
            <div class="w-20 h-20 bg-[#f5edd7] rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-105 transition-transform">
              <Upload class="w-10 h-10 text-[#b8860b]" />
            </div>
            <div class="space-y-3 text-center">
              <h4 class="font-heading text-xl font-bold text-[#1a1a1a]">拖拽文档到此处，或点击上传</h4>
              <p class="text-[#6b6b6b]">支持 .docx 格式，文件大小不超过 10MB</p>
              <p v-if="authStore.isGuest" class="text-sm text-[#c8102e] font-medium px-4 py-2 bg-[#e8d5d9]/50 rounded-lg inline-block">
                游客可试用 {{ guestStore.remainingTrials }} 次
              </p>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              class="hidden"
              accept=".docx"
              @change="handleFileChange"
            />
          </div>
        </div>

        <!-- 已登录 - 快捷工作面板 -->
        <div v-else key="dashboard" class="glass-strong rounded-2xl p-10 shadow-xl border border-[#b8860b]/20 w-full max-w-lg">
          <!-- 用户头像和欢迎词 -->
          <div class="flex flex-col items-center space-y-4 text-center">
            <div class="relative">
              <div class="w-20 h-20 rounded bg-gradient-to-br from-[#b8860b] to-[#d4a84b] flex items-center justify-center text-white text-3xl font-heading font-bold shadow-lg">
                {{ userInitial }}
              </div>
              <!-- 装饰性边框 -->
              <div class="absolute inset-0 -m-1 border-2 border-[#b8860b]/30 rounded"></div>
            </div>
            <div>
              <h2 class="font-heading text-2xl font-bold text-[#1a1a1a]">
                欢迎回来，{{ displayName }}
              </h2>
              <p class="text-[#6b6b6b] mt-2">准备好开始今天的文档检查了吗？</p>
            </div>
          </div>

          <!-- 额度统计条 -->
          <div class="space-y-4 pt-6">
            <!-- 免费额度 -->
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-[#6b6b6b]">本月免费额度</span>
                <span class="font-medium text-[#1a1a1a]">{{ monthlyFreeUsed }}/{{ monthlyFreeTotal }}</span>
              </div>
              <div class="w-full bg-[#f5edd7] h-2 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all bg-gradient-to-r from-[#c8102e] to-[#b8860b]" :style="{ width: monthlyFreeProgress + '%' }"></div>
              </div>
            </div>

            <!-- 基础检测 -->
            <div class="flex items-center justify-between p-3 bg-[#faf8f3] rounded-lg border border-[#b8860b]/10">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-[#f5edd7] flex items-center justify-center">
                  <FileText class="w-5 h-5 text-[#b8860b]" />
                </div>
                <div>
                  <p class="text-sm font-medium text-[#1a1a1a]">基础检测</p>
                  <p class="text-xs text-[#6b6b6b]">格式规范检查</p>
                </div>
              </div>
              <span class="text-lg font-bold font-heading text-[#b8860b]">{{ authStore.user?.basic_count || 0 }}</span>
            </div>

            <!-- 完整检测 -->
            <div class="flex items-center justify-between p-3 bg-[#faf8f3] rounded-lg border border-[#c8102e]/10">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-[#e8d5d9] flex items-center justify-center">
                  <Wand2 class="w-5 h-5 text-[#c8102e]" />
                </div>
                <div>
                  <p class="text-sm font-medium text-[#1a1a1a]">AI完整检测</p>
                  <p class="text-xs text-[#6b6b6b]">深度内容分析</p>
                </div>
              </div>
              <span class="text-lg font-bold font-heading text-[#c8102e]">{{ authStore.user?.full_count || 0 }}</span>
            </div>
          </div>

          <!-- 进入控制台按钮 -->
          <div class="flex justify-center pt-6">
            <button
              @click="goToDashboard"
              class="w-full max-w-xs bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-4 rounded-xl font-heading font-bold hover:shadow-xl transition-all shadow-lg hover:-translate-y-0.5 flex items-center justify-center space-x-2"
            >
              <LayoutDashboard class="w-5 h-5" />
              <span>进入控制台</span>
            </button>
          </div>
        </div>
      </transition>

      <!-- 游客历史记录列表 -->
      <div v-if="showGuestHistory" class="w-full max-w-3xl animate-slideInLeft">
        <GuestHistoryList />
      </div>

      <!-- 功能特性卡片 - 传统风格 -->
      <div class="w-full grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="card in featureCards"
          :key="card.title"
          class="glass-strong p-6 rounded-xl text-left space-y-4 border border-[#b8860b]/10 bento-card group"
        >
          <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="card.iconBg">
            <component :is="card.icon" class="w-6 h-6" :class="card.iconColor" />
          </div>
          <div>
            <h3 class="font-heading font-bold text-lg text-[#1a1a1a]">{{ card.title }}</h3>
            <p class="text-sm text-[#6b6b6b] mt-2 leading-relaxed">{{ card.description }}</p>
          </div>
          <!-- 装饰性角标 -->
          <div class="absolute top-4 right-4 w-2 h-2 rounded-full" :class="card.dotColor"></div>
        </div>
      </div>
    </div>

    <!-- 底部声明 -->
    <footer class="py-12 text-center space-y-2 mt-auto">
      <p class="text-[#6b6b6b] text-sm">© 2026 文心雕龙·AI</p>
      <p class="text-[#9a9a9a] text-xs">京ICP备16016549号-1</p>
    </footer>

    <!-- 游客试用弹窗 -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showGuestModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20" @click.self="showGuestModal = false">
        <div class="glass-strong rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-[#b8860b]/20">
          <div class="p-8 text-center space-y-6">
            <div class="w-16 h-16 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto">
              <User class="w-8 h-8 text-[#b8860b]" />
            </div>

            <!-- 未登录用户 -->
            <template v-if="!authStore.isAuthenticated">
              <h3 class="font-heading text-2xl font-bold text-[#1a1a1a]">欢迎使用</h3>
              <p class="text-[#6b6b6b]">您可以选择以下方式开始使用：</p>
              <div class="flex flex-col gap-3">
                <button
                  @click="continueAsGuest"
                  class="w-full bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-3 rounded-xl font-heading font-bold hover:shadow-lg transition-all"
                >
                  游客试用（{{ guestStore.remainingTrials }}次免费）
                </button>
                <button
                  @click="goToLogin"
                  class="w-full border-2 border-[#b8860b] text-[#1a1a1a] py-3 rounded-xl font-heading font-bold hover:bg-[#f5edd7] transition-all"
                >
                  登录 / 注册
                </button>
              </div>
            </template>

            <!-- 已是游客，但次数用完 -->
            <template v-else>
              <h3 class="font-heading text-2xl font-bold text-[#1a1a1a]">游客试用次数已用完</h3>
              <p class="text-[#6b6b6b]">登录后可获得每月 3 次免费额度，并解锁 AI 深度检查功能</p>
              <button
                @click="goToLogin"
                class="w-full bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-3 rounded-xl font-heading font-bold hover:shadow-lg transition-all"
              >
                立即登录
              </button>
            </template>

            <button
              @click="showGuestModal = false"
              class="w-full text-[#9a9a9a] py-2 text-sm hover:text-[#6b6b6b] transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGuestStore } from '@/stores/guest'
import { ElMessage } from 'element-plus'
import { checkApi } from '@/api'
import GuestHistoryList from '@/components/GuestHistoryList.vue'
import {
  CheckCircle2,
  ShieldCheck,
  Zap,
  FileText,
  Brain,
  Download,
  Wand2,
  LayoutDashboard,
  Upload,
  User,
  Lock
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const guestStore = useGuestStore()

// 本地状态控制游客历史记录显示
const showGuestHistory = ref(false)

// 监听游客历史记录变化
watch(
  () => guestStore.history?.length || 0,
  (newLength) => {
    const shouldShow = authStore.isGuest && newLength > 0
    showGuestHistory.value = shouldShow
  },
  { immediate: true }
)

// 状态
const isDragging = ref(false)
const fileInputRef = ref(null)
const showGuestModal = ref(false)
const pendingFile = ref(null)
const checking = ref(false)
const progress = ref(0)

// 配置数据
const features = [
  {
    label: '格式检查',
    icon: CheckCircle2,
    bgColor: '#d7e8e3',
    borderColor: '#2d5a4a',
    textColor: 'text-[#2d5a4a]',
    iconColor: 'text-[#2d5a4a]'
  },
  {
    label: '智能纠错',
    icon: ShieldCheck,
    bgColor: '#e0e8f0',
    borderColor: '#3d5a80',
    textColor: 'text-[#3d5a80]',
    iconColor: 'text-[#3d5a80]'
  },
  {
    label: '逻辑优化',
    icon: Zap,
    bgColor: '#f5edd7',
    borderColor: '#b8860b',
    textColor: 'text-[#b8860b]',
    iconColor: 'text-[#b8860b]'
  }
]

const loginBenefits = [
  '永久保存检查记录',
  '解锁历史记录管理',
  '每月 3 次免费基础检测'
]

const featureCards = [
  {
    title: '全格式支持',
    description: '支持 Word 和 WPS 主流办公文档格式，一键上传即可开始检测。',
    icon: FileText,
    iconBg: 'bg-[#d7e8e3]',
    iconColor: 'text-[#2d5a4a]',
    dotColor: 'bg-[#2d5a4a]'
  },
  {
    title: 'AI 智能分析',
    description: '基于大模型技术，精准识别文档中的层级结构与样式格式错误。',
    icon: Brain,
    iconBg: 'bg-[#e8d5d9]',
    iconColor: 'text-[#c8102e]',
    dotColor: 'bg-[#c8102e]'
  },
  {
    title: '一键导出报告',
    description: '自动生成标准修改建议报告，详细标注问题位置，助你快速完成格式修正。',
    icon: Download,
    iconBg: 'bg-[#f5edd7]',
    iconColor: 'text-[#b8860b]',
    dotColor: 'bg-[#b8860b]'
  }
]

const monthlyFreeTotal = ref(3)

// 计算属性
const userInitial = computed(() => {
  const username = authStore.user?.username
  return username ? username.charAt(0).toUpperCase() : 'U'
})

const displayName = computed(() => {
  return authStore.user?.username || '用户'
})

const monthlyFreeUsed = computed(() => {
  const freeCount = authStore.user?.free_count || 0
  return Math.max(0, Math.min(3, 3 - freeCount))
})

const monthlyFreeProgress = computed(() => {
  return (monthlyFreeUsed.value / monthlyFreeTotal.value) * 100
})

// 初始化时获取用户信息
onMounted(async () => {
  if (authStore.isAuthenticated) {
    await authStore.fetchProfile()
  }
})

// 文件上传相关方法
const handleFileSelect = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    validateAndSelectFile(file)
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) {
    validateAndSelectFile(file)
  }
}

const validateAndSelectFile = (file) => {
  // 检查文件类型
  if (!file.name.toLowerCase().endsWith('.docx')) {
    ElMessage.error({ message: '仅支持 .docx 格式文件', showClose: true })
    return
  }

  // 检查文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error({ message: '文件大小不能超过 10MB', showClose: true })
    return
  }

  // 判断用户状态
  if (!authStore.isAuthenticated) {
    showGuestModal.value = true
    pendingFile.value = file
    return
  }

  // 游客模式检查
  if (authStore.isGuest) {
    if (!guestStore.hasTrialsRemaining) {
      showGuestModal.value = true
      pendingFile.value = file
      return
    }
    startCheck(file)
  } else {
    goToDashboardWithFile(file)
  }
}

// 开始检测（游客模式）
const startCheck = async (file) => {
  if (!guestStore.hasTrialsRemaining) {
    showGuestModal.value = true
    return
  }

  checking.value = true
  progress.value = 10

  try {
    const uploadResponse = await checkApi.upload(file, 'basic')
    if (uploadResponse.data.code !== 200) {
      ElMessage.error({ message: uploadResponse.data.message || '上传失败', showClose: true })
      checking.value = false
      progress.value = 0
      return
    }

    const fileId = uploadResponse.data.data.file_id
    progress.value = 30

    const checkResponse = await checkApi.submit(fileId, 'basic', file.name)
    if (checkResponse.data.code !== 200) {
      ElMessage.error({ message: checkResponse.data.message || '提交检查失败', showClose: true })
      checking.value = false
      progress.value = 0
      return
    }

    progress.value = 50
    const checkId = checkResponse.data.data.check_id

    await pollForResult(checkId, uploadResponse.data.data.filename)
    progress.value = 100

  } catch (error) {
    ElMessage.error({ message: '检查失败，请重试', showClose: true })
    checking.value = false
    progress.value = 0
  }
}

const pollForResult = async (checkId, filename) => {
  const maxAttempts = 30
  let attempts = 0

  while (attempts < maxAttempts) {
    try {
      const response = await checkApi.getResult(checkId)
      if (response.data.code === 200) {
        const data = response.data.data
        progress.value = 50 + (attempts / maxAttempts) * 40

        if (data.status === 'completed' && data.result) {
          guestStore.incrementTrialCount()
          const historyResult = guestStore.addToHistory({
            filename: filename || data.filename,
            check_type: data.check_type,
            status: data.status,
            total_issues: data.result?.total_issues || 0,
            created_at: data.created_at,
            result: data.result
          })

          if (!historyResult.success && historyResult.message) {
            ElMessage.warning({ message: historyResult.message, showClose: true })
          }

          checking.value = false
          progress.value = 0
          ElMessage.success({ message: '检查完成！', showClose: true })
          return
        } else if (data.status === 'failed') {
          ElMessage.error({ message: data.error_message || '检查失败', showClose: true })
          checking.value = false
          progress.value = 0
          return
        }
      }
    } catch (error) {
      console.error('Poll error:', error)
    }

    attempts++
    await new Promise(resolve => setTimeout(resolve, 2000))
  }

  ElMessage.warning({ message: '检查时间较长，请稍后在历史记录中查看', showClose: true })
  checking.value = false
  progress.value = 0
}

const continueAsGuest = async () => {
  showGuestModal.value = false

  if (!authStore.isGuest) {
    const result = await authStore.initGuestSession()
    if (!result.success) {
      ElMessage.error({ message: result.message || '初始化游客模式失败，请稍后重试', showClose: true })
      return
    }
  }

  if (pendingFile.value) {
    startCheck(pendingFile.value)
    pendingFile.value = null
  }
}

const goToLogin = () => {
  showGuestModal.value = false
  pendingFile.value = null
  router.push('/login')
}

const goToDashboardWithFile = (file) => {
  router.push('/dashboard')
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
/* 确保动画正确应用 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-24px); }
  to { opacity: 1; transform: translateX(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.6s ease-out forwards;
}

.animate-slideInLeft {
  animation: slideInLeft 0.5s ease-out forwards;
}
</style>
