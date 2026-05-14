import { useState } from 'react'
import type { CreateServerRequest } from '../types'

interface Props {
  onSubmit: (data: CreateServerRequest) => Promise<void>
  onClose: () => void
}

export default function AddServerModal({ onSubmit, onClose }: Props) {
  const [form, setForm] = useState<CreateServerRequest>({
    name: '',
    transport_type: 'http',
    url: '',
    command: '',
    auth_type: 'none',
  })
  const [authValue, setAuthValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setError('')
    const data: CreateServerRequest = {
      name: form.name.trim(),
      transport_type: form.transport_type,
      auth_type: form.auth_type,
    }

    if (form.transport_type === 'http') {
      data.url = form.url?.trim()
    } else {
      const parts = (form.command || '').trim().split(/\s+/)
      data.command = parts[0]
      if (parts.length > 1) data.args = parts.slice(1)
    }

    if (form.auth_type === 'api_key' && authValue.trim()) {
      data.auth_config = { api_key: authValue.trim() }
    } else if (form.auth_type === 'bearer' && authValue.trim()) {
      data.auth_config = { token: authValue.trim() }
    }

    setSubmitting(true)
    try {
      await onSubmit(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : '添加失败')
    } finally {
      setSubmitting(false)
    }
  }

  const update = (patch: Partial<CreateServerRequest>) => setForm((f) => ({ ...f, ...patch }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">添加 MCP Server</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
            <input
              value={form.name}
              onChange={(e) => update({ name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="例如: GitHub MCP"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">协议类型</label>
            <div className="flex gap-2">
              {(['http', 'stdio'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => update({ transport_type: type })}
                  className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${
                    form.transport_type === type
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  {type.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {form.transport_type === 'http' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
              <input
                value={form.url || ''}
                onChange={(e) => update({ url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                placeholder="http://localhost:8080/mcp"
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">命令</label>
              <input
                value={form.command || ''}
                onChange={(e) => update({ command: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                placeholder="uvx mcp-server-xxx --arg1 val1"
              />
              <p className="text-xs text-gray-400 mt-1">输入完整命令，空格分隔参数</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">认证方式</label>
            <select
              value={form.auth_type || 'none'}
              onChange={(e) => {
                update({ auth_type: e.target.value as CreateServerRequest['auth_type'] })
                setAuthValue('')
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="none">无认证</option>
              <option value="api_key">API Key</option>
              <option value="bearer">Bearer Token</option>
              <option value="oauth">OAuth</option>
            </select>
          </div>

          {(form.auth_type === 'api_key' || form.auth_type === 'bearer') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {form.auth_type === 'api_key' ? 'API Key' : 'Bearer Token'}
              </label>
              <input
                type="password"
                value={authValue}
                onChange={(e) => setAuthValue(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
              />
            </div>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 py-2 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !form.name.trim()}
              className="flex-1 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? '添加中...' : '添加'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
