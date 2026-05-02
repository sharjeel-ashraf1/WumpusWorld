import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import Grid from './components/Grid'
import Controls from './components/Controls'
import Percepts from './components/Percepts'
import LogPanel from './components/LogPanel'
import StatsBar from './components/StatsBar'

const API = '/api'

export default function App() {
  const [sessionId, setSessionId]     = useState(null)
  const [gameState, setGameState]     = useState('setup') // setup|running|won|dead|stuck
  const [rows, setRows]               = useState(4)
  const [cols, setCols]               = useState(4)
  const [numPits, setNumPits]         = useState(3)
  const [agentState, setAgentState]   = useState(null)
  const [lastStep, setLastStep]       = useState(null)
  const [revealData, setRevealData]   = useState(null)
  const [reveal, setReveal]           = useState(false)
  const [log, setLog]                 = useState([])
  const [totalSteps, setTotalSteps]   = useState(0)
  const [kbClauses, setKbClauses]     = useState(0)
  const [auto, setAuto]               = useState(false)
  const autoRef = useRef(false)

  const addLog = (entries) => setLog(prev => [...prev, ...entries])

  const newGame = async () => {
    try {
      const res = await axios.post(`${API}/new-game`, { rows, cols, num_pits: numPits })
      setSessionId(res.data.session_id)
      setAgentState(res.data.agent_state)
      setGameState('running')
      setLastStep(null)
      setRevealData(null)
      setReveal(false)
      setTotalSteps(0)
      setKbClauses(0)
      setLog([{ t: 'sys', m: res.data.message }])
      autoRef.current = false
      setAuto(false)
    } catch (e) {
      alert('Could not connect to backend. Is python App.py running?')
    }
  }

  const step = async () => {
    if (!sessionId || gameState !== 'running') return
    try {
      const res = await axios.post(`${API}/step`, { session_id: sessionId })
      const d = res.data
      setAgentState(d.agent_state)
      setLastStep(d)
      setTotalSteps(d.total_inference_steps)
      setKbClauses(d.kb_clause_count)
      addLog([
        { t: 'step', m: `── (${d.row},${d.col}) · Draught:${d.percept.breeze} Fetor:${d.percept.stench} Glint:${d.percept.glitter}` },
        ...d.tell_log.map(m => ({ t: 'tell', m })),
        ...d.ask_log.map(m => ({ t: 'ask', m })),
        { t: 'move', m: d.message },
      ])
      if (d.game_over) {
        setGameState(d.outcome === 'gold' ? 'won' : d.outcome === 'stuck' ? 'stuck' : 'dead')
        autoRef.current = false
        setAuto(false)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const toggleAuto = () => {
    autoRef.current = !auto
    setAuto(!auto)
  }

  useEffect(() => {
    if (!auto) return
    const iv = setInterval(() => {
      if (!autoRef.current) { clearInterval(iv); return }
      step()
    }, 800)
    return () => clearInterval(iv)
  }, [auto, sessionId])

  const toggleReveal = async () => {
    if (!reveal && !revealData) {
      const res = await axios.get(`${API}/reveal?session_id=${sessionId}`)
      setRevealData(res.data)
    }
    setReveal(v => !v)
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5ede0', color: '#3b2a14', fontFamily: 'Georgia, serif' }}>

      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg,#3b1f08 0%,#5c3010 100%)',
        borderBottom: '2px solid #8b6340',
        padding: '14px 28px',
        display: 'flex', alignItems: 'center', gap: '16px',
      }}>
        <span style={{ fontSize: '2rem' }}>🗺️</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: 'Georgia,serif', fontSize: '1.4rem', color: '#f5ede0', fontWeight: 'bold', letterSpacing: '0.06em' }}>
            The Dungeon Scholar
          </div>
          <div style={{ fontSize: '0.72rem', color: '#c8a870', fontStyle: 'italic', marginTop: '2px' }}>
            Knowledge-Based Agent · Propositional Logic · Resolution Refutation
          </div>
        </div>
        <StatsBar totalSteps={totalSteps} kbClauses={kbClauses} gameState={gameState} />
      </div>

      {/* Body */}
      <div style={{ display: 'flex', minHeight: 'calc(100vh - 66px)' }}>

        {/* Main */}
        <div style={{ flex: 1, padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

          <Controls
            rows={rows} setRows={setRows}
            cols={cols} setCols={setCols}
            numPits={numPits} setNumPits={setNumPits}
            onNew={newGame}
            onStep={step}
            onAuto={toggleAuto}
            onReveal={toggleReveal}
            auto={auto}
            reveal={reveal}
            gameState={gameState}
          />

          {agentState && (
            <div style={{ display: 'flex', gap: '18px', flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <Grid
                rows={rows} cols={cols}
                agentState={agentState}
                revealData={reveal ? revealData : null}
                gameState={gameState}
              />
              <Percepts agentState={agentState} lastStep={lastStep} />
            </div>
          )}

          {/* End state */}
          {(gameState === 'won' || gameState === 'dead' || gameState === 'stuck') && (
            <div style={{
              background: gameState === 'won' ? '#f0fdf4' : '#fff0f0',
              border: `2px solid ${gameState === 'won' ? '#4caf50' : '#e53935'}`,
              borderRadius: 8, padding: '22px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>
                {gameState === 'won' ? '🔮' : '💀'}
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: gameState === 'won' ? '#2e7d32' : '#c62828' }}>
                {gameState === 'won' ? 'The Relic is secured — Expedition triumphant!' : gameState === 'stuck' ? 'The Scholar is trapped — no safe moves remain.' : 'The Scholar has fallen to the dungeon.'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#8b6340', marginTop: 8, fontStyle: 'italic' }}>
                Total resolution steps: {totalSteps.toLocaleString()}
              </div>
              <button onClick={newGame} style={btnStyle('#3b1f08', '#f5ede0', '#8b6340', '8px 28px')}>
                New Expedition
              </button>
            </div>
          )}

          {gameState === 'setup' && (
            <div style={{
              background: '#fff8ee', border: '1px dashed #c8a870',
              borderRadius: 8, padding: '52px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '3rem', marginBottom: 14 }}>🗺️</div>
              <div style={{ color: '#8b6340', fontSize: '1rem' }}>
                Configure your dungeon, then click <strong>Begin Expedition</strong>.
              </div>
              <div style={{ color: '#b89060', fontSize: '0.8rem', marginTop: 10, fontStyle: 'italic' }}>
                The Scholar proves every chamber safe before entering it.
              </div>
            </div>
          )}
        </div>

        {/* Log sidebar */}
        <LogPanel log={log} />
      </div>
    </div>
  )
}

export function btnStyle(bg, color, border, padding = '6px 14px') {
  return {
    marginTop: 14,
    background: bg, color, border: `1px solid ${border}`,
    borderRadius: 4, cursor: 'pointer',
    fontFamily: 'Georgia, serif', fontSize: '0.75rem',
    padding, letterSpacing: '0.04em',
  }
}