import { useEffect, useState } from 'react'
import type { ToolInfo, ServerInfo } from '../types'
import { fetchServerTools } from '../api/client'

interface Props {
  server: ServerInfo
}

export default function ToolList({ server }: Props) {
  const [tools, setTools] = useState<ToolInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchServerTools(server.id)
      .then(setTools)
      .catch(() => setTools([]))
      .finally(() => setLoading(false))
  }, [server.id])

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">{server.name} 的工具</h2>
      <p className="text-sm text-gray-500 mb-4">
        {server.transport_type === 'http' ? server.url : server.command}
      </p>

      {loading ? (
        <p className="text-sm text-gray-400 py-8 text-center">加载中...</p>
      ) : tools.length === 0 ? (
        <p className="text-sm text-gray-400 py-8 text-center">暂无工具</p>
      ) : (
        <div className="space-y-2">
          {tools.map((tool) => (
            <div key={tool.id} className="p-3 bg-white rounded-lg border border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 font-mono">{tool.name}</h4>
              {tool.description && (
                <p className="text-xs text-gray-500 mt-1">{tool.description}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
