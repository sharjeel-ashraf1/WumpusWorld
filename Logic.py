"""
logic.py
--------
Propositional Logic engine for the Wumpus World agent.

Provides:
  - Literal / Clause representation
  - CNF conversion (biconditional → CNF)
  - Resolution Refutation  (prove α by deriving contradiction from KB ∪ {¬α})
  - KnowledgeBase  (TELL / ASK interface)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Set, Tuple
import itertools


# ─────────────────────────────────────────────────────────────────────────────
# Core data types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Literal:
    """A propositional literal: either P or ¬P."""
    name: str
    negated: bool = False

    def __neg__(self) -> "Literal":
        return Literal(self.name, not self.negated)

    def __str__(self) -> str:
        return f"¬{self.name}" if self.negated else self.name

    def __repr__(self) -> str:
        return str(self)


# A clause is a frozenset of literals (disjunction).
Clause = FrozenSet[Literal]


def make_clause(*literals: Literal) -> Clause:
    return frozenset(literals)


def clause_str(clause: Clause) -> str:
    if not clause:
        return "□"  # empty clause = contradiction
    return " ∨ ".join(str(l) for l in sorted(clause, key=str))


# ─────────────────────────────────────────────────────────────────────────────
# CNF helpers
# ─────────────────────────────────────────────────────────────────────────────

def biconditional_to_cnf(head: Literal, body: List[Literal]) -> List[Clause]:
    """
    Convert  head ⟺ (b1 ∨ b2 ∨ … ∨ bn)  to CNF.

    Equivalences used:
      (A ⟺ B)  →  (A → B) ∧ (B → A)
               →  (¬A ∨ B) ∧ (¬B ∨ A)

    For  head ⟺ (b1 ∨ b2 ∨ … ∨ bn):
      Forward  : ¬head ∨ b1 ∨ b2 ∨ … ∨ bn
      Backward : ¬b_i ∨ head   for each i
    """
    clauses: List[Clause] = []
    # Forward clause
    clauses.append(make_clause(-head, *body))
    # Backward clauses (one per body literal)
    for b in body:
        clauses.append(make_clause(-b, head))
    return clauses


def conjunction_to_cnf(literals: List[Literal]) -> List[Clause]:
    """Convert a conjunction of unit literals to unit clauses."""
    return [make_clause(lit) for lit in literals]


# ─────────────────────────────────────────────────────────────────────────────
# Resolution Refutation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResolutionResult:
    proved: bool
    steps: int
    new_clauses_generated: int
    trace: List[str] = field(default_factory=list)


def resolve_clauses(c1: Clause, c2: Clause) -> List[Clause]:
    """
    Apply the resolution rule to two clauses.
    Returns all possible resolvents (usually 0 or 1).

    Resolution rule:
      If  c1 = {P, …}  and  c2 = {¬P, …}
      then  resolvent = (c1 − {P}) ∪ (c2 − {¬P})
    """
    resolvents: List[Clause] = []
    for lit in c1:
        neg = -lit
        if neg in c2:
            # Found a complementary pair — resolve on it
            new_clause = (c1 - {lit}) | (c2 - {neg})
            # Check for tautology (contains both P and ¬P)
            is_tautology = any((-l) in new_clause for l in new_clause)
            if not is_tautology:
                resolvents.append(frozenset(new_clause))
    return resolvents


def resolution_refutation(
    kb_clauses: List[Clause],
    query: Literal,
    max_iterations: int = 3000,
    record_trace: bool = False,
) -> ResolutionResult:
    """
    Prove  query  by refutation:
      Add ¬query to KB, then derive the empty clause (contradiction).

    Algorithm (basic resolution):
      1. clauses = KB ∪ {¬query}
      2. Repeat:
           new = {}
           For each pair (Ci, Cj) in clauses:
               resolvents = resolve(Ci, Cj)
               if □ in resolvents → return PROVED
               new = new ∪ resolvents − clauses
           if new ⊆ clauses → return NOT PROVED (saturated)
           clauses = clauses ∪ new

    Returns ResolutionResult with proved flag, step count, and optional trace.
    """
    # Start with KB + negation of query
    clauses: List[Clause] = list(kb_clauses) + [make_clause(-query)]
    seen: Set[Clause] = set(clauses)
    steps = 0
    new_clauses_count = 0
    trace: List[str] = []

    if record_trace:
        trace.append(f"Attempting to prove: {query}")
        trace.append(f"Added to KB: {clause_str(make_clause(-query))}")
        trace.append(f"Starting with {len(clauses)} clauses")

    for iteration in range(max_iterations):
        new: List[Clause] = []

        for i, ci in enumerate(clauses):
            for j, cj in enumerate(clauses):
                if j <= i:
                    continue  # avoid duplicate pairs
                resolvents = resolve_clauses(ci, cj)
                steps += 1

                for resolvent in resolvents:
                    if not resolvent:
                        # Empty clause derived → contradiction → query proved
                        if record_trace:
                            trace.append(
                                f"Step {steps}: Resolved {clause_str(ci)} "
                                f"with {clause_str(cj)} → □ (contradiction!)"
                            )
                        return ResolutionResult(
                            proved=True,
                            steps=steps,
                            new_clauses_generated=new_clauses_count,
                            trace=trace,
                        )

                    if resolvent not in seen:
                        seen.add(resolvent)
                        new.append(resolvent)
                        new_clauses_count += 1
                        if record_trace and len(trace) < 200:
                            trace.append(
                                f"Step {steps}: {clause_str(ci)} + {clause_str(cj)} "
                                f"→ {clause_str(resolvent)}"
                            )

        if not new:
            # KB is saturated — query cannot be proved
            if record_trace:
                trace.append("Saturated. No contradiction found — query not provable.")
            return ResolutionResult(
                proved=False,
                steps=steps,
                new_clauses_generated=new_clauses_count,
                trace=trace,
            )

        clauses.extend(new)

    # Max iterations hit
    return ResolutionResult(
        proved=False,
        steps=steps,
        new_clauses_generated=new_clauses_count,
        trace=trace,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeBase:
    """
    Propositional Logic Knowledge Base.

    Stores clauses in CNF. Supports:
      TELL(clauses)  — add new information
      ASK(query)     — query via resolution refutation
    """

    def __init__(self) -> None:
        self._clauses: List[Clause] = []
        self._total_steps: int = 0
        self._tell_log: List[str] = []

    # ── TELL ──────────────────────────────────────────────────────────────

    def tell(self, clauses: List[Clause], description: str = "") -> None:
        """Add a list of CNF clauses to the KB."""
        for clause in clauses:
            if clause not in self._clauses:
                self._clauses.append(clause)
        if description:
            self._tell_log.append(description)

    def tell_unit(self, literal: Literal, description: str = "") -> None:
        """Shortcut: add a single unit clause."""
        self.tell([make_clause(literal)], description)

    def tell_biconditional(
        self, head: Literal, body: List[Literal], description: str = ""
    ) -> None:
        """
        TELL:  head ⟺ (body[0] ∨ body[1] ∨ … ∨ body[n])
        Converts to CNF and adds to KB.
        """
        cnf = biconditional_to_cnf(head, body)
        self.tell(cnf, description or f"Bic: {head} ⟺ {' ∨ '.join(str(b) for b in body)}")

    # ── ASK ───────────────────────────────────────────────────────────────

    def ask(
        self,
        query: Literal,
        record_trace: bool = False,
    ) -> ResolutionResult:
        """
        ASK: Is  query  entailed by the KB?
        Uses Resolution Refutation.
        """
        result = resolution_refutation(
            self._clauses, query, record_trace=record_trace
        )
        self._total_steps += result.steps
        return result

    def is_safe(self, r: int, c: int) -> Tuple[bool, int]:
        """
        Prove ¬Pit(r,c) ∧ ¬Wumpus(r,c) via refutation.
        To prove ¬P: negate ¬P → add P → derive contradiction.
        So we ask(-Literal) which adds +Literal to KB.
        """
        no_pit    = self.ask(-Literal(f"P_{r}_{c}"))
        no_wumpus = self.ask(-Literal(f"W_{r}_{c}"))
        steps = no_pit.steps + no_wumpus.steps
        return (no_pit.proved and no_wumpus.proved), steps

    def is_dangerous(self, r: int, c: int) -> Tuple[bool, int]:
        """
        Prove Pit(r,c) ∨ Wumpus(r,c) via refutation.
        To prove P: negate P → add ¬P → derive contradiction.
        So we ask(Literal) which adds -Literal = ¬P to KB.
        """
        has_pit    = self.ask(Literal(f"P_{r}_{c}"))
        has_wumpus = self.ask(Literal(f"W_{r}_{c}"))
        steps = has_pit.steps + has_wumpus.steps
        return (has_pit.proved or has_wumpus.proved), steps

    # ── Accessors ─────────────────────────────────────────────────────────

    @property
    def clauses(self) -> List[Clause]:
        return list(self._clauses)

    @property
    def clause_count(self) -> int:
        return len(self._clauses)

    @property
    def total_steps(self) -> int:
        return self._total_steps

    @property
    def tell_log(self) -> List[str]:
        return list(self._tell_log)

    def reset(self) -> None:
        self._clauses.clear()
        self._total_steps = 0
        self._tell_log.clear()

    def __repr__(self) -> str:
        return f"KnowledgeBase({self.clause_count} clauses, {self._total_steps} resolution steps)"