'use client'

import { useEffect, useRef, useState } from 'react'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type Session = {
  id: string
  title: string
}

const API_BASE = 'http://localhost:8000'
const SESSIONS_KEY = 'hia_sessions'
const ACTIVE_KEY = 'hia_active_session_id'
const LEGACY_KEY = 'hia_session_id'

function loadSessions(): Session[] {
  const raw = localStorage.getItem(SESSIONS_KEY)
  if (raw) {
    try {
      return JSON.parse(raw) as Session[]
    } catch {
      /* fall through */
    }
  }
  const legacy = localStorage.getItem(LEGACY_KEY)
  if (legacy) {
    const migrated: Session[] = [{ id: legacy, title: 'Sesi 1' }]
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(migrated))
    return migrated
  }
  return []
}

function saveSessions(sessions: Session[]) {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions))
}

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeId, setActiveId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let loaded = loadSessions()
    let active = localStorage.getItem(ACTIVE_KEY) || ''

    if (loaded.length === 0) {
      const id = crypto.randomUUID()
      loaded = [{ id, title: 'Sesi 1' }]
      active = id
      saveSessions(loaded)
      localStorage.setItem(ACTIVE_KEY, id)
    } else if (!active || !loaded.find((s) => s.id === active)) {
      active = loaded[0].id
      localStorage.setItem(ACTIVE_KEY, active)
    }

    setSessions(loaded)
    setActiveId(active)
  }, [])

  useEffect(() => {
    if (!activeId) return
    let cancelled = false

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/chat/history?session_id=${activeId}`)
        const data = await res.json()
        if (!cancelled) setMessages(data.messages || [])
      } catch {
        if (!cancelled) setMessages([])
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [activeId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function newChat() {
    const id = crypto.randomUUID()
    const title = `Sesi ${sessions.length + 1}`
    const updated = [...sessions, { id, title }]
    setSessions(updated)
    saveSessions(updated)
    setActiveId(id)
    localStorage.setItem(ACTIVE_KEY, id)
    setMessages([])
  }

  function switchTo(id: string) {
    if (id === activeId) return
    setActiveId(id)
    localStorage.setItem(ACTIVE_KEY, id)
  }

  async function send() {
    const text = input.trim()
    if (!text || loading || !activeId) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: activeId }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: could not reach the server.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex h-screen">
      <aside className="w-64 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={newChat}
            className="w-full rounded-xl bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700"
          >
            + New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => switchTo(s.id)}
              className={`w-full text-left rounded-lg px-3 py-2 text-sm truncate ${
                s.id === activeId
                  ? 'bg-gray-200 dark:bg-gray-700 font-medium'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-lg font-semibold">Health Intelligence Agent</h1>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 text-sm mt-8">
              Start by telling me what you ate, or ask for your daily summary.
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-2 text-sm text-gray-400">
                Thinking…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
          <input
            className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Type a message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={loading}
          />
          <button
            className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-blue-700 transition-colors"
            onClick={send}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
