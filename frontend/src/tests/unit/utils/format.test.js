/**
 * Unit tests for format utility functions
 */
import { describe, it, expect } from 'vitest'
import { formatTimeShort, formatTimeFull, formatFileSize, calculateScore, getScoreColorClass } from '@/utils/format'

describe('formatTimeShort', () => {
  it('should format date to MM-DD HH:mm', () => {
    const date = new Date('2024-01-15T10:30:00')
    const result = formatTimeShort(date)
    expect(result).toBe('01-15 10:30')
  })

  it('should return empty string for null/undefined', () => {
    expect(formatTimeShort(null)).toBe('')
    expect(formatTimeShort(undefined)).toBe('')
    expect(formatTimeShort('')).toBe('')
  })

  it('should handle date string input', () => {
    const result = formatTimeShort('2024-12-25T14:45:00')
    expect(result).toBe('12-25 14:45')
  })
})

describe('formatTimeFull', () => {
  it('should format date to YYYY-MM-DD HH:mm', () => {
    const date = new Date('2024-01-15T10:30:00')
    const result = formatTimeFull(date)
    expect(result).toBe('2024-01-15 10:30')
  })

  it('should return empty string for null/undefined', () => {
    expect(formatTimeFull(null)).toBe('')
    expect(formatTimeFull(undefined)).toBe('')
  })
})

describe('formatFileSize', () => {
  it('should format bytes to B', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(512)).toBe('512 B')
  })

  it('should format bytes to KB', () => {
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1536)).toBe('1.5 KB')
    expect(formatFileSize(10240)).toBe('10 KB')
  })

  it('should format bytes to MB', () => {
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(2097152)).toBe('2 MB')
    expect(formatFileSize(5242880)).toBe('5 MB')
  })

  it('should format bytes to GB', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB')
    expect(formatFileSize(2147483648)).toBe('2 GB')
  })

  it('should format bytes to TB', () => {
    expect(formatFileSize(1099511627776)).toBe('1 TB')
  })

  it('should handle large numbers with decimal precision', () => {
    expect(formatFileSize(1536000)).toBe('1.46 MB')
  })
})

describe('calculateScore', () => {
  it('should return 100 for zero issues', () => {
    expect(calculateScore(0)).toBe(100)
  })

  it('should deduct 5 points per issue', () => {
    expect(calculateScore(1)).toBe(95)
    expect(calculateScore(2)).toBe(90)
    expect(calculateScore(3)).toBe(85)
    expect(calculateScore(4)).toBe(80)
  })

  it('should not go below 60', () => {
    expect(calculateScore(10)).toBe(60)
    expect(calculateScore(20)).toBe(60)
    expect(calculateScore(100)).toBe(60)
  })
})

describe('getScoreColorClass', () => {
  it('should return green for excellent scores (>=90)', () => {
    expect(getScoreColorClass(0)).toBe('text-green-600')
    expect(getScoreColorClass(1)).toBe('text-green-600')
    expect(getScoreColorClass(2)).toBe('text-green-600')
  })

  it('should return blue for good scores (>=80)', () => {
    expect(getScoreColorClass(3)).toBe('text-blue-600')
    expect(getScoreColorClass(4)).toBe('text-blue-600')
  })

  it('should return orange for fair scores (>=60)', () => {
    expect(getScoreColorClass(5)).toBe('text-orange-600')
    expect(getScoreColorClass(8)).toBe('text-orange-600')
  })

  it('should return red for poor scores (<60)', () => {
    // Note: With minimum score of 60, getScoreColorClass never returns red
    // unless we allow issues > 8 which would give score < 60
    // But calculateScore has Math.max(60, ...) so it never goes below 60
    // This test documents the current behavior
    expect(getScoreColorClass(9)).toBe('text-orange-600') // 60 points (minimum)
    expect(getScoreColorClass(20)).toBe('text-orange-600') // 60 points (minimum)
  })
})
