'use client'

import { useEffect, useRef, useState } from 'react'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

const API_URL = 'http://localhost:8000/chat'

function getSessionId(): string {
  const key = 'hia_session_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(key, id)
  }
  return id
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const sessionId = useRef<string>('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    sessionId.current = getSessionId()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId.current }),
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
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
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
  )
}
