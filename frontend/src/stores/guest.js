import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { GUEST_STORAGE_KEY, GUEST_TOKEN_KEY, MAX_TRIAL_COUNT, MAX_HISTORY_COUNT } from '@/constants/guest'

export const useGuestStore = defineStore('guest', () => {
  // Load from localStorage or initialize
  const storedSession = JSON.parse(localStorage.getItem(GUEST_STORAGE_KEY) || 'null')

  const trialCount = ref(storedSession?.trialCount || 0)
  // 确保 history 始终是一个数组（即使 storedSession 是 null 或 history 是 undefined）
  const history = ref(Array.isArray(storedSession?.history) ? storedSession.history : [])

  // Computed: Check if user is in guest mode
  const isGuest = computed(() => {
    const guestToken = localStorage.getItem(GUEST_TOKEN_KEY)
    const regularToken = localStorage.getItem('token') || sessionStorage.getItem('token')
    return !!(guestToken && !regularToken)
  })

  // Computed properties
  const remainingTrials = computed(() => {
    return Math.max(0, MAX_TRIAL_COUNT - trialCount.value)
  })

  const hasTrialsRemaining = computed(() => {
    return remainingTrials.value > 0
  })

  const historyFull = computed(() => {
    return history.value.length >= MAX_HISTORY_COUNT
  })

  // Actions
  const incrementTrialCount = () => {
    trialCount.value++
    _saveToStorage()
  }

  const addToHistory = (checkRecord) => {
    // Check if history is full
    if (history.value.length >= MAX_HISTORY_COUNT) {
      return { success: false, message: `游客最多可保存 ${MAX_HISTORY_COUNT} 条检查记录，请登录解锁更多` }
    }

    const newRecord = {
      filename: checkRecord.filename,
      check_type: checkRecord.check_type || 'basic',
      status: checkRecord.status || 'completed',
      total_issues: checkRecord.total_issues || 0,
      created_at: checkRecord.created_at || new Date().toISOString(),
      result: checkRecord.result || null
    }

    history.value.unshift(newRecord)
    _saveToStorage()
    return { success: true, message: '检查记录已保存' }
  }

  const getHistory = () => {
    return history.value
  }

  const getHistoryForMigration = () => {
    // Return a copy of history for migration
    return [...history.value]
  }

  const clearHistory = () => {
    history.value = []
    _saveToStorage()
  }

  const clearSession = () => {
    trialCount.value = 0
    history.value = []
    localStorage.removeItem(GUEST_STORAGE_KEY)
  }

  const clearGuestToken = () => {
    localStorage.removeItem(GUEST_TOKEN_KEY)
    // 同时清理会话数据，避免数据残留
    localStorage.removeItem(GUEST_STORAGE_KEY)
  }

  const resetForMigration = () => {
    // Get session data for migration before clearing
    const sessionData = {
      trialCount: trialCount.value,
      history: [...history.value]
    }
    return sessionData
  }

  // Private helper
  const _saveToStorage = () => {
    const sessionData = {
      trialCount: trialCount.value,
      history: history.value
    }
    localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(sessionData))
  }

  return {
    trialCount,
    history,
    isGuest,
    remainingTrials,
    hasTrialsRemaining,
    historyFull,
    incrementTrialCount,
    addToHistory,
    getHistory,
    getHistoryForMigration,
    clearHistory,
    clearSession,
    clearGuestToken,
    resetForMigration,
    MAX_TRIAL_COUNT,
    MAX_HISTORY_COUNT
  }
})
