"""Tests for API client."""
import { vi, describe, it, expect, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios')

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct base URL', () => {
    expect(axios.defaults.baseURL).toBe('/api/v1')
  })

  it('should add auth header when token exists', async () => {
    localStorage.setItem('token', 'test-token')
    axios.get.mockResolvedValue({ data: {} })

    await axios.get('/auth/me')

    expect(axios.get).toHaveBeenCalledWith('/auth/me', {
      headers: expect.objectContaining({
        Authorization: 'Bearer test-token',
      }),
    })
    localStorage.removeItem('token')
  })
})
