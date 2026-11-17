// all calls to the flask backend go through this function
export async function api(path, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = 'Bearer ' + token
  }

  const res = await fetch('/api' + path, {
    method: method,
    headers: headers,
    body: body ? JSON.stringify(body) : null,
  })

  let data = {}
  try {
    data = await res.json()
  } catch (e) {
    // some responses have no json body
  }

  if (res.status === 401 && token) {
    // token expired, send user to login
    localStorage.clear()
    window.location.href = '/login'
  }
  if (!res.ok) {
    throw new Error(data.message || data.msg || 'Something went wrong')
  }
  return data
}

export async function downloadFile(path, filename) {
  const res = await fetch('/api' + path, {
    headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
  })
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
}

export function getUser() {
  const text = localStorage.getItem('user')
  return text ? JSON.parse(text) : null
}
