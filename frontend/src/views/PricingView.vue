<template>
  <div class="min-h-[calc(100vh-80px)] py-12 px-6">
    <div class="max-w-7xl mx-auto space-y-16">
      <!-- 标题区域 -->
      <div class="text-center space-y-4">
        <h2 class="font-heading text-4xl md:text-5xl font-bold text-[#1a1a1a] tracking-tight">为您定制的检查方案</h2>
        <p class="text-[#6b6b6b] text-lg">一次购买，长效保障，提升您的文档生产力</p>
        <div class="w-16 h-1 bg-gradient-to-r from-[#c8102e] to-[#b8860b] mx-auto rounded-full"></div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-20">
        <div class="relative w-16 h-16 mx-auto mb-4">
          <div class="absolute inset-0 border-4 border-[#f5edd7] rounded-full"></div>
          <div class="absolute inset-0 border-4 border-transparent border-t-[#c8102e] rounded-full animate-spin"></div>
        </div>
        <p class="text-[#6b6b6b]">正在获取最新优惠...</p>
      </div>

      <!-- 价格卡片 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div
          v-for="pkg in packages"
          :key="pkg.id"
          :class="[
            'p-8 rounded-2xl flex flex-col space-y-6 transition-all bento-card relative',
            pkg.id === 'full_pack'
              ? 'bg-gradient-to-br from-[#c8102e] to-[#a00c24] text-white shadow-xl'
              : 'glass-strong border-[#b8860b]/20'
          ]"
        >
          <!-- 推荐标签 -->
          <div v-if="pkg.id === 'full_pack'" class="absolute top-4 right-4 px-3 py-1 bg-[#f5edd7] text-[#c8102e] rounded-lg text-[10px] font-black tracking-widest font-heading font-bold">
            推荐
          </div>

          <div class="space-y-2">
            <h3 class="font-heading text-xl font-bold" :class="pkg.id === 'full_pack' ? 'text-white' : 'text-[#1a1a1a]'">{{ pkg.name }}</h3>
            <p :class="pkg.id === 'full_pack' ? 'text-white/80' : 'text-[#6b6b6b]'" class="text-sm">
              {{ pkg.description.split(' ')[0] }}
            </p>
          </div>

          <div class="flex items-baseline space-x-1">
            <span class="text-4xl font-heading font-bold" :class="pkg.id === 'full_pack' ? 'text-[#f5edd7]' : 'text-[#c8102e]'">¥{{ pkg.price }}</span>
            <span :class="pkg.id === 'full_pack' ? 'text-white/80' : 'text-[#6b6b6b]'" class="text-sm">/ {{ pkg.count }}次</span>
          </div>

          <ul class="space-y-3 flex-1">
            <li class="flex items-center space-x-3 text-sm">
              <div class="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center"
                :class="pkg.id === 'full_pack' ? 'bg-[#f5edd7]' : 'bg-[#d7e8e3]'">
                <svg class="w-3 h-3" :class="pkg.id === 'full_pack' ? 'text-[#c8102e]' : 'text-[#2d5a4a]'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span :class="pkg.id === 'full_pack' ? 'text-white' : 'text-[#2d2d2d]'">包含 {{ pkg.count }} 次检测</span>
            </li>
            <li class="flex items-center space-x-3 text-sm">
              <div class="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center"
                :class="pkg.id === 'full_pack' ? 'bg-[#f5edd7]' : 'bg-[#d7e8e3]'">
                <svg class="w-3 h-3" :class="pkg.id === 'full_pack' ? 'text-[#c8102e]' : 'text-[#2d5a4a]'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span :class="pkg.id === 'full_pack' ? 'text-white' : 'text-[#2d2d2d]'">{{ pkg.description }}</span>
            </li>
          </ul>

          <button
            @click="handlePurchase(pkg)"
            :class="[
              'w-full py-4 rounded-xl font-heading font-bold transition-all',
              pkg.id === 'full_pack'
                ? 'bg-[#f5edd7] text-[#c8102e] hover:bg-white shadow-lg'
                : 'bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white hover:shadow-lg shadow-md'
            ]"
          >
            立即订购
          </button>

          <!-- 装饰性印章 -->
          <div v-if="pkg.id === 'full_pack'" class="absolute bottom-4 right-4 w-12 h-12 opacity-20">
            <div class="w-full h-full border-2 border-white rounded flex items-center justify-center">
              <span class="text-white text-xs font-heading font-bold">优</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 常见问题 -->
      <div class="max-w-3xl mx-auto space-y-6 pt-8">
        <h3 class="font-heading text-2xl font-bold text-center text-[#1a1a1a] flex items-center justify-center space-x-3">
          <span>常见问题咨询</span>
          <div class="w-12 h-px bg-[#b8860b]/30"></div>
        </h3>
        <div class="grid grid-cols-1 gap-4">
          <div class="p-6 glass-strong rounded-xl border border-[#b8860b]/10">
            <h4 class="font-heading font-bold mb-2 text-[#1a1a1a]">套餐次数会过期吗？</h4>
            <p class="text-sm text-[#6b6b6b] leading-relaxed">
              所有检测包购买后永久有效，可在任意时间使用，不会过期。
            </p>
          </div>
          <div class="p-6 glass-strong rounded-xl border border-[#b8860b]/10">
            <h4 class="font-heading font-bold mb-2 text-[#1a1a1a]">是否支持企业统一开票？</h4>
            <p class="text-sm text-[#6b6b6b] leading-relaxed">
              支持，登录后在后台个人中心提交开票信息，我们将在 3 个工作日内开具电子发票。
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 支付对话框 -->
    <PaymentDialog
      v-model="showPaymentDialog"
      :order-no="currentOrder.orderNo"
      :amount="currentOrder.amount"
      :expires-at="currentOrder.expiresAt"
      :code-url="currentOrder.codeUrl"
      @success="handlePaymentSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { purchaseApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import PaymentDialog from '@/components/PaymentDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const packages = ref([])
