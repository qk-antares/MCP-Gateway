import type { ServerInfo } from '../types'
import ServerCard from './ServerCard'

interface Props {
  servers: ServerInfo[]
  selectedId: number | null
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  onAdd: () => void
}

export default function ServerList({ servers, selectedId, onSelect, onDelete, onAdd }: Props) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">MCP Servers</h2>
        <button
          onClick={onAdd}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 添加
        </button>
      </div>
      {servers.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">暂无 MCP Server</p>
          <p className="text-xs mt-1">点击上方"添加"按钮开始</p>
        </div>
      ) : (
        <div className="space-y-3">
          {servers.map((s) => (
            <ServerCard
              key={s.id}
              server={s}
              selected={selectedId === s.id}
              onSelect={() => onSelect(s.id)}
              onDelete={() => onDelete(s.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
