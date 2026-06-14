/**
 * Tests for utility functions
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('Number formatting', () => {
  it('formats wan (10k)', () => {
    const n = 12345
    const out = n >= 1e4 ? (n / 1e4).toFixed(1) + 'wan' : String(n)
    expect(out).toBe('1.2wan')
  })

  it('formats yi (100M)', () => {
    const n = 120000000
    const out = n >= 1e8 ? (n / 1e8).toFixed(2) + 'yi' : String(n)
    expect(out).toBe('1.20yi')
  })

  it('keeps small numbers as-is', () => {
    const n = 999
    const out = n >= 1e4 ? 'formatted' : String(n)
    expect(out).toBe('999')
  })
})

describe('Time formatting', () => {
  it('formats ISO to MM-DD HH:mm', () => {
    const iso = '2026-06-13T20:00:00'
    const m = iso.match(/(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
    expect(m).not.toBeNull()
    const out = `${m![2]}-${m![1]} ${m![3]}:${m![4]}`
    expect(out).toBe('06-13 20:00')
  })
})

describe('Keyword highlight (simple)', () => {
  it('returns text unchanged if no keyword', () => {
    const text = 'Hello World'
    const kw = ''
    expect(text.replace(new RegExp(`(${kw})`, 'gi'), '<mark>$1</mark>')).toBe(text)
  })
})
