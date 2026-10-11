const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api`
  : (typeof window !== 'undefined' && window.location.hostname.endsWith('onrender.com'))
    ? 'https://cpcrs-backend.onrender.com/api'
    : '/api'

function getAuthHeader() {
  const token = localStorage.getItem('cpcrs_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const headers = {
    ...getAuthHeader(),
    ...(options.headers || {}),
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type'] && options.body) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const data = isJson ? await response.json().catch(() => null) : null

  if (!response.ok || !data) {
    if (!isJson && response.ok) {
      throw new Error('Backend returned non-JSON response. Please verify API endpoint connectivity.')
    }
    const errorMsg = data?.detail || response.statusText || 'Request failed'
    const error = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export const api = {
  // Auth
  async login(email, password) {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    if (data?.access_token) {
      localStorage.setItem('cpcrs_token', data.access_token)
    }
    return data
  },

  async logout() {
    try {
      await request('/auth/logout', { method: 'POST' })
    } finally {
      localStorage.removeItem('cpcrs_token')
    }
  },

  async getMe() {
    return request('/auth/me')
  },

  // Users
  async getUsers(role = null) {
    const qs = role ? `?role=${encodeURIComponent(role)}` : ''
    return request(`/users${qs}`)
  },

  async createUser(userData) {
    return request('/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  },

  // Projects
  async getProjects() {
    return request('/projects')
  },

  async getProject(id) {
    return request(`/projects/${id}`)
  },

  async createProject(projectData) {
    return request('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    })
  },

  async updateProject(id, updateData) {
    return request(`/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    })
  },

  async deleteProject(id) {
    return request(`/projects/${id}`, {
      method: 'DELETE',
    })
  },

  async getProjectMembers(projectId) {
    return request(`/projects/${projectId}/members`)
  },

  async addProjectMember(projectId, userId) {
    return request(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    })
  },

  async removeProjectMember(projectId, userId) {
    return request(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    })
  },

  async getProjectRepositories(projectId) {
    return request(`/projects/${projectId}/repositories`)
  },

  async addProjectRepository(projectId, repoData) {
    return request(`/projects/${projectId}/repositories`, {
      method: 'POST',
      body: JSON.stringify(repoData),
    })
  },

  // Findings
  async getFindings(params = {}) {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.append(k, v)
    })
    const queryStr = qs.toString() ? `?${qs.toString()}` : ''
    return request(`/findings${queryStr}`)
  },

  async getFinding(id) {
    return request(`/findings/${id}`)
  },

  async createFinding(findingData) {
    return request('/findings', {
      method: 'POST',
      body: JSON.stringify(findingData),
    })
  },

  async deleteFinding(id) {
    return request(`/findings/${id}`, {
      method: 'DELETE',
    })
  },

  async submitForReview(id, resolutionDescription) {
    return request(`/findings/${id}/submit-for-review`, {
      method: 'POST',
      body: JSON.stringify({ resolution_description: resolutionDescription }),
    })
  },

  async updateFindingStatus(id, newStatus, reason = null) {
    return request(`/findings/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus, reason }),
    })
  },

  async getFeedback(findingId) {
    return request(`/findings/${findingId}/feedback`)
  },

  async addFeedback(findingId, body, parentFeedbackId = null) {
    return request(`/findings/${findingId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ body, parent_feedback_id: parentFeedbackId }),
    })
  },

  async getWorkHistory(findingId) {
    return request(`/findings/${findingId}/work-history`)
  },

  async addWorkHistory(findingId, body, entryType = 'progress_update') {
    return request(`/findings/${findingId}/work-history`, {
      method: 'POST',
      body: JSON.stringify({ body, entry_type: entryType }),
    })
  },

  async getStatusHistory(findingId) {
    return request(`/findings/${findingId}/status-history`)
  },

  async getAttachments(findingId) {
    return request(`/findings/${findingId}/attachments`)
  },

  async uploadAttachment(findingId, file, kind = 'supporting_evidence') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('attachment_kind', kind)
    return request(`/findings/${findingId}/attachments`, {
      method: 'POST',
      body: formData,
    })
  },

  getAttachmentDownloadUrl(attachmentId) {
    return `/api/attachments/${attachmentId}/download`
  },
}
