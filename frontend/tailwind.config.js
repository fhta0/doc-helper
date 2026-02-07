/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 参考 HTML 中的配色方案
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#1A365D', // 深蓝色，用于按钮等
        },
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
        // 确保蓝色和紫色透明度可用
        blue: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['PingFang SC', 'Microsoft YaHei UI', 'Noto Sans SC', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
  // 关键：告诉 Tailwind 需要生成 group-hover 变体
  corePlugins: {},
  variants: {
    extend: {
      opacity: ['group-hover'],
      display:  ['group-hover'],   // 如果以后还想 group-hover:block 之类也顺手加上
    },
  },
}

