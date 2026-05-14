import { useEffect, useState, useCallback, useRef } from 'react'
import type { ServerInfo } from './types'
import { fetchServers, createServer, deleteServer } from './api/client'
import type { CreateServerRequest } from './types'
import Layout from './components/Layout'
import ServerList from './components/ServerList'
import AddServerModal from './components/AddServerModal'
import ToolList from './components/ToolList'

export default function App() {
  const [servers, setServers] = useState<ServerInfo[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadServers = useCallback(async () => {
    try {
      const list = await fetchServers()
      setServers(list)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadServers()
  }, [loadServers])

  // 轮询 pending 状态的 Server 直到状态变化
  useEffect(() => {
    const hasPending = servers.some((s) => s.status === 'pending')

    if (hasPending && !pollRef.current) {
      pollRef.current = setInterval(loadServers, 3000)
    } else if (!hasPending && pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [servers, loadServers])

  const selectedServer = servers.find((s) => s.id === selectedId) ?? null

  const handleAdd = async (data: CreateServerRequest) => {
    await createServer(data)
    setShowModal(false)
    await loadServers()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确认删除此 MCP Server？')) return
    await deleteServer(id)
    if (selectedId === id) setSelectedId(null)
    await loadServers()
  }

  if (loading) {
    return (
      <Layout>
        <p className="text-center text-gray-400 py-16">加载中...</p>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <ServerList
            servers={servers}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDelete={handleDelete}
            onAdd={() => setShowModal(true)}
          />
        </div>
        <div className="md:col-span-2">
          {selectedServer ? (
            <ToolList server={selectedServer} />
          ) : (
            <div className="text-center py-16 text-gray-400">
              <p className="text-sm">选择一个 MCP Server 查看工具列表</p>
            </div>
          )}
        </div>
      </div>

      {showModal && <AddServerModal onSubmit={handleAdd} onClose={() => setShowModal(false)} />}
    </Layout>
  )
}
