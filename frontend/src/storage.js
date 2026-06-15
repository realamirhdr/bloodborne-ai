const PREFIX = 'bb_conv_'
const INDEX_KEY = 'bb_conversations'
const MAX_BYTES = 10 * 1024 * 1024 // 10 MB

function usedBytes() {
  let total = 0
  for (const key of Object.keys(localStorage)) {
    if (key.startsWith('bb_')) {
      total += (key.length + (localStorage.getItem(key) ?? '').length) * 2
    }
  }
  return total
}

function readIndex() {
  try { return JSON.parse(localStorage.getItem(INDEX_KEY) ?? '[]') } catch { return [] }
}

function writeIndex(index) {
  localStorage.setItem(INDEX_KEY, JSON.stringify(index))
}

function evictOldest(index) {
  const sorted = [...index].sort((a, b) => a.updatedAt - b.updatedAt)
  let current = [...index]
  while (usedBytes() > MAX_BYTES && current.length > 1) {
    const victim = sorted.shift()
    localStorage.removeItem(PREFIX + victim.id)
    current = current.filter(c => c.id !== victim.id)
    writeIndex(current)
  }
  return current
}

export function loadConversations() {
  return readIndex()
}

export function loadConversation(id) {
  try { return JSON.parse(localStorage.getItem(PREFIX + id) ?? 'null') } catch { return null }
}

export function saveConversation(conv) {
  const index = readIndex()
  const entry = { id: conv.id, title: conv.title, createdAt: conv.createdAt, updatedAt: conv.updatedAt }
  const pos = index.findIndex(c => c.id === conv.id)
  if (pos >= 0) index[pos] = entry
  else index.push(entry)

  localStorage.setItem(PREFIX + conv.id, JSON.stringify(conv))
  writeIndex(index)
  return evictOldest(index)
}

export function deleteConversation(id) {
  localStorage.removeItem(PREFIX + id)
  const index = readIndex().filter(c => c.id !== id)
  writeIndex(index)
  return index
}

export function newId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2)
}
