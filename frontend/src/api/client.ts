import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth
export const authApi = {
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// Datasets
export const datasetApi = {
  list: (params?: { skip?: number; limit?: number; public_only?: boolean }) =>
    api.get('/datasets', { params }),
  upload: (formData: FormData) =>
    api.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  get: (id: string) => api.get(`/datasets/${id}`),
  delete: (id: string) => api.delete(`/datasets/${id}`),
  getCleaningSuggestions: (id: string) =>
    api.get(`/datasets/${id}/cleaning/suggestions`),
  executeCleaning: (id: string, operations: any[]) =>
    api.post(`/datasets/${id}/cleaning/execute`, { operations }),
}

// Conversations
export const conversationApi = {
  list: (datasetId?: string) =>
    api.get('/conversations', { params: { dataset_id: datasetId } }),
  create: (data?: { dataset_id?: string; title?: string }) =>
    api.post('/conversations', data),
  get: (id: string) => api.get(`/conversations/${id}`),
  chat: (id: string, data: { message: string; code_execution?: boolean }) =>
    api.post(`/conversations/${id}/chat`, data),
  delete: (id: string) => api.delete(`/conversations/${id}`),
}

// Charts
export const chartApi = {
  generate: (data: {
    dataset_id: string
    chart_type: string
    x_column?: string
    y_column?: string
    title?: string
  }) => api.post('/charts/generate', data),
  getUrl: (chartId: string) => `${API_BASE}/charts/${chartId}`,
  suggest: (datasetId: string) => api.get(`/charts/suggest/${datasetId}`),
}

// Teams
export const teamApi = {
  list: () => api.get('/teams'),
  create: (data: { name: string }) => api.post('/teams', data),
  get: (id: string) => api.get(`/teams/${id}`),
  addMember: (id: string, email: string, role?: string) =>
    api.post(`/teams/${id}/members`, null, { params: { user_email: email, role } }),
  listMembers: (id: string) => api.get(`/teams/${id}/members`),
  removeMember: (id: string, userId: string) =>
    api.delete(`/teams/${id}/members/${userId}`),
}

export default api
