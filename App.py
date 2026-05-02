"""
app.py
------
Flask REST API for the Wumpus World Logic Agent.

Endpoints:
  POST /api/new-game          — start a new game
  POST /api/step              — execute one agent step
  GET  /api/state             — get current game state
  GET  /api/reveal            — reveal true world (for debug/UI toggle)
  POST /api/ask               — manually ASK the KB about a cell
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

from World import WumpusWorld, WumpusAgent

app = Flask(__name__)
CORS(app)   # allow React frontend on different port

# In-memory session store  {session_id: {"world": WumpusWorld, "agent": WumpusAgent}}
sessions: dict = {}


def get_session(session_id: str):
    if session_id not in sessions:
        return None, jsonify({"error": "Session not found. Start a new game."}), 404
    return sessions[session_id], None, None


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/new-game
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/new-game", methods=["POST"])
def new_game():
    """
    Body (JSON):
      rows     : int  (3–10)
      cols     : int  (3–10)
      num_pits : int  (1–floor(rows*cols/3))
      seed     : int? (optional, for reproducibility)
    """
    data     = request.get_json(force=True)
    rows     = max(3, min(10, int(data.get("rows",     4))))
    cols     = max(3, min(10, int(data.get("cols",     4))))
    num_pits = max(1, min(rows * cols // 3, int(data.get("num_pits", 3))))
    seed     = data.get("seed", None)

    session_id = str(uuid.uuid4())
    world  = WumpusWorld(rows, cols, num_pits, seed=seed)
    agent  = WumpusAgent(world)
    sessions[session_id] = {"world": world, "agent": agent, "history": [], "game_over": False}

    return jsonify({
        "session_id":  session_id,
        "rows":        rows,
        "cols":        cols,
        "num_pits":    num_pits,
        "agent_state": agent.get_state(),
        "message":     f"New {rows}×{cols} dungeon created. Agent starts at (0,0).",
    })


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/step
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/step", methods=["POST"])
def step():
    """
    Body (JSON):
      session_id : str
    """
    data       = request.get_json(force=True)
    session_id = data.get("session_id")
    session, err, code = get_session(session_id)
    if err:
        return err, code

    if session["game_over"]:
        return jsonify({"error": "Game is already over. Start a new game."}), 400

    agent: WumpusAgent = session["agent"]

    if not agent.alive or agent.has_gold:
        session["game_over"] = True
        return jsonify({"error": "Game over. Start a new game."}), 400

    result = agent.step()
    session["history"].append(result.outcome)

    terminal = result.outcome in ("gold", "dead_pit", "dead_wumpus", "stuck")
    if terminal:
        session["game_over"] = True

    return jsonify({
        "row":                   result.row,
        "col":                   result.col,
        "percept":               result.percept,
        "tell_log":              result.tell_log,
        "ask_log":               result.ask_log,
        "cell_statuses":         result.cell_statuses,
        "inference_steps":       result.inference_steps,
        "total_inference_steps": result.total_inference_steps,
        "kb_clause_count":       result.kb_clause_count,
        "moved_to":              result.moved_to,
        "outcome":               result.outcome,
        "message":               result.message,
        "game_over":             terminal,
        "agent_state":           agent.get_state(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/state
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/state", methods=["GET"])
def state():
    session_id = request.args.get("session_id")
    session, err, code = get_session(session_id)
    if err:
        return err, code

    agent: WumpusAgent = session["agent"]
    return jsonify({
        "agent_state": agent.get_state(),
        "game_over":   session["game_over"],
        "history":     session["history"],
    })


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/reveal
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/reveal", methods=["GET"])
def reveal():
    """Return the true world layout (for UI reveal toggle)."""
    session_id = request.args.get("session_id")
    session, err, code = get_session(session_id)
    if err:
        return err, code

    world: WumpusWorld = session["world"]
    return jsonify(world.to_dict())


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/ask
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/ask", methods=["POST"])
def ask_cell():
    """
    Manually query the KB about a specific cell.
    Body (JSON):
      session_id : str
      row        : int
      col        : int
    """
    data       = request.get_json(force=True)
    session_id = data.get("session_id")
    session, err, code = get_session(session_id)
    if err:
        return err, code

    r = int(data.get("row", 0))
    c = int(data.get("col", 0))

    agent: WumpusAgent = session["agent"]
    kb = agent.kb

    safe,   s1 = kb.is_safe(r, c)
    danger, s2 = kb.is_dangerous(r, c)

    # Collect traces for the response
    from Logic import Literal
    from Logic import resolution_refutation, make_clause

    pit_result    = kb.ask(Literal(f"P_{r}_{c}"),   record_trace=True)
    wumpus_result = kb.ask(Literal(f"W_{r}_{c}"),   record_trace=True)

    return jsonify({
        "cell":          [r, c],
        "safe_proved":   safe,
        "danger_proved": danger,
        "verdict":       "SAFE" if safe else ("DANGER" if danger else "UNKNOWN"),
        "pit_proof":     {"proved": pit_result.proved,    "steps": pit_result.steps,    "trace": pit_result.trace[:30]},
        "wumpus_proof":  {"proved": wumpus_result.proved, "steps": wumpus_result.steps, "trace": wumpus_result.trace[:30]},
        "kb_clauses":    kb.clause_count,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "sessions": len(sessions)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)