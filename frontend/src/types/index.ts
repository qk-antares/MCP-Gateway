export interface ServerInfo {
  id: number
  name: string
  transport_type: 'http' | 'stdio'
  url?: string
  command?: string
  auth_type?: string
  status: 'pending' | 'active' | 'error' | 'disabled'
  error_message?: string
  tool_count: number
  created_at: string
  updated_at: string
}

export interface ToolInfo {
  id: number
  name: string
  description?: string
}

export interface CreateServerRequest {
  name: string
  transport_type: 'http' | 'stdio'
  url?: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  auth_type?: 'none' | 'api_key' | 'bearer' | 'oauth'
  auth_config?: Record<string, string>
}
