<template>
  <div class="w-full max-w-2xl mx-auto space-y-4">
    <!-- 标题 -->
    <div class="flex items-center justify-between">
      <h3 class="font-heading text-lg font-bold text-[#1a1a1a] flex items-center space-x-2">
        <span>最近检查记录</span>
        <div class="w-8 h-px bg-[#b8860b]/30"></div>
      </h3>
      <span class="text-xs text-[#6b6b6b] px-2 py-1 bg-[#f5edd7] rounded-lg">游客模式 (最多2条)</span>
    </div>

    <!-- 历史记录列表 -->
    <div v-if="historyItems.length === 0" class="glass-strong bg-[#fffbf5] rounded-2xl p-8 text-center border border-[#b8860b]/10">
      <div class="w-12 h-12 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto mb-3">
        <FileX class="w-6 h-6 text-[#b8860b]" />
      </div>
      <p class="text-[#6b6b6b] text-sm">暂无检查记录</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="(item, index) in historyItems"
        :key="index"
        class="glass-strong bg-[#fffbf5] rounded-xl p-4 border border-[#b8860b]/10 hover:border-[#b8860b]/30 hover:bg-[#f5edd7]/20 transition-all cursor-pointer"
        @click="viewReport(item)"
      >
        <div class="flex items-center justify-between">
          <!-- 左侧：文件信息和分数 -->
          <div class="flex items-center space-x-4 flex-1">
            <div class="w-10 h-10 rounded-lg bg-[#f5edd7] flex items-center justify-center flex-shrink-0">
              <FileText class="w-5 h-5 text-[#b8860b]" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-[#1a1a1a] truncate">{{ item.filename }}</p>
              <p class="text-xs text-[#6b6b6b] font-mono">{{ formatTimeShort(item.created_at) }}</p>
            </div>
          </div>

          <!-- 右侧：分数和按钮 -->
          <div class="flex items-center space-x-4">
            <!-- 分数 -->
            <div class="text-right">
              <p class="text-2xl font-heading font-bold" :class="getScoreColorClass(item.total_issues)">
                {{ calculateScore(item.total_issues) }}
              </p>
              <p class="text-xs text-[#6b6b6b]">{{ item.total_issues }} 处问题</p>
            </div>

            <!-- 查看报告按钮 -->
            <button
              class="bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white px-4 py-2 rounded-lg text-sm font-heading font-medium hover:shadow-lg transition-all shadow-md flex items-center space-x-1 whitespace-nowrap"
            >
              <Eye class="w-4 h-4" />
              <span>查看</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 登录提示弹窗 -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showLoginPrompt" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/15" @click.self="showLoginPrompt = false">
        <div class="glass-strong rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-[#b8860b]/20 animate-scaleIn">
          <div class="p-8 text-center space-y-6">
            <div class="w-16 h-16 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto">
              <Lock class="w-8 h-8 text-[#b8860b]" />
            </div>
            <h3 class="font-heading text-2xl font-bold text-[#1a1a1a]">登录解锁完整报告</h3>
            <p class="text-[#6b6b6b]">登录后可查看详细的格式问题列表，并永久保存您的检查记录</p>
            <div class="flex flex-col gap-3">
              <button
                @click="goToLogin"
                class="w-full bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-3 rounded-xl font-heading font-bold hover:shadow-lg transition-all"
              >
                立即登录
              </button>
              <button
                @click="showLoginPrompt = false"
                class="w-full border-2 border-[#b8860b] text-[#1a1a1a] py-3 rounded-xl font-heading font-bold hover:bg-[#f5edd7] transition-all"
              >
                稍后再说
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGuestStore } from '@/stores/guest'
import { formatTimeShort, calculateScore, getScoreColorClass } from '@/utils/format'
import { FileText, FileX, Eye, Lock } from 'lucide-vue-next'

const router = useRouter()
const guestStore = useGuestStore()

const showLoginPrompt = ref(false)

// 获取历史记录
const historyItems = computed(() => {
  const historyValue = guestStore.history
  if (!historyValue || !Array.isArray(historyValue)) {
    return []
  }
  return historyValue.slice(0, 2)
})

// 查看报告
const viewReport = (item) => {
  showLoginPrompt.value = true
}

// 去登录
const goToLogin = () => {
  showLoginPrompt.value = false
  router.push('/login')
}
</script>

<style scoped>
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scaleIn {
  animation: scaleIn 0.2s ease-out forwards;
}

/* 玻璃态效果 */
.glass-strong {
  background: rgba(255, 251, 245, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(184, 134, 11, 0.2);
}
</style>
