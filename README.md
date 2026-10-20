# Comar — the unified feature/UI-UX bank

Standardizes how different apps *name* the same feature into one canonical term,
stores the reverse-engineered evidence (which app, which class/method, how
implemented) against that term, and **synthesizes** that evidence into a ranked,
evidence-cited build recommendation.

Pipeline: **Coll extracts → Comar standardizes + synthesizes → Bradán builds.**

Same tale as the siblings. Coll (the hazel) produces the wisdom-nuts; Comar (the
confluence) gathers and standardizes them; Bradán (the salmon) assimilates them
into the graph (Segais, the well).

## Quick start

```
python3 comar.py list                              # all canonical terms
python3 comar.py canonicalize "LeftSidebarView"    # -> sidebar
python3 comar.py show sidebar                      # term + aliases + evidence
python3 comar.py synth sidebar                     # legacy one-term spec card
python3 comar.py synthesize sidebar                # FULL synthesis (see below)
```

## The `synthesize` verb

`synthesize <term>` turns a raw symbol dump into a build backlog item. For a
canonical feature (e.g. `sidebar`) it emits, in one report:

1. **Cross-app comparison** — a table of every app that implements the feature,
   the mechanism aspects it touches, and how many clean symbols it contributes.
2. **Shared pattern** — the mechanism aspects present in ≥2 apps (the common
   shape every app converges on), each with per-app evidence citations.
3. **Divergences** — single-app specifics you should adopt only if your surface
   needs them.
4. **Ranked build recommendations** — each sub-part ranked by consensus, with a
   "copy from X" source: directive-backed when a walkthrough directive names an
   app, otherwise the densest reverse-engineered evidence.
5. **Build it this way** — a prose extraction of the reusable pattern: the shared
   core + what varies + the primary copy source.

Example: `python3 comar.py synthesize sidebar` (see `examples/sidebar-synthesis.md`).

The synthesis is **deterministic** — a mechanism lexicon classifies cleaned
symbol names into recurring UI-UX aspects (toggle, position, pin, move,
container, divider, state, …). The walkthrough directives
(`store/walkthrough-*.json`) are the highest-authority copy-source signal;
reverse-engineered evidence is the fallback density signal.

## Layout

```
comar.py            CLI (list / canonicalize / show / synth / synthesize)
mcp-server.py       MCP stdio server (agents drive the bank: + synthesize)
canon/terms.json    canonical taxonomy — term + category + description + aliases
store/evidence.json reverse-engineered evidence keyed by canonical term
store/walkthrough-*.json   copy-from directives (term + target app)
examples/           committed demo syntheses
```

## Laws

- **One canonical term per concept.** Every app-specific name maps to exactly one
  canonical term (aliases never become terms).
- **Evidence-backed.** A canonical term may have no evidence yet, but never
  fabricated evidence. Evidence carries the source app + extracted classes/methods.
- **Platform-agnostic** (design law). The taxonomy is tool-independent.
- **Builder ≠ auditor.** Comar recommends, never fabricates; a recommendation is
  only as strong as the evidence + directives it cites.

Repo: https://github.com/MediaPlural/comar (MIT).
