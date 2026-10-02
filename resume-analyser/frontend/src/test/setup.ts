import '@testing-library/jest-dom/vitest'

// jsdom lacks ResizeObserver, which Recharts requires during rendering
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver
