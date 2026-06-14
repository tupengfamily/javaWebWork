/**
 * Tests for API modules
 * Use fetch mocking via vi.spyOn
 */
import { describe, it, expect, vi } from 'vitest'
import request from '@/utils/request'

describe('API request utility', () => {
  it('sends Authorization header when token exists', async () => {
    localStorage.setItem('token', 'test-token-123')
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ code: 0, message: 'ok', data: null }), {
        status: 200, headers: { 'Content-Type': 'application/json' }
      })
    )

    await request.get('/test')
    expect(fetchSpy).toHaveBeenCalled()
    const callArgs = fetchSpy.mock.calls[0]
    const reqInit = callArgs[1] as RequestInit
    const headers = reqInit.headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer test-token-123')

    fetchSpy.mockRestore()
  })

  it('omits Authorization header when no token', async () => {
    localStorage.removeItem('token')
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ code: 0, data: null }), { status: 200 })
    )

    await request.get('/test')
    const callArgs = fetchSpy.mock.calls[0]
    const reqInit = callArgs[1] as RequestInit
    const headers = reqInit.headers as Record<string, string>
    expect(headers['Authorization']).toBeUndefined()

    fetchSpy.mockRestore()
  })
})
