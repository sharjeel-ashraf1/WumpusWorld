import { useEffect, useRef } from 'react'

export default function LogPanel({ log }) {
  const logRef = useRef(null)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  const getColor = (t) => ({
    tell: '#1565c0',
    ask:  '#2e7d32',
    warn: '#b45309',
    move: '#5c4030',
    step: '#b89060',
    dead: '#c62828',
    win:  '#b45309',
    sys:  '#8b6340',
    info: '#8b6340',
  }[t] || '#8b6340')

  return (
    <div style={{
      width: 320, borderLeft: '1px solid #c8a870',
      background: '#fdf6ec', display: 'flex', flexDirection: 'column'
    }}>
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #c8a870',
        fontSize: '0.75rem', color: '#b45309',
        fontStyle: 'italic', letterSpacing: '0.08em'
      }}>
        📜 Reasoning Journal
      </div>

      <div ref={logRef} style={{
        flex: 1, overflowY: 'auto', padding: '10px 12px',
        display: 'flex', flexDirection: 'column', gap: 2
      }}>
        {!log.length && (
          <div style={{ color: '#b89060', fontSize: '0.75rem', fontStyle: 'italic', padding: 8 }}>
            The journal awaits the first entry…
          </div>
        )}
        {log.map((entry, i) => (
          <div key={i} className="log-entry" style={{
            fontSize: '0.71rem', lineHeight: 1.55,
            padding: entry.t === 'step' ? '6px 5px 2px' : '2px 5px',
            borderTop: entry.t === 'step' ? '1px solid #c8a870' : 'none',
            marginTop: entry.t === 'step' ? 4 : 0,
            color: getColor(entry.t),
            borderRadius: 2,
          }}>
            {entry.m}
          </div>
        ))}
      </div>
    </div>
  )
}