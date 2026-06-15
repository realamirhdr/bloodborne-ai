import styles from './Sidebar.module.css'

export default function Sidebar({ conversations, activeId, onSelect, onNew, onDelete }) {
  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt)

  return (
    <aside className={styles.sidebar}>
      <div className={styles.top}>
        <span className={styles.brand}>BLOODBORNE</span>
        <button className={styles.newBtn} onClick={onNew} title="New conversation">
          + New Hunt
        </button>
      </div>

      <div className={styles.list}>
        {sorted.length === 0 && (
          <p className={styles.empty}>No hunts yet.<br />Start a new conversation.</p>
        )}
        {sorted.map(conv => (
          <div
            key={conv.id}
            className={`${styles.item} ${conv.id === activeId ? styles.active : ''}`}
            onClick={() => onSelect(conv.id)}
          >
            <span className={styles.convTitle}>{conv.title}</span>
            <span className={styles.convDate}>{formatDate(conv.updatedAt)}</span>
            <button
              className={styles.deleteBtn}
              onClick={e => { e.stopPropagation(); onDelete(conv.id) }}
              title="Delete"
            >✕</button>
          </div>
        ))}
      </div>
    </aside>
  )
}

function formatDate(ts) {
  const d = new Date(ts)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
