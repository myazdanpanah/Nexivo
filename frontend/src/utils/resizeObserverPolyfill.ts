/**
 * Lightweight ResizeObserver polyfill for older browsers.
 *
 * ResizeObserver is natively supported in Chrome 64+, Firefox 69+,
 * Safari 13.1+, Edge 79+. This shim provides a no-op fallback
 * for rare legacy environments.
 */
if (typeof window !== 'undefined' && typeof window.ResizeObserver === 'undefined') {
  // Minimal shim using MutationObserver + poll for size changes
  const observedElements = new WeakMap<Element, { width: number; height: number }>()

  class ResizeObserverShim {
    private callback: ResizeObserverCallback
    private targets = new Set<Element>()
    private rafId: number | null = null

    constructor(callback: ResizeObserverCallback) {
      this.callback = callback
    }

    observe(target: Element) {
      this.targets.add(target)
      const rect = target.getBoundingClientRect()
      observedElements.set(target, { width: rect.width, height: rect.height })
      this.startPolling()
    }

    unobserve(target: Element) {
      this.targets.delete(target)
      observedElements.delete(target)
      if (this.targets.size === 0) {
        this.stopPolling()
      }
    }

    disconnect() {
      this.targets.clear()
      this.stopPolling()
    }

    private startPolling() {
      if (this.rafId !== null) return
      const poll = () => {
        const entries: ResizeObserverEntry[] = []
        this.targets.forEach((target) => {
          const rect = target.getBoundingClientRect()
          const prev = observedElements.get(target)
          if (prev && (prev.width !== rect.width || prev.height !== rect.height)) {
            observedElements.set(target, { width: rect.width, height: rect.height })
            const contentRect = { x: 0, y: 0, width: rect.width, height: rect.height, top: 0, left: 0, bottom: rect.height, right: rect.width } as DOMRectReadOnly
          entries.push({
              target,
              contentRect,
              borderBoxSize: [],
              contentBoxSize: [],
              devicePixelContentBoxSize: [],
              toJSON: () => contentRect.toJSON(),
            } as ResizeObserverEntry)
          }
        })
        if (entries.length > 0) {
          this.callback(entries, this as unknown as ResizeObserver)
        }
        this.rafId = requestAnimationFrame(poll)
      }
      this.rafId = requestAnimationFrame(poll)
    }

    private stopPolling() {
      if (this.rafId !== null) {
        cancelAnimationFrame(this.rafId)
        this.rafId = null
      }
    }
  }

  // ResizeObserverShim implements the ResizeObserver interface (observe, unobserve, disconnect)
  // but doesn't perfectly match the constructor signature — safe to cast here.
  window.ResizeObserver = ResizeObserverShim as unknown as typeof ResizeObserver
}
