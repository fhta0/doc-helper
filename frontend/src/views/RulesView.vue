<template>
  <div class="min-h-screen bg-[#f7f4ed] pt-16">
    <!-- 页面标题 -->
    <div class="bg-[#fffbf5] border-b border-[#b8860b]/10">
      <div class="max-w-[1600px] mx-auto px-6 py-4">
        <h1 class="font-heading text-2xl font-bold text-[#1a1a1a]">论文格式检查模板</h1>
        <p class="text-sm text-[#6b6b6b] mt-1">文档格式检查模板</p>
      </div>
    </div>

    <!-- 主内容区 - 三栏布局 -->
    <div class="max-w-[1600px] mx-auto p-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- 左侧：格式模板列表 -->
        <div class="lg:col-span-2">
          <div class="glass-strong bg-[#fffbf5] rounded-xl shadow-sm border border-[#b8860b]/20">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">格式模板</h2>
            </div>

            <!-- 系统模板 -->
            <div class="border-b border-[#b8860b]/5">
              <button
                @click="toggleSystemTemplates"
                class="w-full px-4 py-3 flex items-center justify-between hover:bg-[#f5edd7] transition-colors"
              >
                <span class="text-sm font-medium text-[#2d2d2d]">系统模板 (官方)</span>
                <svg
                  class="w-4 h-4 text-[#b8860b] transition-transform"
                  :class="{ 'rotate-180': systemTemplatesExpanded }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-show="systemTemplatesExpanded" class="pb-2">
                <div
                  v-for="template in systemTemplates"
                  :key="template.id"
                  @click="selectTemplate(template)"
                  class="px-4 py-2 cursor-pointer hover:bg-[#f5edd7] transition-colors"
                  :class="{ 'bg-[#e8d5d9] border-l-2 border-[#c8102e]': currentTemplate?.id === template.id }"
                >
                  <div class="text-sm text-[#2d2d2d]">{{ template.name }}</div>
                  <div v-if="template.is_default" class="text-xs text-[#b8860b] mt-1">
                    <span class="inline-block px-1.5 py-0.5 bg-[#f5edd7] rounded font-medium">默认</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 我的模板 -->
            <div>
              <button
                @click="toggleCustomTemplates"
                class="w-full px-4 py-3 flex items-center justify-between hover:bg-[#f5edd7] transition-colors"
              >
                <span class="text-sm font-medium text-[#2d2d2d]">我的模板 (自定义)</span>
                <svg
                  class="w-4 h-4 text-[#b8860b] transition-transform"
                  :class="{ 'rotate-180': customTemplatesExpanded }"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-show="customTemplatesExpanded" class="pb-2">
                <div
                  v-for="template in customTemplates"
                  :key="template.id"
                  class="px-4 py-2 hover:bg-[#f5edd7] transition-colors group relative"
                  :class="{ 'bg-[#e8d5d9] border-l-2 border-[#c8102e]': currentTemplate?.id === template.id }"
                >
                  <div @click="selectTemplate(template)" class="cursor-pointer pr-6">
                    <div class="text-sm text-[#2d2d2d]">{{ template.name }}</div>
                    <div class="text-xs text-[#9a9a9a] mt-1">{{ template.use_count }}次使用</div>
                  </div>
                  <!-- 删除按钮 -->
                  <button
                    @click.stop="deleteTemplate(template)"
                    class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[#9a9a9a] hover:text-[#c8102e] hover:bg-[#f5e0e5] rounded opacity-0 group-hover:opacity-100 transition-all"
                    title="删除模板"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                <div v-if="customTemplates.length === 0" class="px-4 py-4 text-center">
                  <p class="text-sm text-[#9a9a9a]">暂无自定义模板</p>
                </div>
              </div>
            </div>

            <!-- 新建按钮 -->
            <div class="p-4 border-t border-[#b8860b]/10">
              <router-link
                to="/rules/new"
                class="flex items-center justify-center px-4 py-2.5 border-2 border-[#b8860b] text-[#1a1a1a] rounded-lg hover:bg-[#f5edd7] hover:border-[#b8860b] transition-all text-sm font-heading font-medium space-x-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>新建自定义模板</span>
              </router-link>
            </div>
          </div>
        </div>

        <!-- 中间：文档预览 -->
        <div class="lg:col-span-7">
          <div class="glass-strong bg-[#fffbf5] rounded-xl shadow-sm border border-[#b8860b]/20">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">文档预览</h2>
            </div>

            <!-- Tab -->
            <div class="px-4 pt-4">
              <div class="flex space-x-4 border-b border-[#b8860b]/10">
                <button class="px-2 py-2 text-sm font-heading font-medium text-[#c8102e] border-b-2 border-[#c8102e]">
                  实时预览
                </button>
              </div>
            </div>

            <!-- 预览区域 -->
            <div class="p-6">
              <!-- A4 纸张预览 -->
              <div
                class="mx-auto bg-white shadow-lg border"
                :style="{
                  width: a4Width + 'px',
                  minHeight: a4Height + 'px',
                  padding: configMargins
                }"
              >
                <!-- 标题 -->
                <div
                  v-if="config?.headings?.[0]"
                  class="text-center mb-6"
                  :style="getHeadingStyle(1)"
                >
                  学术论文标题示例
                </div>

                <!-- 一级标题 -->
                <div
                  v-if="config?.headings?.[0]"
                  class="mb-4"
                  :style="getHeadingStyle(1)"
                >
                  一、引言
                </div>

                <!-- 正文段落 -->
                <div
                  v-for="i in 3"
                  :key="i"
                  class="mb-4"
                  :style="getBodyStyle()"
                >
                  本文探讨了学术论文格式规范的重要性及其在现代学术交流中的作用。规范的格式不仅能够提升论文的专业性和可读性，还能确保学术信息的准确传递。本研究采用文献分析法和对比研究法，收集了近年来国内外顶级学术期刊的格式要求文档。
                </div>

                <!-- 二级标题 -->
                <div
                  v-if="config?.headings?.[1]"
                  class="mb-4 mt-6"
                  :style="getHeadingStyle(2)"
                >
                  二、研究方法
                </div>

                <!-- 正文段落 -->
                <div
                  v-for="i in 2"
                  :key="i + 10"
                  class="mb-4"
                  :style="getBodyStyle()"
                >
                  本研究采用文献分析法和对比研究法，收集了近年来国内外顶级学术期刊的格式要求文档。通过对这些文档的系统分析，我们总结出了一套完整的学术论文格式规范体系。该体系包括页面设置、字体要求、行距规范等关键要素。
                </div>

                <!-- 三级标题 -->
                <div
                  v-if="config?.headings?.[2]"
                  class="mb-4 mt-6"
                  :style="getHeadingStyle(3)"
                >
                  2.1 数据收集
                </div>

                <!-- 正文段落 -->
                <div
                  class="mb-4"
                  :style="getBodyStyle()"
                >
                  数据收集过程严格遵循学术规范，确保了研究结果的可靠性和有效性。我们采用了多种数据收集方法，包括在线调查、访谈和文献回顾等。
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：参数设置 -->
        <div class="lg:col-span-3">
          <div class="glass-strong bg-[#fffbf5] rounded-xl shadow-sm border border-[#b8860b]/20">
            <div class="p-4 border-b border-[#b8860b]/10 flex items-center justify-between">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">参数设置</h2>
              <div class="flex items-center space-x-2">
                <span class="text-sm text-[#6b6b6b]">只读</span>
                <button
                  @click="isReadonly = !isReadonly"
                  :disabled="currentTemplate?.template_type === 'system'"
                  class="relative w-10 h-6 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :class="isReadonly ? 'bg-[#b8860b]' : 'bg-[#b8860b]/40'"
                >
                  <span
                    class="absolute top-1 w-4 h-4 bg-white rounded-full transition-transform"
                    :class="isReadonly ? 'left-5' : 'left-1'"></span>
                </button>
              </div>
            </div>

            <!-- 系统模板提示 -->
            <div v-if="currentTemplate?.template_type === 'system'" class="mx-4 mt-4 p-3 bg-[#f5edd7] border border-[#b8860b]/30 rounded-lg flex items-start">
              <svg class="w-5 h-5 text-[#b8860b] mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              <div class="flex-1">
                <p class="text-sm text-[#b8860b]">系统模板为只读模式，不可直接修改</p>
                <p class="text-xs text-[#9a9a9a] mt-1">如需自定义，请使用"保存为副本"功能</p>
              </div>
            </div>

            <div class="p-4 space-y-6">
              <!-- 页边距 -->
              <div>
                <h3 class="text-sm font-medium text-[#2d2d2d] mb-3 flex items-center space-x-1">
                  <span>页边距</span>
                  <div class="w-1 h-1 bg-[#b8860b]/20 rounded-full"></div>
                </h3>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">上边距</label>
                    <input
                      v-model.number="localConfig.page.margins.top_cm"
                      :disabled="isReadonly"
                      type="number"
                      step="0.1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">下边距</label>
                    <input
                      v-model.number="localConfig.page.margins.bottom_cm"
                      :disabled="isReadonly"
                      type="number"
                      step="0.1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">左边距</label>
                    <input
                      v-model.number="localConfig.page.margins.left_cm"
                      :disabled="isReadonly"
                      type="number"
                      step="0.1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">右边距</label>
                    <input
                      v-model.number="localConfig.page.margins.right_cm"
                      :disabled="isReadonly"
                      type="number"
                      step="0.1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                </div>
              </div>

              <!-- 标题样式 -->
              <div
                v-for="(heading, index) in localConfig.headings"
                :key="'heading-' + index"
                class="border-t border-[#b8860b]/10 pt-4"
              >
                <h3 class="text-sm font-medium text-[#2d2d2d] mb-3 flex items-center space-x-1">
                  <span>{{ ['一', '二', '三'][index] || (index + 1) }}级标题</span>
                  <div class="w-1 h-1 bg-[#b8860b]/20 rounded-full"></div>
                </h3>
                <div class="space-y-3">
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">字体</label>
                    <select
                      v-model="heading.font"
                      :disabled="isReadonly"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <option value="SimHei">黑体</option>
                      <option value="SimSun">宋体</option>
                      <option value="KaiTi">楷体</option>
                      <option value="FangSong">仿宋</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">字号 (pt)</label>
                    <input
                      v-model.number="heading.size_pt"
                      :disabled="isReadonly"
                      type="number"
                      step="0.5"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div class="flex items-center space-x-4">
                    <label class="flex items-center">
                      <input
                        v-model="heading.bold"
                        :disabled="isReadonly"
                        type="checkbox"
                        class="w-4 h-4 text-[#b8860b] border-[#b8860b]/30 rounded focus:ring-0 focus:border-[#b8860b] disabled:cursor-not-allowed disabled:opacity-60"
                      />
                      <span class="ml-2 text-sm text-[#6b6b6b]">加粗</span>
                    </label>
                    <div>
                      <label class="text-xs text-[#6b6b6b] block mb-1">对齐</label>
                      <select
                        v-model="heading.alignment"
                        :disabled="isReadonly"
                        class="px-2 py-1 border border-[#b8860b]/20 rounded text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        <option value="center">居中</option>
                        <option value="left">左对齐</option>
                        <option value="right">右对齐</option>
                        <option value="justify">两端对齐</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 正文样式 -->
              <div class="border-t border-[#b8860b]/10 pt-4">
                <h3 class="text-sm font-medium text-[#2d2d2d] mb-3 flex items-center space-x-1">
                  <span>正文</span>
                  <div class="w-1 h-1 bg-[#b8860b]/20 rounded-full"></div>
                </h3>
                <div class="space-y-3">
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">字体</label>
                    <select
                      v-model="localConfig.body.font"
                      :disabled="isReadonly"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <option value="SimSun">宋体</option>
                      <option value="SimHei">黑体</option>
                      <option value="KaiTi">楷体</option>
                      <option value="FangSong">仿宋</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">字号 (pt)</label>
                    <input
                      v-model.number="localConfig.body.size_pt"
                      :disabled="isReadonly"
                      type="number"
                      step="0.5"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">行距 (pt)</label>
                    <input
                      v-model.number="localConfig.body.line_spacing_pt"
                      :disabled="isReadonly"
                      type="number"
                      step="1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                  <div>
                    <label class="text-xs text-[#6b6b6b] block mb-1">首行缩进 (字符)</label>
                    <input
                      v-model.number="localConfig.body.first_line_indent_chars"
                      :disabled="isReadonly"
                      type="number"
                      step="1"
                      class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:ring-0 focus:border-[#b8860b] focus:border-transparent outline-none transition-all disabled:bg-[#faf8f3] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="p-4 border-t border-[#b8860b]/10 space-y-2">
              <button
                v-if="currentTemplate?.template_type === 'system'"
                @click="saveAsCopy"
                class="w-full px-4 py-2.5 bg-[#b8860b] text-white rounded-lg hover:bg-[#d4a84b] transition-colors text-sm font-heading font-medium"
              >
                保存为副本
              </button>
              <button
                v-else
                @click="updateTemplate"
                :disabled="isReadonly"
                class="w-full px-4 py-2.5 bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white rounded-lg hover:shadow-lg transition-all text-sm font-heading font-medium disabled:bg-[#b8860b] disabled:cursor-not-allowed disabled:opacity-60"
              >
                保存修改
              </button>
              <button
                v-if="currentTemplate?.template_type === 'custom'"
                @click="deleteTemplate"
                class="w-full px-4 py-2.5 border-2 border-[#c8102e] text-[#c8102e] rounded-lg hover:bg-[#f5e0e5] transition-colors text-sm font-heading font-medium"
              >
                删除模板
              </button>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { ruleTemplateApi } from '@/api'

const router = useRouter()

// 数据
const templates = ref([])
const currentTemplate = ref(null)
const isReadonly = ref(true)

// 展开状态
const systemTemplatesExpanded = ref(true)
const customTemplatesExpanded = ref(true)

// A4 尺寸 (1cm ≈ 37.8px)
const a4Width = 794 // 21cm
const a4Height = 1123 // 29.7cm

// 本地配置（用于实时预览）
const localConfig = ref({
  page: {
    margins: { top_cm: 2.5, bottom_cm: 2.5, left_cm: 3, right_cm: 2.5 },
    paper_name: 'A4'
  },
  headings: [
    { level: 1, font: 'SimHei', size_pt: 16, bold: true, alignment: 'center' },
    { level: 2, font: 'SimHei', size_pt: 14, bold: true, alignment: 'left' },
    { level: 3, font: 'SimHei', size_pt: 13, bold: true, alignment: 'left' }
  ],
  body: {
    font: 'SimSun',
    size_pt: 12,
    line_spacing_pt: 25,
    first_line_indent_chars: 2
  }
})

// 计算属性
const systemTemplates = computed(() => {
  return templates.value.filter(t => t.template_type === 'system')
})

const customTemplates = computed(() => {
  return templates.value.filter(t => t.template_type === 'custom')
})

const config = computed(() => localConfig.value)

const configMargins = computed(() => {
  const m = localConfig.value.page.margins
  return `${m.top_cm * 37.8}px ${m.right_cm * 37.8}px ${m.bottom_cm * 37.8}px ${m.left_cm * 37.8}px`
})

// 方法
const toggleSystemTemplates = () => {
  systemTemplatesExpanded.value = !systemTemplatesExpanded.value
}

const toggleCustomTemplates = () => {
  customTemplatesExpanded.value = !customTemplatesExpanded.value
}

const selectTemplate = (template) => {
  currentTemplate.value = template
  localConfig.value = JSON.parse(JSON.stringify(template.config))
  isReadonly.value = template.template_type === 'system'
}

const getHeadingStyle = (level) => {
  const heading = localConfig.value.headings.find(h => h.level === level)
  if (!heading) return {}

  return {
    fontFamily: heading.font,
    fontSize: heading.size_pt + 'pt',
    fontWeight: heading.bold ? 'bold' : 'normal',
    textAlign: heading.alignment
  }
}

const getBodyStyle = () => {
  const body = localConfig.value.body
  const lineHeightPt = body.line_spacing_pt
  const lineHeightEm = lineHeightPt / body.size_pt

  return {
    fontFamily: body.font,
    fontSize: body.size_pt + 'pt',
    lineHeight: lineHeightEm.toFixed(2),
    textIndent: body.first_line_indent_chars + 'em',
    textAlign: 'justify'
  }
}

const saveAsCopy = async () => {
  try {
    const name = currentTemplate.value.name + ' (副本)'
    const description = currentTemplate.value.description || ''

    await ruleTemplateApi.createTemplate(name, description, localConfig.value)
    ElMessage.success({ message: '已保存为副本', showClose: true })
    await loadTemplates()
  } catch (error) {
    ElMessage.error({ message: '保存失败', showClose: true })
  }
}

const updateTemplate = async () => {
  try {
    await ruleTemplateApi.updateTemplate(
      currentTemplate.value.id,
      currentTemplate.value.name,
      currentTemplate.value.description,
      localConfig.value
    )
    ElMessage.success({ message: '保存成功', showClose: true })
    await loadTemplates()
  } catch (error) {
    ElMessage.error({ message: '保存失败', showClose: true })
  }
}

const deleteTemplate = async (templateToDelete = null) => {
  try {
    await ElMessageBox.confirm('确定要删除此模板吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const templateId = templateToDelete ? templateToDelete.id : currentTemplate.value.id
    await ruleTemplateApi.deleteTemplate(templateId)
    ElMessage.success({ message: '删除成功', showClose: true })

    if (currentTemplate.value && currentTemplate.value.id === templateId) {
      currentTemplate.value = null
    }

    await loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error({ message: error.response?.data?.message || '删除失败', showClose: true })
    }
  }
}

const loadTemplates = async () => {
  try {
    const res = await ruleTemplateApi.getTemplates()
    if (res.data.code === 200) {
      templates.value = res.data.data.templates

      if (!currentTemplate.value && templates.value.length > 0) {
        const defaultTemplate = templates.value.find(t => t.is_default) || templates.value[0]
        selectTemplate(defaultTemplate)
      }
    }
  } catch (error) {
    ElMessage.error({ message: '加载模板失败', showClose: true })
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  opacity: 1;
}
</style>
