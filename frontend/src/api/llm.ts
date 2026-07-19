import api from './client'

// ─── LLM Providers ─────────────────────────────────────────────
export const getLLMProviders = () => api.get('/llm/providers/')
export const createLLMProvider = (data: Record<string, unknown>) => api.post('/llm/providers/', data)
export const updateLLMProvider = (id: number, data: Record<string, unknown>) => api.put(`/llm/providers/${id}/`, data)
export const deleteLLMProvider = (id: number) => api.delete(`/llm/providers/${id}/`)
export const activateLLMProvider = (id: number) => api.post(`/llm/providers/${id}/activate/`)
export const testLLMProvider = (providerId: number, message?: string) =>
  api.post('/llm/providers/test/', { provider_id: providerId, message: message || 'Hello, are you working?' })

// ─── Chat ───────────────────────────────────────────────────────
export const sendChatMessage = (data: { message: string; session_id?: number; feature?: string }) =>
  api.post('/llm/chat/', data)

// ─── Sessions ───────────────────────────────────────────────────
export const getChatSessions = () => api.get('/llm/sessions/')
export const getChatSession = (id: number) => api.get(`/llm/sessions/${id}/`)
export const deleteChatSession = (id: number) => api.delete(`/llm/sessions/${id}/delete/`)

// ─── Usage ──────────────────────────────────────────────────────
export const getLLMUsageStats = () => api.get('/llm/usage/')
