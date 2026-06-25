import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './components/Toast'
import { useThemeStore, syncThemeClass } from './store/themeStore'
import './utils/resizeObserverPolyfill'
import './index.css'

function ThemeSync() {
  const dark = useThemeStore((s) => s.dark)
  useEffect(() => { syncThemeClass(dark) }, [dark])
  return null
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <ThemeSync />
        <App />
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
