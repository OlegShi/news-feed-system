const API_BASE = '/v1'

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }

  return data
}

export async function register(username, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function login(username, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function publishPost(token, content) {
  return request('/me/feed', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ content }),
  })
}

export async function getFeed(token, offset = 0, limit = 20) {
  return request(`/me/feed?offset=${offset}&limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function addFriend(token, friendUsername) {
  return request('/me/friends', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ friend_username: friendUsername }),
  })
}

export async function getFriends(token) {
  return request('/me/friends', {
    headers: { Authorization: `Bearer ${token}` },
  })
}
