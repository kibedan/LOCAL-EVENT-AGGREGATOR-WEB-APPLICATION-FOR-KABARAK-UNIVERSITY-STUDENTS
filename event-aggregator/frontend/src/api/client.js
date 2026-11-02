const BASE = '/api';

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // no JSON body (e.g. 204)
  }

  if (!res.ok) {
    const message = data?.error || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  me: (token) => request('/auth/me', { token }),
  schools: () => request('/auth/schools'),
  updateSchool: (school, token) => request('/auth/me/school', { method: 'PUT', body: { school }, token }),
  updateInterests: (interests, token) =>
    request('/auth/me/interests', { method: 'PUT', body: { interests }, token }),

  listEvents: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return request(`/events${qs ? `?${qs}` : ''}`);
  },
  getEvent: (id) => request(`/events/${id}`),
  submitEvent: (payload, token) => request('/events', { method: 'POST', body: payload, token }),
  updateEvent: (id, payload, token) => request(`/events/${id}`, { method: 'PUT', body: payload, token }),
  withdrawEvent: (id, token) => request(`/events/${id}`, { method: 'DELETE', token }),
  mySubmissions: (token) => request('/events/mine', { token }),

  listCategories: () => request('/categories'),

  pendingEvents: (token) => request('/admin/events/pending', { token }),
  approveEvent: (id, token, date) =>
    request(`/admin/events/${id}/approve`, { method: 'POST', body: date ? { date } : undefined, token }),
  importFromWebsite: (token) => request('/admin/scrape', { method: 'POST', token }),
  rejectEvent: (id, reason, token) =>
    request(`/admin/events/${id}/reject`, { method: 'POST', body: { reason }, token }),
  analytics: (token) => request('/admin/analytics', { token }),

  notifications: (token) => request('/notifications', { token }),
  markRead: (id, token) => request(`/notifications/${id}/read`, { method: 'POST', token }),
};
