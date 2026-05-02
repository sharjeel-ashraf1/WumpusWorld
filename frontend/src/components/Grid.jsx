export default function Grid({ rows, cols, agentState, revealData, gameState }) {
  const cellPx = Math.min(76, Math.floor(440 / Math.max(rows, cols)))

  const getCellStyle = (r, c) => {
    const id = `${r}_${c}`
    const isAgent = agentState.pos[0] === r && agentState.pos[1] === c
    const st = agentState.cell_statuses[id] || 'unknown'

    if (isAgent && gameState === 'running')
      return { background: '#fffbeb', border: '2px solid #d97706', animation: 'glow 2s infinite' }
    if (isAgent && gameState === 'dead')
      return { background: '#fff0f0', border: '2px solid #e53935' }
    if (st === 'visited')
      return { background: '#ddd0bb', border: '1px solid #c8a870' }
    if (st === 'safe')
      return { background: '#c8e6c9', border: '2px solid #4caf50', animation: 'safe-pulse 2.5s infinite' }
    if (st === 'danger')
      return { background: '#ffcdd2', border: '2px solid #e53935' }
    return { background: '#efe3d0', border: '1px dashed #c8a870' }
  }

  const getCellIcon = (r, c) => {
    const id = `${r}_${c}`
    const isAgent = agentState.pos[0] === r && agentState.pos[1] === c
    const st = agentState.cell_statuses[id] || 'unknown'

    if (isAgent && gameState === 'running') return '🧭'
    if (isAgent && gameState === 'dead')    return '💀'

    if (revealData) {
      const cell = revealData.cells[r][c]
      if (cell.pit)    return '🌀'
      if (cell.wumpus) return '🦂'
      if (cell.gold)   return '🔮'
    }

    if (st === 'danger')  return '✕'
    if (st === 'safe' && !agentState.visited.some(v => v[0] === r && v[1] === c)) return '✓'
    if (st === 'visited') return ''
    return ''
  }

  const getIconStyle = (r, c) => {
    const id = `${r}_${c}`
    const st = agentState.cell_statuses[id] || 'unknown'
    if (st === 'danger') return { color: '#c62828', fontSize: '1rem', fontWeight: 'bold' }
    if (st === 'safe')   return { color: '#2e7d32', fontSize: '0.9rem' }
    return { fontSize: '1.4rem' }
  }

  return (
    <div style={{
      background: '#fff8ee', border: '1px solid #c8a870',
      borderRadius: 8, padding: 16,
      boxShadow: '0 2px 12px #c8a87033'
    }}>
      <div style={{
        fontFamily: 'Georgia,serif', fontSize: '0.72rem',
        color: '#b89060', letterSpacing: '0.12em',
        marginBottom: 10, textAlign: 'center', fontStyle: 'italic'
      }}>
        — DUNGEON MAP —
      </div>

      {/* Col headers */}
      <div style={{ display: 'flex', gap: 5, paddingLeft: 22, marginBottom: 4 }}>
        {Array.from({ length: cols }, (_, c) => (
          <div key={c} style={{ width: cellPx, textAlign: 'center', fontSize: '0.6rem', color: '#b89060' }}>{c}</div>
        ))}
      </div>

      {/* Grid rows */}
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} style={{ display: 'flex', gap: 5, marginBottom: 5, alignItems: 'center' }}>
          <div style={{ width: 18, textAlign: 'right', fontSize: '0.6rem', color: '#b89060' }}>{r}</div>
          {Array.from({ length: cols }, (_, c) => (
            <div key={c} className="cell" style={{
              width: cellPx, height: cellPx,
              borderRadius: 5,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              position: 'relative',
              ...getCellStyle(r, c)
            }}>
              <span style={getIconStyle(r, c)}>{getCellIcon(r, c)}</span>
              <span style={{
                position: 'absolute', bottom: 2, right: 3,
                fontSize: '0.45rem', color: '#c8a870', opacity: 0.7
              }}>{r},{c}</span>
            </div>
          ))}
        </div>
      ))}

      {/* Legend */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 10, justifyContent: 'center' }}>
        {[
          { bg: '#fffbeb', bdr: '#d97706', lbl: '🧭 Explorer' },
          { bg: '#ddd0bb', bdr: '#c8a870', lbl: 'Explored' },
          { bg: '#c8e6c9', bdr: '#4caf50', lbl: '✓ Safe' },
          { bg: '#efe3d0', bdr: '#c8a870', lbl: 'Unknown', dash: true },
          { bg: '#ffcdd2', bdr: '#e53935', lbl: '✕ Danger' },
        ].map(({ bg, bdr, lbl, dash }) => (
          <div key={lbl} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 11, height: 11, background: bg, border: `${dash ? '1px dashed' : '1px solid'} ${bdr}`, borderRadius: 2 }} />
            <span style={{ fontSize: '0.62rem', color: '#8b6340', fontStyle: 'italic' }}>{lbl}</span>
          </div>
        ))}
      </div>
    </div>
  )
}