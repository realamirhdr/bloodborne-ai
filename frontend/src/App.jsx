import { useState, useRef, useEffect } from 'react'
import styles from './App.module.css'
import Sidebar from './Sidebar.jsx'
import {
  loadConversations, loadConversation, saveConversation,
  deleteConversation, newId,
} from './storage.js'

const API_URL = import.meta.env.VITE_API_URL ?? ''
const WELCOME = { role: 'assistant', content: 'Good evening, Hunter. What knowledge do you seek?' }

function blankConv(id) {
  const now = Date.now()
  return { id, title: 'New hunt', messages: [WELCOME], history: [], createdAt: now, updatedAt: now }
}

export default function App() {
  const [convList, setConvList] = useState(() => loadConversations())
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const history = useRef([])
  const bottomRef = useRef(null)

  // Load most recent conversation on first render
  useEffect(() => {
    const sorted = [...loadConversations()].sort((a, b) => b.updatedAt - a.updatedAt)
    if (sorted.length > 0) loadConv(sorted[0].id)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function loadConv(id) {
    const conv = loadConversation(id)
    if (!conv) return
    setActiveId(id)
    setMessages(conv.messages)
    history.current = conv.history
    setInput('')
  }

  function startNew() {
    const id = newId()
    const conv = blankConv(id)
    setConvList(saveConversation(conv))
    setActiveId(id)
    setMessages([WELCOME])
    history.current = []
    setInput('')
  }

  function handleDelete(id) {
    const updated = deleteConversation(id)
    setConvList(updated)
    if (id === activeId) {
      const next = [...updated].sort((a, b) => b.updatedAt - a.updatedAt)[0]
      if (next) loadConv(next.id)
      else { setActiveId(null); setMessages([WELCOME]); history.current = [] }
    }
  }

  async function send() {
    const message = input.trim()
    if (!message || loading) return

    // Create a conversation if none is active
    let convId = activeId
    if (!convId) {
      convId = newId()
      const conv = blankConv(convId)
      setConvList(saveConversation(conv))
      setActiveId(convId)
    }

    const snapshot = messages // messages before this turn
    setInput('')
    setLoading(true)
    setMessages(prev => [
      ...prev,
      { role: 'user', content: message },
      { role: 'assistant', content: '', streaming: true },
    ])

    try {
      const resp = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: history.current }),
      })
      if (!resp.ok) throw new Error(`${resp.status}`)

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let answer = ''
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            answer += JSON.parse(data)
            setMessages(prev => [...prev.slice(0, -1), { role: 'assistant', content: answer, streaming: true }])
          } catch { /* skip */ }
        }
      }

      const newHistory = [...history.current,
        { role: 'user', content: message },
        { role: 'assistant', content: answer },
      ]
      history.current = newHistory

      const finalMessages = [
        ...snapshot,
        { role: 'user', content: message },
        { role: 'assistant', content: answer },
      ]
      setMessages(finalMessages)

      const existing = loadConversation(convId)
      const now = Date.now()
      const conv = {
        id: convId,
        title: existing?.title === 'New hunt' ? message.slice(0, 52) : (existing?.title ?? message.slice(0, 52)),
        messages: finalMessages,
        history: newHistory,
        createdAt: existing?.createdAt ?? now,
        updatedAt: now,
      }
      setConvList(saveConversation(conv))

    } catch {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: 'The connection to the workshop has been severed. Please try again.' },
      ])
    }

    setLoading(false)
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className={styles.app}>
      <Sidebar
        conversations={convList}
        activeId={activeId}
        onSelect={loadConv}
        onNew={startNew}
        onDelete={handleDelete}
      />

      <div className={styles.main}>
        <header className={styles.header}>
          <h1 className={styles.title}>BLOODBORNE</h1>
          <p className={styles.subtitle}>Lore Expert &mdash; Ask about hunters, Great Ones, locations &amp; weapons</p>
        </header>

        <main className={styles.messages}>
          {messages.map((msg, i) => (
            <div key={i} className={`${styles.message} ${styles[msg.role]}`}>
              {msg.role === 'assistant' && <span className={styles.label}>HUNTER</span>}
              <p className={styles.body}>
                {msg.content}
                {msg.streaming && <span className={styles.cursor}>▋</span>}
                {msg.streaming && !msg.content && <span className={styles.thinking}>…</span>}
              </p>
            </div>
          ))}
          <div ref={bottomRef} />
        </main>

        <footer className={styles.footer}>
          <textarea
            className={styles.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about Bloodborne lore…"
            disabled={loading}
            rows={2}
          />
          <button className={styles.sendBtn} onClick={send} disabled={loading}>
            {loading ? '…' : 'Send'}
          </button>
        </footer>
      </div>
    </div>
  )
}
