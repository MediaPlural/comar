# Comar — the unified feature/UI-UX bank

Standardizes how different apps *name* the same feature into one canonical term,
and stores the reverse-engineered evidence (which app, which class/method, how
implemented) against that term. The result: a coherent, synthesized whole that
feeds the build backlog.

Pipeline: **Coll extracts → Comar standardizes → Bradán synthesizes.**

Same tale as the siblings. Coll (the hazel) produces the wisdom-nuts; Comar (the
confluence) gathers and standardizes them; Bradán (the salmon) assimilates them
into the graph (Segais, the well).

## Quick start

```
python3 comar.py list                              # all canonical terms
python3 comar.py canonicalize "LeftSidebarView"    # -> sidebar
python3 comar.py show sidebar                      # term + aliases + evidence
```

## Layout

```
comar.py            CLI (list / canonicalize / show)
canon/terms.json    canonical taxonomy — term + category + description + aliases
store/evidence.json reverse-engineered evidence keyed by canonical term
```

## Laws

- **One canonical term per concept.** Every app-specific name maps to exactly one
  canonical term (aliases never become terms).
- **Evidence-backed.** A canonical term may have no evidence yet, but never
  fabricated evidence. Evidence carries the source app + extracted classes/methods.
- **Platform-agnostic** (estate law). The taxonomy is tool-independent.

Repo: https://github.com/MediaPlural/comar (MIT). Local: /Users/sharpe/mp-repos/comar.
