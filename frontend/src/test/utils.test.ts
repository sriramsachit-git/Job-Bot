import { describe, it, expect } from 'vitest'
import { cn } from '../lib/utils'

describe('utils', () => {
  describe('cn', () => {
    it('merges class names correctly', () => {
      const result = cn('class1', 'class2')
      expect(result).toContain('class1')
      expect(result).toContain('class2')
    })

    it('handles conditional classes', () => {
      const result = cn('base', true && 'conditional')
      expect(result).toContain('base')
      expect(result).toContain('conditional')
    })

    it('handles undefined and null', () => {
      const result = cn('base', undefined, null, 'valid')
      expect(result).toContain('base')
      expect(result).toContain('valid')
      expect(result).not.toContain('undefined')
      expect(result).not.toContain('null')
    })
  })
})
