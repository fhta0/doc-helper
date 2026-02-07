<template>
  <el-dialog
    v-model="visible"
    width="420px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="payment-dialog-wrapper"
  >
    <template #header>
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-[#f5edd7] rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-[#b8860b]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <span class="font-heading text-lg font-bold text-[#1a1a1a]">微信支付</span>
      </div>
    </template>

    <div class="payment-dialog">
      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-10">
        <div class="relative w-12 h-12 mx-auto mb-4">
          <div class="absolute inset-0 border-3 border-[#f5edd7] rounded-full"></div>
          <div class="absolute inset-0 border-3 border-transparent border-t-[#c8102e] rounded-full animate-spin"></div>
        </div>
        <p class="mt-4 text-[#6b6b6b]">正在生成支付二维码...</p>
      </div>

      <!-- 二维码展示 -->
      <div v-else-if="codeUrl" class="text-center space-y-5">
        <div class="qr-code-container relative">
          <!-- 装饰性边框 -->
          <div class="absolute inset-0 border-2 border-dashed border-[#b8860b]/20 rounded-xl pointer-events-none"></div>

          <img :src="qrCodeUrl" alt="支付二维码" class="qr-code" />

          <!-- 中心印章图标 -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-md">
              <svg class="w-6 h-6 text-[#09BB07]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="text-sm space-y-1">
          <p class="text-[#2d2d2d]">订单金额: <span class="font-heading font-bold text-[#c8102e]">¥{{ amount }}</span></p>
          <p class="text-[#9a9a9a] text-xs">请使用微信扫码支付</p>
        </div>

        <!-- 倒计时 -->
        <div v-if="expiresAt" class="inline-flex items-center space-x-2 px-3 py-1.5 bg-[#f5edd7] rounded-lg">
          <svg class="w-4 h-4 text-[#b8860b]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-xs text-[#b8860b] font-medium">支付有效期: {{ formatTime(expiresAt) }}</span>
        </div>
      </div>

      <!-- 支付结果 -->
      <div v-else-if="orderStatus === 'paid'" class="text-center py-10">
        <div class="w-20 h-20 bg-[#d7e8e3] rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="mt-4 text-lg font-heading font-bold text-[#2d5a4a]">支付成功！</p>
        <p class="text-[#6b6b6b]">正在跳转...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else class="text-center py-10">
        <div class="w-20 h-20 bg-[#f5e0e5] rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-[#c8102e]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="mt-4 text-[#c8102e] font-medium">{{ errorMessage || '生成支付二维码失败' }}</p>
      </div>
    </div>

    <template #footer>
      <div class="flex space-x-3">
        <button
          @click="handleClose"
          :disabled="orderStatus === 'paid'"
          class="flex-1 py-2.5 rounded-lg text-sm font-heading font-medium transition-all"
          :class="orderStatus === 'paid' ? 'bg-[#d7e8e3] text-[#2d5a4a] cursor-default' : 'bg-[#faf8f3] text-[#6b6b6b] hover:bg-[#f5edd7] hover:text-[#1a1a1a] border border-[#b8860b]/20'"
        >
          {{ orderStatus === 'paid' ? '完成' : '取消' }}
        </button>
        <button
          v-if="codeUrl && orderStatus !== 'paid'"
          @click="checkOrderStatus"
          class="flex-1 bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white py-2.5 rounded-lg text-sm font-heading font-medium hover:shadow-lg transition-all shadow-md"
        >
          刷新状态
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { purchaseApi } from '@/api'
import QRCode from 'qrcode'

const props = defineProps({
  modelValue: Boolean,
  orderNo: String,
  amount: Number,
  expiresAt: String,
  codeUrl: String
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(true)
const codeUrl = ref('')
const qrCodeUrl = ref('')
const orderStatus = ref('pending')
const errorMessage = ref('')
let checkInterval = null

// 生成二维码
const generateQRCode = async (url) => {
  try {
    qrCodeUrl.value = await QRCode.toDataURL(url)
  } catch (error) {
    console.error('Failed to generate QR code:', error)
    errorMessage.value = '生成二维码失败'
  }
}

// 查询订单状态
const checkOrderStatus = async () => {
  if (!props.orderNo) return

  try {
    const res = await purchaseApi.queryOrder(props.orderNo)
    if (res.data.code === 200) {
      const status = res.data.data.status
      if (status === 'paid') {
        orderStatus.value = 'paid'
        clearInterval(checkInterval)
        ElMessage.success({ message: '支付成功！', showClose: true })
        emit('success')
        setTimeout(() => {
          handleClose()
        }, 2000)
      }
    }
  } catch (error) {
    console.error('Failed to check order status:', error)
  }
}

// 开始轮询订单状态
const startPolling = () => {
  clearInterval(checkInterval)
  checkInterval = setInterval(() => {
    checkOrderStatus()
  }, 3000)
}

// 格式化时间
const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.max(0, Math.floor((date - now) / 1000))
  const minutes = Math.floor(diff / 60)
  const seconds = diff % 60
  return `${minutes}分${seconds}秒`
}

// 监听对话框显示
watch(() => props.modelValue, async (newVal) => {
  if (newVal && props.orderNo) {
    loading.value = true
    codeUrl.value = ''
    qrCodeUrl.value = ''
    orderStatus.value = 'pending'
    errorMessage.value = ''

    await new Promise(resolve => setTimeout(resolve, 1000))
    codeUrl.value = props.codeUrl || 'https://example.com'
    await generateQRCode(codeUrl.value)
    loading.value = false
    startPolling()
  } else {
    clearInterval(checkInterval)
  }
})

const handleClose = () => {
  clearInterval(checkInterval)
  visible.value = false
}

onUnmounted(() => {
  clearInterval(checkInterval)
})
</script>

<style scoped>
.payment-dialog {
  min-height: 320px;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #faf8f3 0%, #f5edd7 100%);
  border-radius: 16px;
  position: relative;
}

.qr-code {
  width: 220px;
  height: 220px;
  display: block;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Element Plus dialog 样式覆盖 */
.payment-dialog-wrapper :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 16px 48px rgba(26, 26, 26, 0.15);
}

.payment-dialog-wrapper :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(184, 134, 11, 0.1);
  padding: 16px 20px;
  margin: 0;
}

.payment-dialog-wrapper :deep(.el-dialog__body) {
  padding: 20px;
}

.payment-dialog-wrapper :deep(.el-dialog__footer) {
  border-top: 1px solid rgba(184, 134, 11, 0.1);
  padding: 12px 20px 16px;
  margin: 0;
}

.payment-dialog-wrapper :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #6b6b6b;
}

.payment-dialog-wrapper :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #1a1a1a;
}
</style>
