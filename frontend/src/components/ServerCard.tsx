import { useState } from 'react'
import type { ServerInfo } from '../types'
import { fetchOAuthUrl } from '../api/client'

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
}

const STATUS_LABELS: Record<string, string> = {
  active: '已连接',
  pending: '连接中',
  error: '错误',
}

interface Props {
  server: ServerInfo
  selected: boolean
  onSelect: () => void
  onDelete: () => void
}

export default function ServerCard({ server, selected, onSelect, onDelete }: Props) {
  const [oauthLoading, setOauthLoading] = useState(false)

  const handleOAuthClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setOauthLoading(true)
    try {
      const url = await fetchOAuthUrl(server.id)
      if (url) {
        window.open(url, '_blank', 'width=600,height=700')
      }
    } finally {
      setOauthLoading(false)
    }
  }

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-lg border cursor-pointer transition-all ${
        selected ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-200 bg-white hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{server.name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-mono">
              {server.transport_type}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${STATUS_STYLES[server.status] || ''}`}>
              {STATUS_LABELS[server.status] || server.status}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-2 truncate">
            {server.transport_type === 'http' ? server.url : server.command}
          </p>
          <p className="text-xs text-gray-500 mt-1">{server.tool_count} 个工具</p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="ml-2 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
          title="删除"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      {server.status === 'pending' && server.auth_type === 'oauth' && (
        <button
          onClick={handleOAuthClick}
          disabled={oauthLoading}
          className="mt-2 w-full py-1.5 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50 transition-colors"
        >
          {oauthLoading ? '获取授权链接...' : '点击进行 OAuth 授权'}
        </button>
      )}
      {server.status === 'error' && server.error_message && (
        <p className="text-xs text-red-500 mt-2 truncate" title={server.error_message}>
          {server.error_message}
        </p>
      )}
    </div>
  )
}
