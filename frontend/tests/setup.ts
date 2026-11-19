import { disableAutoUnmount, enableAutoUnmount } from '@vue/test-utils'
import { afterEach, vi } from 'vitest'

// A single worker reuses the CommonJS test-utils module between test files.
disableAutoUnmount()
enableAutoUnmount(afterEach)
afterEach(() => vi.unstubAllGlobals())
