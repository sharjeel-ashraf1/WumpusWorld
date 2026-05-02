# The Dungeon Scholar — Wumpus World Logic Agent

A Knowledge-Based Agent that navigates a Wumpus World-style grid using
Propositional Logic and Resolution Refutation to deduce safe cells before moving.

## Demo
> Live URL: (add after deployment)

---

## Project Structure
Wumpus/
├── Logic.py          # Propositional logic engine (CNF, Resolution Refutation, KB)
├── World.py          # Wumpus World environment + Knowledge-Based Agent
├── App.py            # Flask REST API (5 endpoints)
├── requirements.txt  # Python dependencies
└── frontend/         # React + Vite web interface
└── src/
├── App.jsx
└── components/
├── Controls.jsx
├── Grid.jsx
├── Percepts.jsx
├── LogPanel.jsx
└── StatsBar.jsx

---

## How It Works

### 1. Knowledge Base (Logic.py)
- Propositional variables: `P_r_c` (Pit), `W_r_c` (Wumpus), `B_r_c` (Breeze), `S_r_c` (Stench)
- Clauses stored in CNF (Conjunctive Normal Form)
- `KnowledgeBase.tell()` — adds new clauses to the KB
- `KnowledgeBase.ask()` — queries via Resolution Refutation

### 2. Resolution Refutation (Logic.py)
To prove a query `α`:
1. Add `¬α` to the KB
2. Repeatedly resolve clause pairs
3. If the empty clause `□` is derived → contradiction found → `α` is proved

### 3. Agent Decision Cycle (World.py)
On every step the agent:
1. **Perceives** — Breeze, Stench, Glitter at current cell
2. **TELL** — Updates KB with biconditionals:
   - `B(r,c) ⟺ P(r-1,c) ∨ P(r+1,c) ∨ P(r,c-1) ∨ P(r,c+1)`
   - `S(r,c) ⟺ W(r-1,c) ∨ W(r+1,c) ∨ W(r,c-1) ∨ W(r,c+1)`
3. **ASK** — Runs Resolution Refutation on each adjacent cell to classify it as Safe, Danger, or Unknown
4. **Move** — Prefers unvisited safe cells, then unknown cells, avoids confirmed danger

### 4. Flask API (App.py)
| Endpoint | Method | Description |
|---|---|---|
| `/api/new-game` | POST | Start a new game session |
| `/api/step` | POST | Execute one agent step |
| `/api/state` | GET | Get current game state |
| `/api/reveal` | GET | Reveal true world layout |
| `/api/ask` | POST | Manually query KB about a cell |

---

## Running Locally

### Backend
```bash
pip install -r requirements.txt
python App.py
```
Flask runs on `http://127.0.0.1:5000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
React runs on `http://localhost:5173`

---

## Tech Stack
- **Backend:** Python 3, Flask, Flask-CORS
- **Frontend:** React, Vite, Axios
- **Logic Engine:** Custom Propositional Logic + Resolution Refutation (no external AI libraries)

---

## Key Concepts Implemented
- Propositional Logic Knowledge Base
- CNF (Conjunctive Normal Form) conversion
- Biconditional elimination
- Resolution Refutation proof by contradiction
- Dynamic percept-based KB updates
