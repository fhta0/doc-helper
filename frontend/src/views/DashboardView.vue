<template>
  <div class="min-h-[calc(100vh-80px)] w-full max-w-7xl mx-auto px-6 pt-6 pb-6 md:pb-10 space-y-6">
    <!-- 上传区域 -->
    <div class="glass-strong bg-[#fffbf5] p-8 rounded-2xl shadow-sm border border-[#b8860b]/20">
      <!-- 格式模板选择 -->
      <div class="mb-6" v-if="!selectedFile && !checking">
        <label class="block text-sm font-medium text-[#2d2d2d] mb-3 flex items-center space-x-2">
          <span>格式规范模板</span>
          <div class="w-2 h-2 rounded-full bg-[#c8102e]"></div>
        </label>
        <div class="flex items-center space-x-4">
          <select
            v-model="selectedTemplateId"
            class="flex-1 px-4 py-3 bg-[#faf8f3] border-2 border-[#b8860b]/20 rounded-xl text-sm focus:ring-0 focus:border-[#b8860b] outline-none transition-all"
          >
            <option :value="null">选择格式规范模板...</option>
            <optgroup label="系统模板" v-if="templates.some(t => t.template_type === 'system')">
              <option v-for="t in templates.filter(t => t.template_type === 'system')" :key="t.id" :value="t.id">
                {{ t.name }}{{ t.is_default ? ' (默认)' : '' }}
              </option>
            </optgroup>
            <optgroup label="自定义模板" v-if="templates.some(t => t.template_type === 'custom')">
              <option v-for="t in templates.filter(t => t.template_type === 'custom')" :key="t.id" :value="t.id">
                {{ t.name }}
              </option>
            </optgroup>
          </select>
          <a
            href="/rules"
            class="text-[#c8102e] text-sm font-heading font-medium hover:underline flex items-center space-x-1"
          >
            <span>模板中心</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </a>
        </div>
        <p class="text-xs text-[#6b6b6b] mt-2">选择格式规范模板用于文档检查</p>
      </div>

      <!-- 检查类型选择 -->
      <div class="mb-6" v-if="!selectedFile && !checking">
        <label class="block text-sm font-medium text-[#2d2d2d] mb-3 flex items-center space-x-2">
          <span>检查类型</span>
          <div class="w-2 h-2 rounded-full bg-[#b8860b]"></div>
        </label>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            class="p-4 rounded-xl border-2 cursor-pointer transition-all relative group"
            :class="checkType === 'basic' ? 'border-[#c8102e] bg-[#e8d5d9]/30' : 'border-[#b8860b]/20 hover:border-[#b8860b]/40 bg-[#faf8f3]'"
            @click="checkType = 'basic'"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all"
                  :class="checkType === 'basic' ? 'border-[#c8102e]' : 'border-[#b8860b]/40'">
                  <div v-if="checkType === 'basic'" class="w-2.5 h-2.5 rounded-full bg-[#c8102e]"></div>
                </div>
                <div>
                  <h4 class="font-heading font-semibold text-[#1a1a1a]">基础检查</h4>
                  <p class="text-sm text-[#6b6b6b]">页面设置、字体、段落等格式检查</p>
                </div>
              </div>
              <div class="text-right">
                <span class="text-sm font-heading font-medium" :class="getBasicCountClass()">
                  {{ getBasicCountText() }}
                </span>
              </div>
            </div>
          </div>
          <div
            class="p-4 rounded-xl border-2 transition-all relative group"
            :class="
              guestStore.isGuest
                ? 'border-[#b8860b]/10 opacity-60 cursor-not-allowed bg-[#faf8f3]'
                : (checkType === 'full' ? 'border-[#c8102e] bg-[#e8d5d9]/30' : (canUseFullCheck ? 'border-[#b8860b]/20 hover:border-[#b8860b]/40 bg-[#faf8f3]' : 'border-[#b8860b]/10 opacity-60 cursor-not-allowed bg-[#faf8f3]'))
            "
            @click="!guestStore.isGuest && canUseFullCheck ? checkType = 'full' : null"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all"
                  :class="checkType === 'full' ? 'border-[#c8102e]' : 'border-[#b8860b]/40'">
                  <div v-if="checkType === 'full'" class="w-2.5 h-2.5 rounded-full bg-[#c8102e]"></div>
                </div>
                <div>
                  <h4 class="font-heading font-semibold text-[#1a1a1a]">完整检查</h4>
                  <p class="text-sm text-[#6b6b6b]">基础检查 + AI深度分析</p>
                  <p v-if="guestStore.isGuest" class="text-xs text-[#b8860b] mt-1 font-medium">登录解锁</p>
                  <p v-else-if="!canUseFullCheck" class="text-xs text-[#b8860b] mt-1 font-medium">次数不足，请购买</p>
                </div>
              </div>
              <div class="text-right">
                <span v-if="guestStore.isGuest" class="text-xs text-[#9a9a9a]">—</span>
                <span v-else class="text-sm font-heading font-medium" :class="getFullCountClass()">
                  {{ getFullCountText() }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 已选文件显示 -->
      <div v-if="selectedFile && !checking" class="mb-6 p-4 bg-[#f5edd7] rounded-xl flex items-center justify-between border border-[#b8860b]/20">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg bg-[#faf8f3] flex items-center justify-center">
            <FileText class="w-5 h-5 text-[#b8860b]" />
          </div>
          <div>
            <p class="font-medium text-[#1a1a1a]">{{ selectedFile.name }}</p>
            <p class="text-sm text-[#6b6b6b]">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <span class="text-sm text-[#c8102e] font-medium">正在准备检查...</span>
          <button @click="clearFile" class="text-[#9a9a9a] hover:text-[#c8102e] transition-colors">
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- 检查中状态 -->
      <div v-if="checking" class="text-center py-12">
        <div class="relative w-20 h-20 mx-auto mb-6">
          <!-- 传统风格加载器 -->
          <div class="absolute inset-0 border-4 border-[#f5edd7] rounded-full"></div>
          <div class="absolute inset-0 border-4 border-transparent border-t-[#c8102e] rounded-full animate-spin"></div>
          <div class="absolute inset-2 border-4 border-transparent border-r-[#b8860b] rounded-full animate-spin" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
        </div>
        <h3 class="font-heading text-xl font-bold text-[#1a1a1a] mb-2">正在检查文档格式...</h3>
        <p class="text-[#6b6b6b] mb-6">请稍候，这可能需要几秒钟</p>
        <div class="max-w-md mx-auto">
          <div class="w-full bg-[#f5edd7] h-2 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-[#c8102e] to-[#b8860b]" :style="{ width: progress + '%' }"></div>
          </div>
          <p class="text-sm text-[#6b6b6b] mt-2 font-mono">{{ progress }}%</p>
        </div>
      </div>

      <!-- 上传区域 -->
      <div
        v-if="!selectedFile && !checking"
        class="flex flex-col items-center justify-center space-y-6 text-center cursor-pointer border-2 border-dashed rounded-xl p-12 transition-all"
        :class="{ 'border-[#c8102e] bg-[#e8d5d9]/30': isDragging, 'border-[#b8860b]/30 hover:border-[#b8860b] hover:bg-[#f5edd7]/20': !isDragging }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @click="selectFile"
      >
        <div class="w-16 h-16 bg-[#f5edd7] rounded-2xl flex items-center justify-center">
          <Upload class="w-8 h-8 text-[#b8860b]" />
        </div>
        <div class="space-y-2">
          <p class="text-[#2d2d2d] font-medium">拖拽文件到此处，或点击图标上传</p>
          <p class="text-sm text-[#6b6b6b]">支持 .docx 格式，文件大小不超过 100MB</p>
          <p v-if="guestStore.isGuest" class="text-sm text-[#c8102e] font-medium">
            游客剩余试用次数：{{ guestStore.remainingTrials }} 次
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

    <!-- 最近检查记录 -->
    <div class="glass-strong bg-[#fffbf5] p-8 rounded-2xl shadow-sm border border-[#b8860b]/20">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-heading text-lg font-bold text-[#1a1a1a] flex items-center space-x-2">
          <span>最近检查</span>
          <div class="w-8 h-px bg-[#b8860b]/30"></div>
        </h3>
        <button v-if="recentChecks.length > 5" class="text-[#c8102e] text-sm font-heading font-medium hover:underline" @click="loadMore">
          {{ showAllChecks ? '收起' : '查看全部' }}
        </button>
      </div>

      <div v-if="recentChecks.length === 0" class="text-center py-12">
        <div class="w-16 h-16 bg-[#f5edd7] rounded-full flex items-center justify-center mx-auto mb-4">
          <FileX class="w-8 h-8 text-[#b8860b]" />
        </div>
        <p class="text-[#6b6b6b]">暂无检查记录</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-[#6b6b6b] text-sm border-b border-[#b8860b]/10">
              <th class="pb-4 font-medium text-left pr-8">文档名称</th>
              <th class="pb-4 font-medium text-center px-4" style="width: 180px">检查时间</th>
              <th class="pb-4 font-medium text-center px-4" style="width: 180px">完成时间</th>
              <th class="pb-4 font-medium text-center px-4" style="width: 100px">状态</th>
              <th class="pb-4 font-medium text-center px-4" style="width: 130px">结果</th>
              <th class="pb-4 font-medium text-right pl-4" style="width: 100px">操作</th>
            </tr>
          </thead>

          <tbody class="divide-y divide-[#b8860b]/5">
            <tr
              v-for="check in (showAllChecks ? recentChecks : recentChecks.slice(0, 5))"
              :key="check.check_id"
              class="group hover:bg-[#f5edd7]/30 transition-colors"
            >
              <td class="py-4 font-medium text-left pr-8">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 rounded-lg bg-[#f5edd7] flex items-center justify-center">
                    <FileText class="w-4 h-4 text-[#b8860b]" />
                  </div>
                  <span class="truncate">{{ check.filename }}</span>
                </div>
              </td>
              <td class="py-4 text-sm text-[#6b6b6b] text-center px-4 font-mono">{{ formatTimeFull(check.created_at) }}</td>
              <td class="py-4 text-sm text-[#6b6b6b] text-center px-4 font-mono">{{ check.updated_at ? formatTimeFull(check.updated_at) : '-' }}</td>
              <td class="py-4 text-center px-4">
                <div class="inline-flex">
                  <span
                    v-if="check.status === 'completed'"
                    class="px-2.5 py-1 bg-[#d7e8e3] text-[#2d5a4a] text-xs rounded-lg font-medium"
                  >检查完成</span>
                  <span
                    v-else-if="check.status === 'processing'"
                    class="px-2.5 py-1 bg-[#e0e8f0] text-[#3d5a80] text-xs rounded-lg font-medium"
                  >正在处理</span>
                  <span
                    v-else-if="check.status === 'failed'"
                    class="px-2.5 py-1 bg-[#f5e0e5] text-[#c8102e] text-xs rounded-lg font-medium"
                  >检查失败</span>
                  <span v-else class="px-2.5 py-1 bg-[#faf8f3] text-[#6b6b6b] text-xs rounded-lg font-medium">等待中</span>
                </div>
              </td>
              <td class="py-4 text-sm font-medium text-center px-4">
                <template v-if="check.status === 'completed'">
                  <span v-if="check.total_issues === 0" class="text-[#2d5a4a]">格式完全正确</span>
                  <span v-else class="text-[#b8860b]">发现 {{ check.total_issues }} 处异常</span>
                </template>
                <span v-else class="text-[#9a9a9a]">-</span>
              </td>
              <td class="py-4 text-right pl-4">
                <template v-if="check.status === 'completed'">
                  <button
                    class="text-[#c8102e] text-sm font-heading font-medium hover:underline
                          invisible group-hover:visible opacity-0 group-hover:opacity-100
                          transition-opacity"
                    @click.stop="viewCheckResult(check)"
                  >
                    查看详情
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 检查结果弹窗 -->
    <div v-if="showResultModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/15" @click.self="closeResultModal">
      <div class="glass-strong rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-[#b8860b]/20 animate-scaleIn">
        <!-- 弹窗头部 -->
        <div class="p-6 border-b border-[#b8860b]/10 flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center"
              :class="checkResultData?.result?.total_issues === 0 ? 'bg-[#d7e8e3]' : 'bg-[#f5edd7]'">
              <CheckCircle2 v-if="checkResultData?.result?.total_issues === 0" class="w-5 h-5 text-[#2d5a4a]" />
              <AlertCircle v-else class="w-5 h-5 text-[#b8860b]" />
            </div>
            <div>
              <h3 class="font-heading font-bold text-[#1a1a1a]">{{ checkResultData?.filename }}</h3>
              <p class="text-sm text-[#6b6b6b]">
                {{ checkResultData?.check_type === 'basic' ? '基础检查' : '完整检查' }} ·
                {{ checkResultData?.result?.total_issues || 0 }} 个问题
              </p>
            </div>
          </div>
          <button @click="closeResultModal" class="text-[#6b6b6b] hover:text-[#1a1a1a] transition-colors">
            <X class="w-6 h-6" />
          </button>
        </div>

        <!-- 弹窗内容 -->
        <div class="p-6 overflow-y-auto flex-1 scrollbar-traditional">
          <div v-if="checkResultData?.result?.total_issues === 0" class="text-center py-12">
            <div class="w-20 h-20 bg-[#d7e8e3] rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 class="w-10 h-10 text-[#2d5a4a]" />
            </div>
            <h3 class="font-heading text-2xl font-bold text-[#1a1a1a] mb-2">恭喜！文档格式完全符合规范</h3>
            <p class="text-[#6b6b6b]">您的文档通过了所有格式检查项</p>
          </div>

          <div v-else class="space-y-4">
            <!-- 顶部操作栏 -->
            <div class="flex justify-between items-center mb-4">
              <h4 class="font-heading font-bold text-[#1a1a1a]">问题详情</h4>
              <button
                @click="handleDownloadRevised"
                :disabled="isGeneratingRevised"
                class="flex items-center space-x-2 bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white px-4 py-2 rounded-xl text-sm font-heading font-medium hover:shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed"
              >
                <Download v-if="!isGeneratingRevised" class="w-4 h-4" />
                <div v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>{{ checkResultData?.revised_file_generated ? '下载修订版文档' : (isGeneratingRevised ? '生成中...' : '生成修订建议版') }}</span>
              </button>
            </div>

            <div
              v-for="(issue, index) in checkResultData?.result?.issues"
              :key="index"
              class="p-4 rounded-xl border border-[#b8860b]/10 hover:border-[#b8860b]/30 hover:bg-[#f5edd7]/20 transition-all cursor-pointer bg-[#faf8f3]"
              @click="toggleIssueDetail(index)"
            >
              <div class="flex items-start justify-between">
                <div class="flex items-start space-x-3 flex-1">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                    :class="getIssueBgClass(issue.category)">
                    <span class="text-xs font-heading font-bold" :class="getIssueTextClass(issue.category)">
                      {{ getIssueIcon(issue.category) }}
                    </span>
                  </div>
                  <div class="flex-1">
                    <p class="font-medium text-[#1a1a1a]">{{ issue.rule_name }}</p>
                    <p class="text-sm text-[#c8102e] mt-1">{{ issue.error_message }}</p>
                    <p class="text-sm text-[#b8860b] mt-1">建议: {{ issue.suggestion }}</p>
                  </div>
                </div>
                <ChevronDown class="w-5 h-5 text-[#6b6b6b] transition-transform"
                  :class="{ 'rotate-180': expandedIssues.has(index) }" />
              </div>

              <!-- 位置详情 -->
              <div v-if="expandedIssues.has(index) && issue.locations_list?.length > 0" class="mt-4 pt-4 border-t border-[#b8860b]/10">
                <p class="text-sm font-medium text-[#2d2d2d] mb-3">问题位置 (共 {{ issue.location?.count || 0 }} 处):</p>
                <div class="space-y-2">
                  <div v-for="(pageGroup, pageIdx) in issue.locations_list" :key="pageGroup.page" class="flex flex-wrap items-center gap-2">
                    <span class="text-xs font-medium text-[#c8102e] bg-[#e8d5d9] px-2 py-1 rounded-lg">第{{ pageGroup.page }}页</span>
                    <span v-for="(item, idx) in (expandedPages.has(`${index}-${pageIdx}`) ? pageGroup.all_items : pageGroup.items)" :key="idx" class="text-xs bg-[#faf8f3] px-2 py-1 rounded text-[#6b6b6b] border border-[#b8860b]/10">
                      {{ item }}
                    </span>
                    <button
                      v-if="pageGroup.has_more && !expandedPages.has(`${index}-${pageIdx}`)"
                      @click.stop="togglePageExpand(index, pageIdx)"
                      class="text-xs text-[#c8102e] hover:underline"
                    >
                      全部展开
                    </button>
                    <button
                      v-if="expandedPages.has(`${index}-${pageIdx}`)"
                      @click.stop="togglePageExpand(index, pageIdx)"
                      class="text-xs text-[#6b6b6b] hover:underline"
                    >
                      收起
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGuestStore } from '@/stores/guest'
import { checkApi, ruleTemplateApi } from '@/api'
import { ElMessage } from 'element-plus'
import { formatTimeFull, formatFileSize } from '@/utils/format'
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  FileText,
  FileX,
  Upload,
  X,
  Download
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const guestStore = useGuestStore()

// 状态
const recentChecks = ref([])
const isDragging = ref(false)
const fileInputRef = ref(null)
const selectedFile = ref(null)
const checkType = ref('basic')
const selectedTemplateId = ref(null)
const templates = ref([])
const checking = ref(false)
const progress = ref(0)
const showResultModal = ref(false)
const checkResultData = ref(null)
const expandedIssues = ref(new Set())
const expandedPages = ref(new Set())
const showAllChecks = ref(false)

// 计算属性
const canUseFullCheck = computed(() => {
  return (authStore.user?.full_count || 0) > 0
})

// 获取基础检查次数文本
const getBasicCountText = () => {
  if (guestStore.isGuest) {
    return `${guestStore.remainingTrials}/3`
  }

  // 计算总可用次数 = 免费次数 + 购买的基础检测包次数
  const freeCount = authStore.user?.free_count || 0
  const basicCount = authStore.user?.basic_count || 0
  const totalRemaining = freeCount + basicCount

  if (totalRemaining === 0) {
    return '0次'
  }

  // 如果有免费次数，显示"含X次免费"
  if (freeCount > 0) {
    return `剩余${totalRemaining}次（含${freeCount}次免费）`
  }

  return `剩余${totalRemaining}次`
}

// 获取基础检查次数样式
const getBasicCountClass = () => {
  if (guestStore.isGuest) {
    return guestStore.remainingTrials > 0 ? 'text-[#c8102e]' : 'text-[#b8860b]'
  }

  // 基于总可用次数判断颜色
  const freeCount = authStore.user?.free_count || 0
  const basicCount = authStore.user?.basic_count || 0
  const totalRemaining = freeCount + basicCount

  if (totalRemaining === 0) return 'text-[#b8860b]'
  if (totalRemaining <= 5) return 'text-[#b8860b]'
  return 'text-[#c8102e]'
}

// 获取完整检查次数文本
const getFullCountText = () => {
  const quota = authStore.user?.quota?.full
  if (quota && quota.total > 0) {
    return `${quota.used}/${quota.total}`
  }

  const remaining = authStore.user?.full_count || 0
  if (remaining > 0) {
    return `剩余${remaining}次`
  }
  return '0/0'
}

// 获取完整检查次数样式
const getFullCountClass = () => {
  const remaining = authStore.user?.full_count || 0
  if (remaining === 0) return 'text-[#b8860b]'
  if (remaining <= 2) return 'text-[#b8860b]'
  return 'text-[#c8102e]'
}

// 初始化
onMounted(async () => {
  showResultModal.value = false

  // Load rule templates
  try {
    const res = await ruleTemplateApi.getTemplates()
    if (res.data.code === 200) {
      templates.value = res.data.data.templates || []

      let templateToSelect = null

      if (authStore.user?.last_template_id) {
        const lastTemplate = templates.value.find(t => t.id === authStore.user.last_template_id)
        if (lastTemplate) {
          templateToSelect = lastTemplate
        }
      }

      if (!templateToSelect) {
        templateToSelect = templates.value.find(t => t.is_default)
      }

      if (templateToSelect) {
        selectedTemplateId.value = templateToSelect.id
      }
    }
  } catch (error) {
    console.error('Failed to load templates:', error)
  }

  // Check if user is guest or regular user
  if (authStore.isGuest) {
    if (!guestStore.hasTrialsRemaining) {
      ElMessage.warning({ message: '您的试用次数已用完，请登录后继续使用', showClose: true })
      router.push('/login')
      return
    }

    recentChecks.value = guestStore.getHistory().map(h => ({
      filename: h.filename,
      check_type: h.check_type,
      status: h.status,
      total_issues: h.total_issues,
      created_at: h.created_at,
      check_id: `guest_${Date.now()}`
    }))
  } else if (authStore.isAuthenticated) {
    try {
      // 确保 token 已同步到请求拦截器，稍作延迟
      await new Promise(resolve => setTimeout(resolve, 50))
      await authStore.fetchProfile()
      await fetchRecentChecks()
    } catch (error) {
      if (error.response?.status === 401) {
        authStore.clearUser()
        recentChecks.value = guestStore.getHistory().map(h => ({
          filename: h.filename,
          check_type: h.check_type,
          status: h.status,
          total_issues: h.total_issues,
          created_at: h.created_at,
          check_id: `guest_${Date.now()}`
        }))
      }
    }
  }
})

// 获取最近检查记录
const fetchRecentChecks = async () => {
  try {
    const response = await checkApi.getRecent(10)
    if (response.data.code === 200) {
      recentChecks.value = response.data.data.checks || []
    }
  } catch (error) {
    console.error('Failed to fetch recent checks:', error)
  }
}

// 文件选择
const selectFile = () => {
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
  if (!file.name.toLowerCase().endsWith('.docx')) {
    ElMessage.error({ message: '仅支持 .docx 格式文件', showClose: true })
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error({ message: '文件大小不能超过 10MB', showClose: true })
    return
  }

  if (guestStore.isGuest && !guestStore.hasTrialsRemaining) {
    ElMessage.warning({ message: '您的试用次数已用完，请登录后继续使用', showClose: true })
    router.push('/login')
    return
  }

  if (!guestStore.isGuest && authStore.isAuthenticated) {
    const freeCount = authStore.user?.free_count || 0
    const basicCount = authStore.user?.basic_count || 0
    const totalRemaining = freeCount + basicCount

    if (totalRemaining === 0) {
      ElMessage.warning({ message: '您的检测次数已用完，请购买更多次数', showClose: true })
      return
    }
  }

  selectedFile.value = file
  handleSubmit()
}

const clearFile = () => {
  selectedFile.value = null
}

// 提交检查
const handleSubmit = async () => {
  if (!selectedFile.value) {
    ElMessage.warning({ message: '请先选择文件', showClose: true })
    return
  }

  if (guestStore.isGuest) {
    if (!guestStore.hasTrialsRemaining) {
      ElMessage.warning({ message: '您的试用次数已用完，请登录后继续使用', showClose: true })
      router.push('/login')
      return
    }
  }

  checking.value = true
  progress.value = 10

  try {
    const uploadResponse = await checkApi.upload(selectedFile.value, checkType.value)
    if (uploadResponse.data.code !== 200) {
      ElMessage.error({ message: uploadResponse.data.message || '上传失败', showClose: true })
      checking.value = false
      selectedFile.value = null
      return
    }

    const fileId = uploadResponse.data.data.file_id
    progress.value = 30

    const checkResponse = await checkApi.submit(
      fileId,
      checkType.value,
      selectedFile.value.name,
      selectedTemplateId.value
    )
    if (checkResponse.data.code !== 200) {
      ElMessage.error({ message: checkResponse.data.message || '提交检查失败', showClose: true })
      checking.value = false
      selectedFile.value = null
      return
    }

    progress.value = 50
    const checkId = checkResponse.data.data.check_id

    // 立即更新用户信息，反映次数扣减
    if (!guestStore.isGuest && authStore.isAuthenticated) {
      await authStore.fetchProfile()
    }

    await pollForResult(checkId, uploadResponse.data.data.filename)
    progress.value = 100

  } catch (error) {
    ElMessage.error({ message: '检查失败，请重试', showClose: true })
    checking.value = false
    selectedFile.value = null
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
          checkResultData.value = data
          showResultModal.value = true

          if (guestStore.isGuest) {
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
            recentChecks.value = guestStore.getHistory().map(h => ({
              filename: h.filename,
              check_type: h.check_type,
              status: h.status,
              total_issues: h.total_issues,
              created_at: h.created_at,
              check_id: `guest_${Date.now()}`
            }))
          } else {
            await fetchRecentChecks()
            await authStore.fetchProfile()
          }
          checking.value = false
          selectedFile.value = null
          progress.value = 0
          return
        } else if (data.status === 'failed') {
          ElMessage.error({ message: data.error_message || '检查失败', showClose: true })
          checking.value = false
          selectedFile.value = null
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

  checking.value = false
  selectedFile.value = null
  progress.value = 0
  ElMessage.warning({ message: '检查时间较长，请稍后在历史记录中查看', showClose: true })
}

// 查看检查结果
const viewCheckResult = async (check) => {
  if (check.status === 'processing' || check.status === 'pending') {
    ElMessage.info({ message: '文档正在处理中，请稍后刷新', showClose: true })
    return
  }

  if (check.status === 'failed') {
    ElMessage.error({ message: check.error_message || '检查失败', showClose: true })
    return
  }

  try {
    const response = await checkApi.getResult(check.check_id)
    if (response.data.code === 200) {
      checkResultData.value = response.data.data
      showResultModal.value = true
    }
  } catch (error) {
    ElMessage.error({ message: '获取结果失败', showClose: true })
  }
}

const isGeneratingRevised = ref(false)

// 生成并下载修订版
const handleDownloadRevised = async () => {
  if (!checkResultData.value || !checkResultData.value.check_id) return

  if (checkResultData.value.revised_file_generated) {
    downloadRevisedFile(checkResultData.value.check_id)
    return
  }

  isGeneratingRevised.value = true
  try {
    const response = await checkApi.generateRevised(checkResultData.value.check_id)
    if (response.data.code === 200) {
      ElMessage.success({ message: '修订版生成成功，开始下载', showClose: true })
      checkResultData.value.revised_file_generated = true
      downloadRevisedFile(checkResultData.value.check_id)
    } else {
      ElMessage.error({ message: response.data.message || '生成修订版失败', showClose: true })
    }
  } catch (error) {
    ElMessage.error({ message: '请求失败，请稍后重试', showClose: true })
  } finally {
    isGeneratingRevised.value = false
  }
}

const downloadRevisedFile = (checkId) => {
  const downloadUrl = `${import.meta.env.VITE_API_URL || ''}/api/check/${checkId}/download_revised`
  window.open(downloadUrl, '_blank')
}

const closeResultModal = () => {
  showResultModal.value = false
  checkResultData.value = null
  expandedIssues.value.clear()
  expandedPages.value.clear()
}

// 展开/收起问题详情
const toggleIssueDetail = (index) => {
  if (expandedIssues.value.has(index)) {
    expandedIssues.value.delete(index)
  } else {
    expandedIssues.value.add(index)
  }
}

const togglePageExpand = (issueIdx, pageIdx) => {
  const key = `${issueIdx}-${pageIdx}`
  if (expandedPages.value.has(key)) {
    expandedPages.value.delete(key)
  } else {
    expandedPages.value.add(key)
  }
}

// 问题分类样式
const getIssueBgClass = (category) => {
  const classes = {
    page: 'bg-[#f5edd7]',
    font: 'bg-[#f5e0e5]',
    paragraph: 'bg-[#f5e0e5]',
    heading: 'bg-[#faf8f3]',
    figure: 'bg-[#e0e8f0]',
    reference: 'bg-[#d7e8e3]',
    other: 'bg-[#faf8f3]'
  }
  return classes[category] || 'bg-[#faf8f3]'
}

const getIssueTextClass = (category) => {
  const classes = {
    page: 'text-[#b8860b]',
    font: 'text-[#c8102e]',
    paragraph: 'text-[#c8102e]',
    heading: 'text-[#2d2d2d]',
    figure: 'text-[#3d5a80]',
    reference: 'text-[#2d5a4a]',
    other: 'text-[#6b6b6b]'
  }
  return classes[category] || 'text-[#6b6b6b]'
}

const getIssueIcon = (category) => {
  const icons = {
    page: '页',
    font: '字',
    paragraph: '段',
    heading: '标',
    figure: '图',
    reference: '参',
    other: '其'
  }
  return icons[category] || '其'
}

// 其他方法
const loadMore = () => {
  showAllChecks.value = !showAllChecks.value
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
