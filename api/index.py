from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from World import WumpusWorld, WumpusAgent
import uuid

app = Flask(__name__)
CORS(app)

sessions = {}

def get_session(session_id):
    if session_id not in sessions:
        return None
    return sessions[session_id]

@app.route("/api/new-game", methods=["POST"])
def new_game():
    data     = request.get_json(force=True)
    rows     = max(3, min(10, int(data.get("rows", 4))))
    cols     = max(3, min(10, int(data.get("cols", 4))))
    num_pits = max(1, min(rows * cols // 3, int(data.get("num_pits", 3))))
    seed     = data.get("seed", None)

    session_id = str(uuid.uuid4())
    world  = WumpusWorld(rows, cols, num_pits, seed=seed)
    agent  = WumpusAgent(world)
    sessions[session_id] = {
        "world": world,
        "agent": agent,
        "history": [],
        "game_over": False
    }

    return jsonify({
        "session_id":  session_id,
        "rows":        rows,
        "cols":        cols,
        "num_pits":    num_pits,
        "agent_state": agent.get_state(),
        "message":     f"New {rows}×{cols} dungeon created. Agent starts at (0,0).",
    })

@app.route("/api/step", methods=["POST"])
def step():
    data       = request.get_json(force=True)
    session_id = data.get("session_id")
    session    = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if session["game_over"]:
        return jsonify({"error": "Game is already over."}), 400

    agent = session["agent"]
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

@app.route("/api/state", methods=["GET"])
def state():
    session_id = request.args.get("session_id")
    session    = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    agent = session["agent"]
    return jsonify({
        "agent_state": agent.get_state(),
        "game_over":   session["game_over"],
        "history":     session["history"],
    })

@app.route("/api/reveal", methods=["GET"])
def reveal():
    session_id = request.args.get("session_id")
    session    = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    return jsonify(session["world"].to_dict())

@app.route("/api/ask", methods=["POST"])
def ask_cell():
    data       = request.get_json(force=True)
    session_id = data.get("session_id")
    session    = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404

    r  = int(data.get("row", 0))
    c  = int(data.get("col", 0))
    kb = session["agent"].kb

    safe,   s1 = kb.is_safe(r, c)
    danger, s2 = kb.is_dangerous(r, c)

    return jsonify({
        "cell":          [r, c],
        "verdict":       "SAFE" if safe else ("DANGER" if danger else "UNKNOWN"),
        "kb_clauses":    kb.clause_count,
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "sessions": len(sessions)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)