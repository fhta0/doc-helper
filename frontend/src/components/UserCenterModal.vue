<template>
  <!-- Full screen overlay with backdrop blur -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="closeModal">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/15 backdrop-blur-sm"></div>

        <!-- Modal content -->
        <div class="relative glass-strong w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-[#b8860b]/20 max-h-[90vh] flex flex-col animate-scaleIn">
          <!-- Header -->
          <div class="p-6 border-b border-[#b8860b]/10 flex items-center justify-between flex-shrink-0">
            <div class="flex items-center space-x-4">
              <!-- 头像 - 印章风格 -->
              <div class="relative">
                <div class="w-14 h-14 rounded bg-gradient-to-br from-[#b8860b] to-[#d4a84b] flex items-center justify-center text-white font-heading font-bold text-xl shadow-md">
                  {{ userInitial }}
                </div>
                <!-- 金色装饰框 -->
                <div class="absolute inset-0 -m-0.5 border border-[#b8860b]/40 rounded pointer-events-none"></div>
              </div>
              <div>
                <h3 class="font-heading font-bold text-lg text-[#1a1a1a]">{{ displayName }}</h3>
                <p class="text-sm text-[#6b6b6b] font-mono">UID: {{ authStore.user?.id }}</p>
              </div>
            </div>
            <button @click="closeModal" class="text-[#6b6b6b] hover:text-[#1a1a1a] transition-colors p-1">
              <X class="w-6 h-6" />
            </button>
          </div>

          <!-- Scrollable content -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-traditional">
            <!-- Asset Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- 使用额度卡片 -->
              <div class="bg-[#faf8f3] p-5 rounded-xl border border-[#b8860b]/10 shadow-sm space-y-4">
                <div>
                  <h3 class="font-heading font-bold text-base text-[#1a1a1a]">使用额度</h3>
                  <p class="text-xs text-[#6b6b6b] mt-1">本月免费次数</p>
                </div>
                <!-- 进度条 -->
                <div class="space-y-2">
                  <div class="w-full bg-[#f5edd7] h-2 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all bg-gradient-to-r from-[#c8102e] to-[#b8860b]" :style="{ width: monthlyFreeProgress + '%' }"></div>
                  </div>
                  <div class="flex justify-end">
                    <span class="text-xs text-[#6b6b6b] font-mono">{{ monthlyFreeUsed }}/{{ monthlyFreeTotal }}</span>
                  </div>
                </div>
                <!-- 额度详情 -->
                <div class="grid grid-cols-2 gap-3 pt-1">
                  <div class="flex flex-col items-start space-y-1">
                    <FileText class="w-4 h-4 text-[#b8860b]" />
                    <p class="text-xs text-[#6b6b6b]">基础检测剩余</p>
                    <p class="text-xl font-bold font-heading text-[#b8860b]">{{ authStore.user?.basic_count || 0 }}</p>
                    <p class="text-xs text-[#9a9a9a]">次</p>
                  </div>
                  <div class="flex flex-col items-start space-y-1">
                    <Wand2 class="w-4 h-4 text-[#c8102e]" />
                    <p class="text-xs text-[#6b6b6b]">AI完整检测剩余</p>
                    <p class="text-xl font-bold font-heading text-[#c8102e]">{{ authStore.user?.full_count || 0 }}</p>
                    <p class="text-xs text-[#9a9a9a]">次</p>
                  </div>
                </div>
                <button class="w-full border-2 border-[#b8860b] text-[#b8860b] bg-transparent py-2 rounded-lg text-xs font-heading font-medium hover:bg-[#f5edd7] transition-colors" @click="goToPricing">
                  购买更多检测次数
                </button>
              </div>

              <!-- 使用统计卡片 -->
              <div class="bg-gradient-to-br from-[#c8102e] to-[#a00c24] p-5 rounded-xl shadow-md space-y-4 text-white">
                <h3 class="font-heading font-bold text-base">使用统计</h3>
                <div class="grid grid-cols-2 gap-3 pt-1">
                  <div class="flex flex-col space-y-1">
                    <p class="text-xs text-white/80">检查文档数</p>
                    <p class="text-2xl font-bold font-heading">{{ stats.total_checks }}</p>
                  </div>
                  <div class="flex flex-col space-y-1">
                    <p class="text-xs text-white/80">发现问题数</p>
                    <p class="text-2xl font-bold font-heading">{{ stats.total_issues }}</p>
                  </div>
                  <div class="flex flex-col space-y-1">
                    <p class="text-xs text-white/80">基础检测数</p>
                    <p class="text-2xl font-bold font-heading">{{ stats.basic_checks }}</p>
                  </div>
                  <div class="flex flex-col space-y-1">
                    <p class="text-xs text-white/80">AI完整检测数</p>
                    <p class="text-2xl font-bold font-heading">{{ stats.full_checks }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Transaction History -->
            <div>
              <h4 class="font-heading font-bold text-[#1a1a1a] mb-4 flex items-center space-x-2">
                <span>充值记录</span>
                <div class="flex-1 h-px bg-[#b8860b]/20"></div>
              </h4>

              <!-- Loading state -->
              <div v-if="loadingOrders" class="text-center py-8 text-[#6b6b6b]">
                <div class="w-8 h-8 border-2 border-[#b8860b]/20 border-t-[#c8102e] rounded-full animate-spin mx-auto mb-2"></div>
                <p class="text-sm">加载中...</p>
              </div>

              <!-- Empty state -->
              <div v-else-if="orders.length === 0" class="text-center py-8">
                <div class="w-16 h-16 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto mb-3">
                  <FileText class="w-8 h-8 text-[#b8860b]" />
                </div>
                <p class="text-[#6b6b6b] text-sm">暂无充值记录</p>
              </div>

              <!-- Orders list -->
              <div v-else class="space-y-2">
                <div
                  v-for="order in displayedOrders"
                  :key="order.id"
                  class="bg-[#faf8f3] rounded-xl p-4 flex items-center justify-between hover:bg-[#f5edd7] transition-colors border border-[#b8860b]/10"
                >
                  <div class="flex-1 min-w-0">
                    <p class="font-medium text-[#1a1a1a] text-sm truncate">{{ order.product_name }}</p>
                    <p class="text-xs text-[#6b6b6b] mt-1 font-mono">{{ formatDate(order.created_at) }}</p>
                  </div>
                  <div class="flex items-center space-x-3 ml-4">
                    <div class="text-right">
                      <p class="font-bold font-heading text-[#1a1a1a]">¥{{ order.amount.toFixed(2) }}</p>
                      <p class="text-xs font-medium" :class="getStatusClass(order.status)">
                        {{ getStatusText(order.status) }}
                      </p>
                    </div>
                    <!-- 待支付订单可以关闭 -->
                    <button
                      v-if="order.status === 'pending'"
                      @click="handleCloseOrder(order)"
                      class="text-[#c8102e] hover:text-[#a00c24] hover:bg-[#e8d5d9] transition-colors p-1.5 rounded"
                      title="关闭订单"
                    >
                      <X class="w-4 h-4" />
                    </button>
                    <button class="text-[#9a9a9a] hover:text-[#6b6b6b] transition-colors p-1.5" title="下载收据">
                      <FileText class="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <!-- Load more button -->
                <button
                  v-if="hasMoreOrders"
                  @click="loadMoreOrders"
                  class="w-full py-2.5 text-sm text-[#b8860b] font-heading font-medium hover:bg-[#f5edd7] rounded-lg transition-colors border border-dashed border-[#b8860b]/30"
                >
                  加载更多
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userApi, checkApi, purchaseApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { X, FileText, Wand2 } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const authStore = useAuthStore()

const orders = ref([])
const loadingOrders = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const totalOrders = ref(0)

const stats = ref({
  total_checks: 0,
  total_issues: 0,
  basic_checks: 0,
  full_checks: 0
})

// Computed properties
const userInitial = computed(() => {
  const username = authStore.user?.username
  return username ? username.charAt(0).toUpperCase() : 'U'
})

const displayName = computed(() => {
  return authStore.user?.nickname || authStore.user?.username || '用户'
})

const monthlyFreeTotal = computed(() => 3)
const monthlyFreeUsed = computed(() => {
  const freeCount = authStore.user?.free_count || 0
  return Math.max(0, Math.min(3, 3 - freeCount))
})
const monthlyFreeProgress = computed(() => {
  return (monthlyFreeUsed.value / monthlyFreeTotal.value) * 100
})

const displayedOrders = computed(() => orders.value)
const hasMoreOrders = computed(() => orders.value.length < totalOrders.value)

// Methods
const closeModal = () => {
  emit('update:modelValue', false)
}

const goToPricing = () => {
  closeModal()
  router.push('/pricing')
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}:${seconds}`
}

const getStatusText = (status) => {
  const statusMap = {
    'paid': '已支付',
    'pending': '待支付',
    'expired': '已过期',
    'closed': '已关闭',
    'refunded': '已退款'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const classMap = {
    'paid': 'text-[#2d5a4a]',
    'pending': 'text-[#b8860b]',
    'expired': 'text-[#9a9a9a]',
    'closed': 'text-[#9a9a9a]',
    'refunded': 'text-[#c8102e]'
  }
  return classMap[status] || 'text-[#9a9a9a]'
}

const fetchOrders = async (page = 1) => {
  loadingOrders.value = true
  try {
    const response = await userApi.getOrders(page, pageSize.value)
    if (response.data.code === 200) {
      if (page === 1) {
        orders.value = response.data.data.orders
      } else {
        orders.value.push(...response.data.data.orders)
      }
      totalOrders.value = response.data.data.total
      currentPage.value = page
    }
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  } finally {
    loadingOrders.value = false
  }
}

const fetchUserStats = async () => {
  try {
    const response = await checkApi.getStats()
    if (response.data.code === 200) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to fetch user stats:', error)
  }
}

const loadMoreOrders = () => {
  fetchOrders(currentPage.value + 1)
}

// 关闭订单
const handleCloseOrder = async (order) => {
  try {
    await ElMessageBox.confirm(
      `确定要关闭订单 ${order.order_no} 吗？关闭后将无法恢复。`,
      '关闭订单',
      {
        confirmButtonText: '确定关闭',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await purchaseApi.closeOrder(order.order_no)
    if (response.data.code === 200) {
      ElMessage.success({ message: '订单已关闭', showClose: true })
      currentPage.value = 1
      orders.value = []
      fetchOrders(1)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error({ message: error.response?.data?.message || '关闭订单失败', showClose: true })
    }
  }
}

// Watch for modal open
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    currentPage.value = 1
    orders.value = []
    fetchOrders(1)
    fetchUserStats()
    authStore.fetchProfile()
  }
})
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

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.95);
}

/* 玻璃态效果 */
.glass-strong {
  background: rgba(255, 251, 245, 0.95);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}

/* 自定义滚动条 */
.scrollbar-traditional::-webkit-scrollbar {
  width: 6px;
}
.scrollbar-traditional::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-traditional::-webkit-scrollbar-thumb {
  background: #b8860b;
  border-radius: 3px;
  opacity: 0.3;
}
.scrollbar-traditional::-webkit-scrollbar-thumb:hover {
  opacity: 0.5;
}
</style>
