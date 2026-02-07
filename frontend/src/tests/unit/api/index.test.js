/**
 * Unit tests for API module
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { checkApi, purchaseApi, userApi, ruleTemplateApi } from '@/api'

// Mock API module before importing
vi.mock('@/api', () => {
  const mockApi = {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }

  return {
    default: mockApi,
    checkApi: {
      upload: vi.fn(),
      submit: vi.fn(),
      getResult: vi.fn(),
      generateRevised: vi.fn(),
      getRecent: vi.fn(),
      getStats: vi.fn()
    },
    purchaseApi: {
      getPackages: vi.fn(),
      createOrder: vi.fn(),
      queryOrder: vi.fn(),
      closeOrder: vi.fn()
    },
    userApi: {
      getOrders: vi.fn()
    },
    ruleTemplateApi: {
      getTemplates: vi.fn(),
      getTemplate: vi.fn(),
      createTemplate: vi.fn(),
      updateTemplate: vi.fn(),
      deleteTemplate: vi.fn(),
      parseText: vi.fn(),
      parseDocx: vi.fn()
    }
  }
})

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

describe('API Module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('checkApi', () => {
    it('should call upload with file and check type', () => {
      const mockFile = new File(['content'], 'test.docx')
      checkApi.upload(mockFile, 'full')

      expect(checkApi.upload).toHaveBeenCalledWith(mockFile, 'full')
    })

    it('should call submit with correct params', () => {
      checkApi.submit('file_id_123', 'basic', 'test.docx', 5)

      expect(checkApi.submit).toHaveBeenCalledWith('file_id_123', 'basic', 'test.docx', 5)
    })

    it('should call getResult with checkId', () => {
      checkApi.getResult('check_id_456')

      expect(checkApi.getResult).toHaveBeenCalledWith('check_id_456')
    })

    it('should call generateRevised with checkId', () => {
      checkApi.generateRevised('check_id_789')

      expect(checkApi.generateRevised).toHaveBeenCalledWith('check_id_789')
    })

    it('should call getRecent with pagination params', () => {
      checkApi.getRecent(10, 5)

      expect(checkApi.getRecent).toHaveBeenCalledWith(10, 5)
    })

    it('should call getStats', () => {
      checkApi.getStats()

      expect(checkApi.getStats).toHaveBeenCalled()
    })
  })

  describe('purchaseApi', () => {
    it('should call getPackages', () => {
      purchaseApi.getPackages()

      expect(purchaseApi.getPackages).toHaveBeenCalled()
    })

    it('should call createOrder with data', () => {
      const orderData = {
        product_id: 1,
        payment_method: 'wechat_native'
      }
      purchaseApi.createOrder(orderData)

      expect(purchaseApi.createOrder).toHaveBeenCalledWith(orderData)
    })

    it('should call queryOrder with orderNo', () => {
      purchaseApi.queryOrder('ORDER_123')

      expect(purchaseApi.queryOrder).toHaveBeenCalledWith('ORDER_123')
    })

    it('should call closeOrder with orderNo', () => {
      purchaseApi.closeOrder('ORDER_456')

      expect(purchaseApi.closeOrder).toHaveBeenCalledWith('ORDER_456')
    })
  })

  describe('userApi', () => {
    it('should call getOrders with pagination', () => {
      userApi.getOrders(2, 20)

      expect(userApi.getOrders).toHaveBeenCalledWith(2, 20)
    })

    it('should call getOrders with default values', () => {
      userApi.getOrders()

      expect(userApi.getOrders).toHaveBeenCalled()
    })
  })

  describe('ruleTemplateApi', () => {
    it('should call getTemplates without filter', () => {
      ruleTemplateApi.getTemplates()

      expect(ruleTemplateApi.getTemplates).toHaveBeenCalledWith()
    })

    it('should call getTemplates with type filter', () => {
      ruleTemplateApi.getTemplates('custom')

      expect(ruleTemplateApi.getTemplates).toHaveBeenCalledWith('custom')
    })

    it('should call getTemplate with id', () => {
      ruleTemplateApi.getTemplate(5)

      expect(ruleTemplateApi.getTemplate).toHaveBeenCalledWith(5)
    })

    it('should call createTemplate with params', () => {
      const config = {
        page: { margins: { top_cm: 2.5 } },
        body: { font: 'SimSun', size_pt: 14 }
      }
      ruleTemplateApi.createTemplate('Academic', 'For academic papers', config)

      expect(ruleTemplateApi.createTemplate).toHaveBeenCalledWith('Academic', 'For academic papers', config)
    })

    it('should call updateTemplate with params', () => {
      const config = { page: { margins: { top_cm: 3.0 } } }
      ruleTemplateApi.updateTemplate(5, 'Updated Name', 'Updated description', config)

      expect(ruleTemplateApi.updateTemplate).toHaveBeenCalledWith(5, 'Updated Name', 'Updated description', config)
    })

    it('should call deleteTemplate with id', () => {
      ruleTemplateApi.deleteTemplate(10)

      expect(ruleTemplateApi.deleteTemplate).toHaveBeenCalledWith(10)
    })

    it('should call parseText with text', () => {
      ruleTemplateApi.parseText('要求使用宋体14磅字')

      expect(ruleTemplateApi.parseText).toHaveBeenCalledWith('要求使用宋体14磅字')
    })

    it('should call parseDocx with file', () => {
      const mockFile = new File(['content'], 'sample.docx')
      ruleTemplateApi.parseDocx(mockFile)

      expect(ruleTemplateApi.parseDocx).toHaveBeenCalledWith(mockFile)
    })
  })
})
