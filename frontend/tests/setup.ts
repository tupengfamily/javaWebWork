/**
 * Vitest setup file
 * - global mocks
 * - Element Plus stubs
 */
import { vi } from 'vitest'

// Mock Element Plus icons (avoid heavy import in test)
vi.mock('@element-plus/icons-vue', () => ({}))