const loading = ref(true)
const showPaymentDialog = ref(false)
const currentOrder = ref({
  orderNo: '',
  amount: 0,
  expiresAt: '',
  codeUrl: ''
})

const fetchPackages = async () => {
  try {
    const res = await purchaseApi.getPackages()
    if (res.data.code === 200) {
      const list = res.data.data.packages
      const order = ['basic_pack', 'full_pack', 'single_full']
      packages.value = list.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))
    }
  } catch (error) {
    console.error('Failed to fetch packages:', error)
    ElMessage.error({ message: '获取套餐列表失败', showClose: true })
  } finally {
    loading.value = false
  }
}

const handlePurchase = async (pkg) => {
  if (!authStore.isAuthenticated || authStore.isGuest) {
    ElMessage.warning({ message: '请先登录', showClose: true })
    router.push('/login')
    return
  }

  try {
    const res = await purchaseApi.createOrder({
      package_type: pkg.id,
      payment_method: 'wechat'
    })

    if (res.data.code === 200) {
      const data = res.data.data
      currentOrder.value = {
        orderNo: data.order_no,
        amount: data.amount,
        expiresAt: data.expires_at,
        codeUrl: data.code_url
      }
      showPaymentDialog.value = true
    } else if (res.data.code === 4003) {
      const pendingOrder = res.data.data.pending_order
      ElMessageBox.confirm(
        `您有未支付的订单（订单号：${pendingOrder.order_no}），请先完成或关闭该订单后再创建新订单。`,
        '存在未支付订单',
        {
          confirmButtonText: '关闭未支付订单',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await purchaseApi.closeOrder(pendingOrder.order_no)
          ElMessage.success({ message: '订单已关闭，请重新点击购买', showClose: true })
        } catch (error) {
          ElMessage.error({ message: error.response?.data?.message || '关闭订单失败', showClose: true })
        }
      }).catch(() => {
        // User cancelled
      })
    }
  } catch (error) {
    console.error('Purchase failed:', error)
    ElMessage.error({ message: error.response?.data?.message || '创建订单失败', showClose: true })
  }
}

const handlePaymentSuccess = async () => {
  await authStore.fetchUser()
}

onMounted(() => {
  fetchPackages()
})
</script>

<style scoped>
/* 玻璃态效果 */
.glass-strong {
  background: rgba(255, 251, 245, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(184, 134, 11, 0.2);
}
</style>
