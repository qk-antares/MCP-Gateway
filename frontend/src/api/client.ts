import type { ServerInfo, ToolInfo, CreateServerRequest } from '../types'

const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `请求失败: ${res.status}`)
  }
  return res.json()
}

export async function fetchServers(): Promise<ServerInfo[]> {
  const data = await request<{ servers: ServerInfo[] }>('/servers')
  return data.servers
}

export async function createServer(req: CreateServerRequest): Promise<ServerInfo> {
  const data = await request<{ server: ServerInfo }>('/servers', {
    method: 'POST',
    body: JSON.stringify(req),
  })
  return data.server
}

export async function deleteServer(id: number): Promise<void> {
  await request(`/servers/${id}`, { method: 'DELETE' })
}

export async function fetchServerTools(serverId: number): Promise<ToolInfo[]> {
  const data = await request<{ tools: ToolInfo[] }>(`/servers/${serverId}/tools`)
  return data.tools
}

export async function fetchOAuthUrl(serverId: number): Promise<string | null> {
  const data = await request<{ oauth_url: string | null }>(`/servers/${serverId}/oauth-url`)
  return data.oauth_url
}
