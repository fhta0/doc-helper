<template>
  <div class="min-h-screen bg-[#f7f4ed] pt-20">
    <!-- 页面标题 -->
    <div class="bg-[#fffbf5] border-b border-[#b8860b]/10 px-6 py-4">
      <div class="max-w-7xl mx-auto">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-heading font-bold text-[#1a1a1a]">新模板创建</h1>
            <p class="text-sm text-[#6b6b6b] mt-1">上传范文或输入格式要求，AI将自动解析并生成格式模板</p>
          </div>
          <button
            @click="goBack"
            class="px-4 py-2 border border-[#b8860b]/20 text-[#2d2d2d] rounded-lg hover:bg-[#f5edd7] transition-colors text-sm font-medium"
          >
            返回
          </button>
        </div>
      </div>
    </div>

    <!-- 主内容区 - 三栏布局 -->
    <div class="max-w-7xl mx-auto p-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- 左栏：输入区域 -->
        <div class="lg:col-span-4 space-y-6">
          <!-- 上传范文 -->
          <div class="glass-strong bg-[#fffbf5] rounded-xl border border-[#b8860b]/20">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">上传范文</h2>
            </div>
            <div class="p-4">
              <div
                @drop="handleDrop"
                @dragover.prevent
                @dragenter.prevent
                class="border-2 border-dashed border-[#b8860b]/30 rounded-lg p-6 text-center hover:border-[#b8860b] transition-colors cursor-pointer"
                :class="{ 'border-[#c8102e] bg-[#e8d5d9]/30': isDragging }"
                @click="triggerFileInput"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".docx,.doc"
                  class="hidden"
                  @change="handleFileSelect"
                >
                <svg class="w-12 h-12 text-[#b8860b]/50 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p class="text-sm text-[#6b6b6b] mb-1">拖拽文件到此处或点击上传</p>
                <p class="text-xs text-[#9a9a9a]">支持 DOC、DOCX 格式</p>
              </div>
              <div v-if="uploadedFile" class="mt-3 p-3 bg-[#e8d5d9]/30 rounded-lg flex items-center justify-between">
                <div class="flex items-center">
                  <svg class="w-8 h-8 text-[#c8102e] mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span class="text-sm text-[#2d2d2d]">{{ uploadedFile.name }}</span>
                </div>
                <button @click="clearFile" class="text-[#c8102e] hover:text-[#a00c24]">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 格式要求文字 -->
          <div class="glass-strong bg-[#fffbf5] rounded-xl border border-[#b8860b]/20">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">格式要求文字</h2>
            </div>
            <div class="p-4">
              <textarea
                v-model="formatText"
                class="w-full h-48 px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:border-[#b8860b] resize-none placeholder:text-[#9a9a9a]"
                placeholder="复制粘贴您的格式要求文字...&#10;&#10;示例：&#10;正文仿宋四号，行距25磅&#10;一级标题黑体三号居中&#10;二级标题黑体四号左对齐&#10;页边距上下2.5cm，左右3cm"
              ></textarea>
            </div>
          </div>

          <!-- 开始AI解析按钮 -->
          <button
            @click="startAIAnalysis"
            :disabled="!canStartAnalysis || isAnalyzing"
            class="w-full px-6 py-3 bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white rounded-xl hover:shadow-lg transition-all font-medium disabled:bg-[#d7d7d7] disabled:cursor-not-allowed flex items-center justify-center shadow-md"
          >
            <svg v-if="!isAnalyzing" class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <svg v-else class="w-5 h-5 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isAnalyzing ? 'AI解析中...' : '开始AI解析' }}
          </button>
        </div>

        <!-- 中栏：AI解析流 -->
        <div class="lg:col-span-4">
          <div class="glass-strong bg-[#fffbf5] rounded-xl border border-[#b8860b]/20 h-full">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">AI 解析流</h2>
            </div>
            <div class="p-6">
              <div v-if="!hasStartedAnalysis" class="text-center py-12">
                <svg class="w-16 h-16 text-[#b8860b]/30 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p class="text-[#6b6b6b]">等待输入内容后开始AI解析...</p>
              </div>

              <div v-else-if="isAnalyzing" class="text-center py-12">
                <div class="relative w-16 h-16 mx-auto mb-4">
                  <div class="absolute inset-0 border-4 border-[#f5edd7] rounded-full"></div>
                  <div class="absolute inset-0 border-4 border-transparent border-t-[#c8102e] rounded-full animate-spin"></div>
                  <div class="absolute inset-2 border-4 border-transparent border-r-[#b8860b] rounded-full animate-spin"></div>
                </div>
                <p class="text-[#2d2d2d] font-medium">AI正在解析格式要求...</p>
                <p class="text-sm text-[#9a9a9a] mt-2">这可能需要几秒钟</p>
              </div>

              <div v-else-if="analysisResult" class="space-y-4">
                <div class="flex items-start">
                  <svg class="w-6 h-6 text-[#2d5a4a] mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p class="font-heading font-medium text-[#1a1a1a]">解析成功！</p>
                    <p class="text-sm text-[#6b6b6b] mt-1">AI已成功提取格式模板配置</p>
                  </div>
                </div>

                <div class="border-t border-[#b8860b]/10 pt-4">
                  <p class="text-sm font-heading font-medium text-[#2d2d2d] mb-3">提取的配置项：</p>
                  <div class="space-y-2 text-sm max-h-96 overflow-y-auto">
                    <!-- 目录信息 -->
                    <template v-if="analysisResult.structure?.table_of_contents?.exists">
                      <div class="flex items-start text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#3d5a80] mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
                        </svg>
                        <div class="flex-1">
                          <div class="font-medium">目录</div>
                          <div class="text-xs text-[#9a9a9a] mt-1">
                            共 {{ analysisResult.structure.table_of_contents.entries?.length || 0 }} 个条目
                          </div>
                          <div v-if="analysisResult.structure.table_of_contents.entries?.length > 0" class="mt-2 space-y-1 max-h-32 overflow-y-auto">
                            <div v-for="(entry, idx) in analysisResult.structure.table_of_contents.entries.slice(0, 5)" :key="idx" class="text-xs text-[#9a9a9a] ml-4">
                              {{ '  '.repeat(entry.level - 1) }}{{ entry.title }} <span class="text-[#b5b5b5]">(页{{ entry.page_number || '?' }})</span>
                            </div>
                            <div v-if="analysisResult.structure.table_of_contents.entries.length > 5" class="text-xs text-[#b5b5b5] ml-4">
                              ...还有 {{ analysisResult.structure.table_of_contents.entries.length - 5 }} 个条目
                            </div>
                          </div>
                        </div>
                      </div>
                    </template>

                    <!-- 标题结构 -->
                    <template v-if="analysisResult.structure?.heading_structure?.flat?.length > 0">
                      <div class="flex items-start text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#3d5a80] mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div class="flex-1">
                          <div class="font-medium">标题结构</div>
                          <div class="text-xs text-[#9a9a9a] mt-1">
                            共 {{ analysisResult.structure.heading_structure.flat.length }} 个标题
                          </div>
                          <div class="mt-2 space-y-1 max-h-32 overflow-y-auto">
                            <div v-for="(heading, idx) in analysisResult.structure.heading_structure.flat.slice(0, 5)" :key="idx" class="text-xs text-[#9a9a9a] ml-4">
                              {{ '  '.repeat(heading.level - 1) }}[{{ heading.level }}级] {{ heading.text.substring(0, 30) }}{{ heading.text.length > 30 ? '...' : '' }}
                            </div>
                            <div v-if="analysisResult.structure.heading_structure.flat.length > 5" class="text-xs text-[#b5b5b5] ml-4">
                              ...还有 {{ analysisResult.structure.heading_structure.flat.length - 5 }} 个标题
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="border-t border-[#b8860b]/10 my-2"></div>
                    </template>
                    <!-- 页面设置 -->
                    <template v-if="analysisResult.page">
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        页边距：{{ analysisResult.page.margins?.top_cm }}cm / {{ analysisResult.page.margins?.bottom_cm }}cm / {{ analysisResult.page.margins?.left_cm }}cm / {{ analysisResult.page.margins?.right_cm }}cm
                      </div>
                      <div v-if="analysisResult.page.gutter_cm !== undefined" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        装订线：{{ analysisResult.page.gutter_cm }}cm
                      </div>
                      <div v-if="analysisResult.page.header_cm !== undefined" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        页眉：{{ analysisResult.page.header_cm }}cm
                      </div>
                      <div v-if="analysisResult.page.footer_cm !== undefined" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        页脚：{{ analysisResult.page.footer_cm }}cm
                      </div>
                      <div v-if="analysisResult.page.paper_name" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        纸张：{{ analysisResult.page.paper_name }}
                      </div>
                    </template>

                    <!-- 正文格式 -->
                    <template v-if="analysisResult.body">
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        正文字体：{{ getFontName(analysisResult.body.font) }} {{ analysisResult.body.size_pt }}pt
                      </div>
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        行距：{{ analysisResult.body.line_spacing_pt }}磅
                      </div>
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        首行缩进：{{ analysisResult.body.first_line_indent_chars }}字符
                      </div>
                      <div v-if="analysisResult.body.align_to_grid" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        对齐网格：是
                      </div>
                    </template>

                    <!-- 标题样式 -->
                    <template v-if="analysisResult.headings && analysisResult.headings.length > 0">
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        {{ analysisResult.headings.length }}级标题样式
                      </div>
                      <div v-for="heading in analysisResult.headings" :key="heading.level" class="flex items-center text-[#9a9a9a] ml-6">
                        <svg class="w-3 h-3 mr-2 text-[#b5b5b5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                        </svg>
                        {{ heading.level }}级：{{ getFontName(heading.font) }} {{ heading.size_pt }}pt{{ heading.bold ? ' 加粗' : '' }} {{ getAlignmentName(heading.alignment) }}
                      </div>
                    </template>

                    <!-- 页码设置 -->
                    <template v-if="analysisResult.page_number">
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        页码：{{ analysisResult.page_number.font }} {{ analysisResult.page_number.size_pt }}pt {{ getAlignmentName(analysisResult.page_number.alignment) }}
                      </div>
                      <div v-if="analysisResult.page_number.number_format" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        页码格式：{{ getNumberFormatName(analysisResult.page_number.number_format) }}
                      </div>
                      <div v-if="analysisResult.page_number.toc_number_format && analysisResult.page_number.toc_number_format !== analysisResult.page_number.number_format" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        目录页码：{{ getNumberFormatName(analysisResult.page_number.toc_number_format) }}
                      </div>
                    </template>

                    <!-- 表格样式 -->
                    <template v-if="analysisResult.table">
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        表格边框：{{ analysisResult.table.border_width_pt }}pt
                      </div>
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        表头：{{ getFontName(analysisResult.table.header_font) }} {{ analysisResult.table.header_size_pt }}pt
                      </div>
                      <div class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        表内：{{ getFontName(analysisResult.table.body_font) }} {{ analysisResult.table.body_size_pt }}pt，行距{{ analysisResult.table.line_spacing_pt }}磅
                      </div>
                    </template>

                    <!-- 图表标题 -->
                    <template v-if="analysisResult.table_caption || analysisResult.figure_caption">
                      <div v-if="analysisResult.table_caption" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        表格编号：{{ analysisResult.table_caption.format }}
                      </div>
                      <div v-if="analysisResult.figure_caption" class="flex items-center text-[#6b6b6b]">
                        <svg class="w-4 h-4 mr-2 text-[#2d5a4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        图编号：{{ analysisResult.figure_caption.format }}
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <div v-else-if="analysisError" class="text-center py-12">
                <svg class="w-16 h-16 text-[#c8102e]/60 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p class="text-[#c8102e] font-medium">解析失败</p>
                <p class="text-sm text-[#9a9a9a] mt-2">{{ analysisError }}</p>
                <button
                  @click="resetAnalysis"
                  class="mt-4 px-4 py-2 border border-[#b8860b]/20 text-[#2d2d2d] rounded-lg hover:bg-[#f5edd7] transition-colors text-sm"
                >
                  重新开始
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右栏：格式预览 -->
        <div class="lg:col-span-4">
          <div class="glass-strong bg-[#fffbf5] rounded-xl border border-[#b8860b]/20 h-full">
            <div class="p-4 border-b border-[#b8860b]/10">
              <h2 class="font-heading font-semibold text-[#1a1a1a]">格式预览</h2>
            </div>
            <div class="p-4">
              <!-- A4 预览 -->
              <div
                class="mx-auto bg-white shadow-md border border-[#b8860b]/20"
                style="width: 300px; min-height: 424px;"
                :style="getPreviewStyle()"
              >
                <div class="p-4">
                  <!-- 标题 -->
                  <div
                    v-if="analysisResult?.headings?.[0]"
                    class="text-center mb-3"
                    :style="getHeadingPreviewStyle(1)"
                  >
                    学术论文标题示例
                  </div>

                  <!-- 一级标题 -->
                  <div
                    v-if="analysisResult?.headings?.[0]"
                    class="mb-2"
                    :style="getHeadingPreviewStyle(1)"
                  >
                    一、引言
                  </div>

                  <!-- 正文 -->
                  <div
                    v-for="i in 3"
                    :key="i"
                    class="mb-2"
                    :style="getBodyPreviewStyle()"
                  >
                    本文探讨了学术论文格式规范的重要性及其在现代学术交流中的作用。
                  </div>

                  <!-- 二级标题 -->
                  <div
                    v-if="analysisResult?.headings?.[1]"
                    class="mb-2 mt-3"
                    :style="getHeadingPreviewStyle(2)"
                  >
                    二、研究方法
                  </div>

                  <!-- 正文 -->
                  <div
                    class="mb-2"
                    :style="getBodyPreviewStyle()"
                  >
                    本研究采用文献分析法和对比研究法。
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div v-if="analysisResult" class="mt-6 space-y-3">
                <div>
                  <label class="text-sm font-heading font-medium text-[#2d2d2d] block mb-2">模板名称</label>
                  <input
                    v-model="templateName"
                    type="text"
                    class="w-full px-3 py-2 bg-[#faf8f3] border border-[#b8860b]/20 rounded-lg text-sm focus:border-[#b8860b] placeholder:text-[#9a9a9a]"
                    placeholder="输入模板名称"
                  >
                </div>
                <button
                  @click="saveTemplate"
                  :disabled="isSaving"
                  class="w-full px-4 py-2 bg-gradient-to-r from-[#c8102e] to-[#a00c24] text-white rounded-lg hover:shadow-lg transition-all font-heading font-medium disabled:bg-[#d7d7d7] disabled:cursor-not-allowed flex items-center justify-center shadow-md"
                >
                  <svg v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ isSaving ? '保存中...' : '保存为自定义模板' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ruleTemplateApi } from '@/api'

const router = useRouter()

// 数据
const formatText = ref('')
const uploadedFile = ref(null)
const isDragging = ref(false)
const isAnalyzing = ref(false)
const isSaving = ref(false)
const hasStartedAnalysis = ref(false)
const analysisResult = ref(null)
const analysisError = ref(null)
const templateName = ref('')
const fileInput = ref(null)

// 计算属性
const canStartAnalysis = computed(() => {
  return formatText.value.trim().length > 0 || uploadedFile.value !== null
})

// 方法
const goBack = () => {
  router.push('/rules')
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    uploadedFile.value = file
  }
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file && (file.name.endsWith('.docx') || file.name.endsWith('.doc'))) {
    uploadedFile.value = file
  } else {
    ElMessage.warning({ message: '请上传 DOC 或 DOCX 格式的文件', showClose: true })
  }
}

const clearFile = () => {
  uploadedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const startAIAnalysis = async () => {
  if (!canStartAnalysis.value) return

  isAnalyzing.value = true
  hasStartedAnalysis.value = true
  analysisError.value = null
  analysisResult.value = null

  try {
      if (uploadedFile.value) {
        // 使用docx解析
        const res = await ruleTemplateApi.parseDocx(uploadedFile.value)
        if (res.data.code === 200) {
          // 合并config和structure信息
          analysisResult.value = {
            ...res.data.data.config,
            structure: res.data.data.structure
          }
          templateName.value = uploadedFile.value.name.replace(/\.(docx|doc)$/, '') + ' 模板'
        } else {
          throw new Error(res.data.message || '解析失败')
        }
    } else {
      // 使用文本解析
      const res = await ruleTemplateApi.parseText(formatText.value)
      if (res.data.code === 200) {
        analysisResult.value = res.data.data.config
        templateName.value = '自定义格式模板'
      } else {
        throw new Error(res.data.message || '解析失败')
      }
    }
  } catch (error) {
    console.error('AI analysis error:', error)
    analysisError.value = error.message || '解析过程中出现错误'
  } finally {
    isAnalyzing.value = false
  }
}

const resetAnalysis = () => {
  hasStartedAnalysis.value = false
  analysisResult.value = null
  analysisError.value = null
}

const saveTemplate = async () => {
  if (!templateName.value.trim()) {
    ElMessage.warning({ message: '请输入模板名称', showClose: true })
    return
  }

  if (isSaving.value) return

  isSaving.value = true
  try {
    await ruleTemplateApi.createTemplate(
      templateName.value,
      '通过AI解析创建的格式模板',
      analysisResult.value
    )
    ElMessage.success({ message: '模板保存成功', showClose: true })
    router.push('/rules')
  } catch (error) {
    ElMessage.error({ message: error.response?.data?.message || '保存失败', showClose: true })
  } finally {
    isSaving.value = false
  }
}

// 样式辅助方法
const getFontName = (font) => {
  const fontMap = {
    'SimSun': '宋体',
    'SimHei': '黑体',
    'KaiTi': '楷体',
    'FangSong': '仿宋'
  }
  return fontMap[font] || font
}

const getAlignmentName = (alignment) => {
  const alignmentMap = {
    'left': '左对齐',
    'center': '居中',
    'right': '右对齐',
    'justify': '两端对齐'
  }
  return alignmentMap[alignment] || alignment
}

const getNumberFormatName = (format) => {
  const formatMap = {
    'arabic': '阿拉伯数字(1,2,3)',
    'roman': '罗马数字(Ⅰ,Ⅱ,Ⅲ)'
  }
  return formatMap[format] || format
}

const getPreviewStyle = () => {
  if (!analysisResult.value) return {}

  const m = analysisResult.value.page?.margins || {}
  const scale = 0.5 // 预览缩放比例

  return {
    padding: `${(m.top_cm || 2.5) * 10 * scale}px ${(m.right_cm || 2.5) * 10 * scale}px ${(m.bottom_cm || 2.5) * 10 * scale}px ${(m.left_cm || 3) * 10 * scale}px`
  }
}

const getHeadingPreviewStyle = (level) => {
  const heading = analysisResult.value?.headings?.find(h => h.level === level)
  if (!heading) return {}

  return {
    fontFamily: heading.font,
    fontSize: Math.min(heading.size_pt, 14) + 'pt',
    fontWeight: heading.bold ? 'bold' : 'normal',
    textAlign: heading.alignment
  }
}

const getBodyPreviewStyle = () => {
  const body = analysisResult.value?.body || {}
  const lineHeightPt = body.line_spacing_pt || 25
  const lineHeightEm = lineHeightPt / (body.size_pt || 12)

  return {
    fontFamily: body.font || 'SimSun',
    fontSize: Math.min(body.size_pt || 12, 10) + 'pt',
    lineHeight: lineHeightEm.toFixed(2),
    textIndent: (body.first_line_indent_chars || 2) + 'em'
  }
}
</script>

<style scoped>
input[type="file"] {
  display: none;
}

/* 玻璃态效果 */
.glass-strong {
  background: rgba(255, 251, 245, 0.9);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(184, 134, 11, 0.2);
}
</style>
