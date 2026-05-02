"""
world.py
--------
Wumpus World environment and the Knowledge-Based Agent.

Environment:
  - Dynamic grid (rows × cols)
  - Random Pits and a Wumpus (unknown to agent initially)
  - Percept generation: Breeze / Stench / Glitter

Agent:
  - Maintains a Propositional Logic KB (via logic.py)
  - On each step: perceives → TELLs KB → ASKs KB → moves
  - Uses Resolution Refutation to classify adjacent cells
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from Logic import KnowledgeBase, Literal, make_clause, biconditional_to_cnf


# ─────────────────────────────────────────────────────────────────────────────
# Cell classification (from agent's perspective)
# ─────────────────────────────────────────────────────────────────────────────

class CellStatus(str, Enum):
    UNKNOWN  = "unknown"
    SAFE     = "safe"
    VISITED  = "visited"
    DANGER   = "danger"   # confirmed pit or wumpus


# ─────────────────────────────────────────────────────────────────────────────
# Variable naming conventions
# ─────────────────────────────────────────────────────────────────────────────

def pit_var(r: int, c: int)     -> str: return f"P_{r}_{c}"
def wumpus_var(r: int, c: int)  -> str: return f"W_{r}_{c}"
def breeze_var(r: int, c: int)  -> str: return f"B_{r}_{c}"
def stench_var(r: int, c: int)  -> str: return f"S_{r}_{c}"


# ─────────────────────────────────────────────────────────────────────────────
# World (environment)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Cell:
    has_pit:    bool = False
    has_wumpus: bool = False
    has_gold:   bool = False


@dataclass
class Percept:
    breeze:  bool = False
    stench:  bool = False
    glitter: bool = False
    bump:    bool = False


class WumpusWorld:
    """
    The hidden environment.  The agent cannot see this directly.
    """

    def __init__(self, rows: int, cols: int, num_pits: int, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self._place_hazards(num_pits)

    # ── Setup ─────────────────────────────────────────────────────────────

    def _place_hazards(self, num_pits: int) -> None:
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if not (r == 0 and c == 0)]
        random.shuffle(all_cells)

        # Pits
        placed = 0
        for r, c in all_cells:
            if placed >= num_pits:
                break
            self.grid[r][c].has_pit = True
            placed += 1

        # Wumpus (not on a pit cell)
        safe_cells = [(r, c) for r, c in all_cells if not self.grid[r][c].has_pit]
        wr, wc = random.choice(safe_cells)
        self.grid[wr][wc].has_wumpus = True

        # Gold (not on hazard)
        no_hazard = [(r, c) for r, c in all_cells
                     if not self.grid[r][c].has_pit and not self.grid[r][c].has_wumpus]
        gr, gc = random.choice(no_hazard)
        self.grid[gr][gc].has_gold = True

    # ── Queries ───────────────────────────────────────────────────────────

    def adjacent(self, r: int, c: int) -> List[Tuple[int, int]]:
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def get_percept(self, r: int, c: int, wumpus_alive: bool) -> Percept:
        p = Percept()
        for nr, nc in self.adjacent(r, c):
            if self.grid[nr][nc].has_pit:
                p.breeze = True
            if self.grid[nr][nc].has_wumpus and wumpus_alive:
                p.stench = True
        if self.grid[r][c].has_gold:
            p.glitter = True
        return p

    def is_pit(self, r: int, c: int)    -> bool: return self.grid[r][c].has_pit
    def is_wumpus(self, r: int, c: int) -> bool: return self.grid[r][c].has_wumpus

    def to_dict(self) -> dict:
        """Serialise the true world state (for reveal / debug)."""
        cells = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                cell = self.grid[r][c]
                row.append({
                    "pit":    cell.has_pit,
                    "wumpus": cell.has_wumpus,
                    "gold":   cell.has_gold,
                })
            cells.append(row)
        return {"rows": self.rows, "cols": self.cols, "cells": cells}


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    """Result of one agent step — returned to the API / frontend."""
    row: int
    col: int
    percept: dict
    tell_log: List[str]
    ask_log:  List[str]
    cell_statuses: Dict[str, str]
    inference_steps: int
    total_inference_steps: int
    kb_clause_count: int
    moved_to: Optional[Tuple[int, int]]
    outcome: str   # "ok" | "dead_pit" | "dead_wumpus" | "gold" | "stuck"
    message: str


class WumpusAgent:
    """
    Knowledge-Based Agent for the Wumpus World.

    Decision cycle (per step):
      1. Perceive current cell
      2. TELL KB: update with percept-based biconditionals
      3. ASK KB: classify each adjacent cell via resolution refutation
      4. Choose safest available move
      5. Move and check outcome
    """

    def __init__(self, world: WumpusWorld):
        self.world  = world
        self.kb     = KnowledgeBase()
        self.pos    = (0, 0)
        self.alive  = True
        self.has_gold        = False
        self.wumpus_alive    = True
        self.visited:  Set[Tuple[int, int]] = {(0, 0)}
        self.safe:     Set[Tuple[int, int]] = {(0, 0)}
        self.danger:   Set[Tuple[int, int]] = set()
        self.cell_statuses: Dict[str, str]  = {}
        self._init_cell_statuses()
        # Tell KB that start cell is safe
        r, c = 0, 0
        self.kb.tell_unit(-Literal(pit_var(r, c)),    "Start (0,0) has no pit")
        self.kb.tell_unit(-Literal(wumpus_var(r, c)), "Start (0,0) has no wumpus")

    def _init_cell_statuses(self) -> None:
        for r in range(self.world.rows):
            for c in range(self.world.cols):
                self.cell_statuses[f"{r}_{c}"] = CellStatus.UNKNOWN

    def _set_status(self, r: int, c: int, status: CellStatus) -> None:
        self.cell_statuses[f"{r}_{c}"] = status

    # ── TELL ──────────────────────────────────────────────────────────────

    def _tell_percepts(self, r: int, c: int, percept: Percept) -> List[str]:
        """
        Update KB with biconditionals derived from current percept.
        Returns log lines for the frontend.
        """
        log: List[str] = []
        neighbors = self.world.adjacent(r, c)
        pit_lits    = [Literal(pit_var(nr, nc))    for nr, nc in neighbors]
        wumpus_lits = [Literal(wumpus_var(nr, nc)) for nr, nc in neighbors]

        # ── Breeze ↔ Pit in adjacent cell ──────────────────────────────
        b_lit = Literal(breeze_var(r, c))
        if percept.breeze:
            self.kb.tell_unit(b_lit, f"B({r},{c}) = TRUE")
            self.kb.tell_biconditional(
                b_lit, pit_lits,
                f"B({r},{c}) ⟺ {' ∨ '.join(str(l) for l in pit_lits)}"
            )
            log.append(f"TELL: B({r},{c})=T  →  Pit in one of {[(nr,nc) for nr,nc in neighbors]}")
        else:
            self.kb.tell_unit(-b_lit, f"¬B({r},{c}) = TRUE")
            for pl in pit_lits:
                self.kb.tell_unit(-pl, f"¬{pl} (no breeze)")
            log.append(f"TELL: ¬B({r},{c})  →  No pits adjacent to ({r},{c})")

        # ── Stench ↔ Wumpus in adjacent cell ───────────────────────────
        s_lit = Literal(stench_var(r, c))
        if percept.stench:
            self.kb.tell_unit(s_lit, f"S({r},{c}) = TRUE")
            self.kb.tell_biconditional(
                s_lit, wumpus_lits,
                f"S({r},{c}) ⟺ {' ∨ '.join(str(l) for l in wumpus_lits)}"
            )
            log.append(f"TELL: S({r},{c})=T  →  Wumpus in one of {[(nr,nc) for nr,nc in neighbors]}")
        else:
            self.kb.tell_unit(-s_lit, f"¬S({r},{c}) = TRUE")
            for wl in wumpus_lits:
                self.kb.tell_unit(-wl, f"¬{wl} (no stench)")
            log.append(f"TELL: ¬S({r},{c})  →  No wumpus adjacent to ({r},{c})")

        # ── Current cell is safe ────────────────────────────────────────
        self.kb.tell_unit(-Literal(pit_var(r, c)),    f"¬P({r},{c}) visited safely")
        self.kb.tell_unit(-Literal(wumpus_var(r, c)), f"¬W({r},{c}) visited safely")

        return log

    # ── ASK ───────────────────────────────────────────────────────────────

    def _ask_adjacent(self, r: int, c: int) -> Tuple[List[str], int]:
        """
        For each unclassified adjacent cell, ask the KB:
          - Is it SAFE?   (prove ¬Pit ∧ ¬Wumpus)
          - Is it DANGER? (prove Pit ∨ Wumpus)
        Returns log lines and total inference steps used.
        """
        log: List[str] = []
        steps = 0

        for nr, nc in self.world.adjacent(r, c):
            pos = (nr, nc)
            if pos in self.safe or pos in self.danger:
                continue

            safe, s1 = self.kb.is_safe(nr, nc)
            steps += s1

            if safe:
                self.safe.add(pos)
                self._set_status(nr, nc, CellStatus.SAFE)
                log.append(f"ASK: ({nr},{nc}) → SAFE ✓  (proved ¬Pit∧¬Wumpus in {s1} steps)")
                continue

            danger, s2 = self.kb.is_dangerous(nr, nc)
            steps += s2

            if danger:
                self.danger.add(pos)
                self._set_status(nr, nc, CellStatus.DANGER)
                log.append(f"ASK: ({nr},{nc}) → DANGER ✕  [{s2} resolution steps]")
            else:
                log.append(f"ASK: ({nr},{nc}) → UNKNOWN  [{s1+s2} steps, insufficient info]")

        return log, steps

    # ── Move selection ────────────────────────────────────────────────────

    def _choose_next(self, r: int, c: int) -> Optional[Tuple[int, int]]:
        """
        Priority:
          1. Unvisited safe cell
          2. Unknown cell (risky — explore rather than loop)
          3. Visited safe cell (backtrack only if no other option)
        """
        neighbors = self.world.adjacent(r, c)

        # Priority 1: unvisited + safe
        for pos in neighbors:
            if pos in self.safe and pos not in self.visited:
                return pos

        # Priority 2: unknown (risky but avoids looping forever)
        for pos in neighbors:
            if pos not in self.danger and pos not in self.visited:
                return pos

        # Priority 3: visited safe cell (last resort backtrack)
        # Pick the one that has the most unvisited safe neighbors
        best, best_score = None, -1
        for pos in neighbors:
            if pos in self.safe or pos in self.visited:
                nr, nc = pos
                score = sum(
                    1 for np in self.world.adjacent(nr, nc)
                    if np not in self.visited and np not in self.danger
                )
                if score > best_score:
                    best_score = score
                    best = pos
        return best

    # ── Main step ─────────────────────────────────────────────────────────

    def step(self) -> AgentStep:
        """Execute one agent step and return the full state snapshot."""
        r, c = self.pos

        # 1. Perceive
        percept = self.world.get_percept(r, c, self.wumpus_alive)

        # 2. TELL
        tell_log = self._tell_percepts(r, c, percept)
        steps_before = self.kb.total_steps

        # 2b. Glitter → grab gold
        if percept.glitter:
            self.has_gold = True
            self._set_status(r, c, CellStatus.VISITED)
            return AgentStep(
                row=r, col=c,
                percept=percept.__dict__,
                tell_log=tell_log, ask_log=[],
                cell_statuses=dict(self.cell_statuses),
                inference_steps=0,
                total_inference_steps=self.kb.total_steps,
                kb_clause_count=self.kb.clause_count,
                moved_to=None,
                outcome="gold",
                message=f"★ Gold grabbed at ({r},{c})! Agent wins.",
            )

        # 3. ASK
        ask_log, ask_steps = self._ask_adjacent(r, c)
        self._set_status(r, c, CellStatus.VISITED)

        # 4. Choose move
        next_pos = self._choose_next(r, c)
        if next_pos is None:
            return AgentStep(
                row=r, col=c,
                percept=percept.__dict__,
                tell_log=tell_log, ask_log=ask_log,
                cell_statuses=dict(self.cell_statuses),
                inference_steps=ask_steps,
                total_inference_steps=self.kb.total_steps,
                kb_clause_count=self.kb.clause_count,
                moved_to=None,
                outcome="stuck",
                message="Agent is trapped — no safe moves available.",
            )

        nr, nc = next_pos
        risky = next_pos not in self.safe
        if risky:
            ask_log.append(f"⚠ No proven safe path. Venturing blind into ({nr},{nc}).")

        # 5. Move
        self.pos = next_pos
        self.visited.add(next_pos)

        # 6. Check outcome
        if self.world.is_pit(nr, nc):
            self.alive = False
            self._set_status(nr, nc, CellStatus.DANGER)
            return AgentStep(
                row=nr, col=nc,
                percept=percept.__dict__,
                tell_log=tell_log, ask_log=ask_log,
                cell_statuses=dict(self.cell_statuses),
                inference_steps=ask_steps,
                total_inference_steps=self.kb.total_steps,
                kb_clause_count=self.kb.clause_count,
                moved_to=(nr, nc),
                outcome="dead_pit",
                message=f"✝ Agent fell into a pit at ({nr},{nc}).",
            )

        if self.world.is_wumpus(nr, nc) and self.wumpus_alive:
            self.alive = False
            self._set_status(nr, nc, CellStatus.DANGER)
            return AgentStep(
                row=nr, col=nc,
                percept=percept.__dict__,
                tell_log=tell_log, ask_log=ask_log,
                cell_statuses=dict(self.cell_statuses),
                inference_steps=ask_steps,
                total_inference_steps=self.kb.total_steps,
                kb_clause_count=self.kb.clause_count,
                moved_to=(nr, nc),
                outcome="dead_wumpus",
                message=f"✝ Agent consumed by the Wumpus at ({nr},{nc}).",
            )

        # Update statuses for safe confirmed cells
        for pos in self.safe:
            pr, pc = pos
            if pos in self.visited:
                self._set_status(pr, pc, CellStatus.VISITED)
            else:
                self._set_status(pr, pc, CellStatus.SAFE)
        for pos in self.danger:
            pr, pc = pos
            self._set_status(pr, pc, CellStatus.DANGER)
        self._set_status(nr, nc, CellStatus.VISITED)

        return AgentStep(
            row=nr, col=nc,
            percept=percept.__dict__,
            tell_log=tell_log, ask_log=ask_log,
            cell_statuses=dict(self.cell_statuses),
            inference_steps=ask_steps,
            total_inference_steps=self.kb.total_steps,
            kb_clause_count=self.kb.clause_count,
            moved_to=(nr, nc),
            outcome="ok",
            message=f"Moved to ({nr},{nc})" + (" [RISKY]" if risky else " [safe]"),
        )

    def get_state(self) -> dict:
        """Serialise full agent state for the frontend."""
        return {
            "pos":                    list(self.pos),
            "alive":                  self.alive,
            "has_gold":               self.has_gold,
            "wumpus_alive":           self.wumpus_alive,
            "visited":                [list(p) for p in self.visited],
            "safe":                   [list(p) for p in self.safe],
            "danger":                 [list(p) for p in self.danger],
            "cell_statuses":          self.cell_statuses,
            "kb_clause_count":        self.kb.clause_count,
            "total_inference_steps":  self.kb.total_steps,
        }