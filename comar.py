#!/usr/bin/env python3
"""Comar — the unified feature/UI-UX bank.

Standardizes app-specific names into one canonical term, stores the
reverse-engineered evidence (which app, which class/method, how implemented)
against that canonical term, and *synthesizes* that evidence into a ranked,
evidence-cited build recommendation.

Pipeline: Coll extracts -> Comar standardizes + synthesizes -> Bradán builds.

Usage:
  python3 comar.py list                              # all canonical terms
  python3 comar.py canonicalize "LeftSidebarView"    # -> sidebar
  python3 comar.py show sidebar                      # term + aliases + evidence
  python3 comar.py synth sidebar                      # legacy one-term spec card
  python3 comar.py synthesize sidebar                 # FULL synthesis: comparison
                                                      # + design pattern + ranked
                                                      # build recommendations
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TERMS = os.path.join(HERE, "canon", "terms.json")
EVIDENCE = os.path.join(HERE, "store", "evidence.json")
DIRECTIVES_GLOB = os.path.join(HERE, "store", "walkthrough-*.json")

# ---------------------------------------------------------------------------
# Mechanism lexicon — the "what varies vs what's shared" vocabulary.
#
# Each aspect is a recurring UI-UX mechanism. A cleaned evidence member is
# tokenized and matched against these trigger words; a member may satisfy
# several aspects at once. This is the design-pattern extraction engine:
# aspects present in >=2 apps are the *shared pattern*; single-app aspects are
# *divergences*. (Ordered by how central the mechanism is to most surfaces.)
# ---------------------------------------------------------------------------
ASPECTS = [
    ("toggle",      ["toggle", "open", "close", "show", "hide", "collapse",
                     "expand", "enable", "disable", "shown", "hidden",
                     "openandclose"]),
    ("position",    ["left", "right", "leading", "trailing", "top", "bottom"]),
    ("pin",         ["pin", "pinned", "unpin", "pinable", "lock", "sticky"]),
    ("move",        ["move", "reorder", "reposition", "drag", "slide", "swipe",
                     "sliding"]),
    ("container",   ["container", "panel", "pane", "view", "holder", "host",
                     "canvas", "dialogpanes", "sheet"]),
    ("divider",     ["divider", "separator", "splitter", "border", "rule"]),
    ("state",       ["state", "current", "active", "selected", "restore",
                     "save", "store", "cache", "persist", "preference"]),
    ("folder",      ["folder", "section", "group", "vault", "category",
                     "channel"]),
    ("item",        ["item", "row", "cell", "entry", "listitem", "list"]),
    ("menu",        ["menu", "popup", "context", "menuitem"]),
    ("header",      ["header", "title", "titlebar", "topbar", "cap"]),
    ("background",  ["background", "backdrop"]),
    ("icon",        ["icon", "glyph", "plusicon"]),
    ("secondary",   ["secondary", "auxiliary", "aux"]),
    ("empty",       ["empty", "none", "blank", "zero"]),
    ("constraint",  ["constraint", "layout", "anchor", "inset"]),
    ("search",      ["search", "filter", "query"]),
    ("scroll",      ["scroll", "scrollbar"]),
]

# Runtime/symbol noise stripped from raw extracted members.
_ADDR = re.compile(r"^\+\s*0x[0-9a-f]+\s+")
_HEX = re.compile(r"\b[0-9a-f]{12,}\b", re.IGNORECASE)
_SWIFT_MANGLE = re.compile(r"^_TtC\d+")
_LEAD_DIGITS = re.compile(r"^\d+")

# Whole-token runtime/symbol noise removed before tokenization.
_NOISE_SUBSTRINGS = (
    "__objc_empty_cache", "_swift_deletedMethodError",
    "_OBJC_METACLASS_$_NSObject",
)


def load(p: str):
    with open(p) as f:
        return json.load(f)


def terms() -> list:
    return load(TERMS)["terms"]


def evidence() -> dict:
    return load(EVIDENCE)


def directives() -> list:
    """All copy-from directives across every walkthrough file in the store."""
    out = []
    for path in sorted(glob.glob(DIRECTIVES_GLOB)):
        try:
            data = load(path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, list):
            out.extend(data)
        elif isinstance(data, dict) and isinstance(data.get("directives"), list):
            out.extend(data["directives"])
    return out


def canonicalize(name: str, terms_list: list) -> str | None:
    n = name.lower().strip()
    best = None
    for t in terms_list:
        tid = t["id"].lower()
        aliases = [a.lower() for a in t.get("aliases", [])]
        if n == tid or n in aliases:
            return t["id"]
        for a in [tid] + aliases:
            if a and (a in n or n in a):
                if best is None or len(a) > best[1]:
                    best = (t["id"], len(a))
    return best[0] if best else None


def entry_members(e: dict) -> list:
    """Collect every reverse-engineered symbol from an evidence entry.

    Evidence entries may carry `members`, `classes`, `methods`, and/or `state`
    lists depending on the extractor; normalize to one flat list.
    """
    out = []
    for key in ("members", "classes", "methods", "state"):
        val = e.get(key)
        if isinstance(val, list):
            out.extend(str(v) for v in val)
    return out


# ---------------------------------------------------------------------------
# Cleaning + tokenization
# ---------------------------------------------------------------------------
def clean_member(raw: str, app: str) -> str:
    """Strip symbol noise and return a readable, de-mangled identifier."""
    s = raw.strip()
    s = _ADDR.sub("", s)
    for noise in _NOISE_SUBSTRINGS:
        s = s.replace(noise, " ")
    # Swift "(Foo in _HASH)" mangling -> keep the readable Foo.
    s = re.sub(r"\(([^()]*?)\s+in\s+_[0-9A-F]+\)", r"\1", s)
    # Swift _TtC<len><Module><len><Class> mangling -> Class name.
    s = _SWIFT_MANGLE.sub("", s)
    for mod in _known_modules():
        s = re.sub(r"^" + re.escape(mod) + r"\.", "", s)   # "Telegram.Foo"
        s = re.sub(r"^" + re.escape(mod) + r"\d+", "", s)  # "Telegram14Foo"
        s = re.sub(r"^\d+" + re.escape(mod), "", s)        # "8Telegram..."
    s = _LEAD_DIGITS.sub("", s)
    # Long hex hashes -> space.
    s = _HEX.sub(" ", s)
    # CSS-module strings "cls--Component_Hash": drop the trailing hash.
    if "--" in s:
        s = s.replace("--", " ")
        s = re.sub(r"_[A-Za-z0-9]{4,8}$", "", s)
    # Leading underscores and stray separators.
    s = s.strip("_:-. ")
    return s


_KNOWN_MODULES: list | None = None


def _known_modules() -> list:
    global _KNOWN_MODULES
    if _KNOWN_MODULES is None:
        names = {"Telegram", "Snagit", "1Password", "Obsidian", "Cursor",
                 "Visual Studio Code", "ChatGPT", "X-Grok", "Conduit", "WeChat",
                 "Perplexity", "Discord", "Hermes", "The Abyss", "Safari",
                 "Shortcuts", "Reins", "Anywhere"}
        for _, entries in evidence().items():
            for e in entries:
                if e.get("app"):
                    names.add(e["app"])
        _KNOWN_MODULES = sorted(names, key=len, reverse=True)
    return _KNOWN_MODULES


def word_tokens(s: str) -> list:
    """Split camelCase/snake/kebab/dot/space into lowercase word tokens."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = s.replace("_", " ").replace("-", " ").replace(".", " ")
    s = s.replace(":", " ").replace("/", " ")
    return [w.lower() for w in s.split() if w]


def classify(words: list) -> list:
    """Return the mechanism aspects a tokenized member satisfies."""
    hits = []
    for aspect, triggers in ASPECTS:
        if any(t in w for w in words for t in triggers):
            hits.append(aspect)
    return hits


def app_aspect_map(entries: list) -> tuple:
    """Build app -> {aspect -> [clean members]} from evidence entries.

    Returns a tuple of (mapping, per-app clean member lists).
    """
    mapping = defaultdict(lambda: defaultdict(list))
    per_app = defaultdict(list)
    for e in entries:
        app = e.get("app", "(unknown)")
        seen = set()
        for raw in entry_members(e):
            cleaned = clean_member(raw, app)
            words = word_tokens(cleaned)
            if not words:
                continue
            label = cleaned
            if label not in seen:
                seen.add(label)
                per_app[app].append(label)
            for aspect in classify(words):
                mapping[app][aspect].append(label)
    # De-dupe aspect member lists, preserving order.
    for app, aspects in mapping.items():
        for aspect, members in aspects.items():
            mapping[app][aspect] = list(dict.fromkeys(members))
    return mapping, {a: list(dict.fromkeys(v)) for a, v in per_app.items()}


# ---------------------------------------------------------------------------
# Legacy synthesis card (kept for backward compatibility)
# ---------------------------------------------------------------------------
def synth_card(t: dict, ev: list) -> str:
    """Emit one canonical term as a synthesis-ready spec card."""
    lines = [f"## {t['id']}  [{t.get('category', '')}]"]
    lines.append(t.get("description", ""))
    aliases = [a for a in t.get("aliases", []) if " " in a or len(a) > 12] or t.get("aliases", [])
    lines.append(f"aliases: {', '.join(aliases)}")
    if ev:
        lines.append(f"evidence ({len(ev)} apps):")
        for e in ev:
            lines.append(f"  - {e['app']}: {', '.join(entry_members(e)[:8])}")
    else:
        lines.append("evidence: none yet (awaiting extraction)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full synthesis
# ---------------------------------------------------------------------------
def synthesize_report(term_id: str, t: dict, entries: list, dirs: list) -> str:
    """Produce the full cross-app synthesis report for one canonical term."""
    app_map, per_app = app_aspect_map(entries)
    apps = sorted(per_app.keys())
    term_dirs = [d for d in dirs if d.get("canonical_term") == term_id]

    # aspect -> set(apps with evidence for it); used for ranking + shared vs divergent.
    aspect_consensus = defaultdict(set)
    for app, aspects in app_map.items():
        for aspect in aspects:
            aspect_consensus[aspect].add(app)

    L: list = []
    L.append(f"# synthesize: {term_id}  [{t.get('category', '')}]")
    L.append(t.get("description", ""))
    aliases = ", ".join(t.get("aliases", []))
    if aliases:
        L.append(f"aliases: {aliases}")
    L.append("")

    # --- directives --------------------------------------------------------
    if term_dirs:
        L.append(f"## Walkthrough directives (copy-from, {len(term_dirs)})")
        seen = set()
        for d in term_dirs:
            text = d.get("directive", "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            L.append(f"  - **{d.get('target_app', '?')}**: {text}")
        L.append("")

    # --- cross-app comparison table ---------------------------------------
    L.append(f"## Cross-app comparison ({len(apps)} app{'s' if len(apps) != 1 else ''})")
    if not apps:
        L.append("  (no evidence in store yet — awaiting Coll extraction)")
        L.append("")
    else:
        L.append(f"  {'app':18} {'aspects':44} clean members")
        L.append(f"  {'-' * 18} {'-' * 44} {'-' * 30}")
        for app in apps:
            aspects = list(app_map[app].keys())
            aspects_sorted = sorted(aspects, key=lambda a: -len(aspect_consensus[a]))
            aspect_str = ", ".join(aspects_sorted)
            members = per_app[app]
            L.append(f"  {app:18} {aspect_str:44} {len(members)}")
        L.append("")

    # --- shared pattern ----------------------------------------------------
    # aspect -> {app -> [clean members]} for aspects present in >=2 apps.
    shared_by_aspect = defaultdict(dict)
    for app, aspects in app_map.items():
        for aspect in aspects:
            if len(aspect_consensus[aspect]) >= 2:
                shared_by_aspect[aspect][app] = aspects[aspect]

    if shared_by_aspect:
        L.append("## Shared pattern — what every app converges on (>=2 apps)")
        ranked = sorted(shared_by_aspect.items(),
                        key=lambda kv: -len(kv[1]))
        for i, (aspect, app_members) in enumerate(ranked, 1):
            L.append(f"  {i}. **{aspect}** ({len(app_members)} apps)")
            for app in sorted(app_members):
                sample = ", ".join(app_members[app][:5])
                L.append(f"       {app}: {sample}")
        L.append("")

    # --- divergences -------------------------------------------------------
    # aspect -> {app -> [clean members]} for single-app aspects.
    divergences = defaultdict(dict)
    for app, aspects in app_map.items():
        for aspect in aspects:
            if len(aspect_consensus[aspect]) == 1:
                divergences[aspect][app] = aspects[aspect]
    if divergences:
        L.append("## Divergences — single-app specifics (build only if you need them)")
        for aspect in sorted(divergences, key=lambda a: -len(next(iter(divergences[a].values())))):
            for app in sorted(divergences[aspect]):
                sample = ", ".join(divergences[aspect][app][:5])
                L.append(f"  - **{aspect}** ({app}): {sample}")
        L.append("")

    # --- ranked build recommendations -------------------------------------
    directive_targets = [d.get("target_app") for d in term_dirs if d.get("target_app")]
    L.append("## Ranked build recommendations")
    if not shared_by_aspect and not divergences:
        L.append("  (nothing to recommend yet — no evidence in store)")
    else:
        # Merge shared + divergences into one ranked list by consensus desc.
        all_aspects = {}
        for aspect, app_members in shared_by_aspect.items():
            all_aspects[aspect] = app_members
        for aspect, app_members in divergences.items():
            all_aspects[aspect] = app_members
        ranked = sorted(all_aspects.items(), key=lambda kv: -len(kv[1]))
        for i, (aspect, app_members) in enumerate(ranked, 1):
            copy_from, reason = _recommend(aspect, app_members, directive_targets)
            L.append(f"  {i}. **{aspect}** — copy from **{copy_from}**"
                     f"  ({len(app_members)} app{'s' if len(app_members) != 1 else ''})")
            L.append(f"       {reason}")
        L.append("")

    # --- build-it-this-way prose ------------------------------------------
    if shared_by_aspect or divergences:
        L.append("## Build it this way (extracted design pattern)")
        L.append(_build_prose(term_id, shared_by_aspect, divergences,
                              directive_targets, per_app))

    return "\n".join(L).rstrip() + "\n"


def _recommend(aspect: str, app_members: dict, directive_targets: list):
    """Pick the best copy-from app for an aspect + a cited reason."""
    # Directive-backed wins: a directive target with evidence for this aspect.
    for target in directive_targets:
        if target in app_members:
            sample = ", ".join(app_members[target][:3])
            return target, f"directive-backed; evidence: {sample}"
    # Otherwise the app with the most specific evidence.
    best = max(app_members.items(), key=lambda kv: len(kv[1]))
    app, members = best
    sample = ", ".join(members[:3])
    return app, f"densest evidence ({len(members)} symbols); e.g. {sample}"


def _build_prose(term_id, shared, divergences, directive_targets, per_app):
    """A paragraph describing the reusable mechanism: common shape + what varies."""
    ranked_shared = sorted(shared.items(), key=lambda kv: -len(kv[1]))
    core = ", ".join(a for a, _ in ranked_shared[:4]) or "a minimal surface"
    variation = ", ".join(sorted(divergences)) or "none"
    if directive_targets:
        primary = directive_targets[0]
        source_line = f"Primary copy source: {primary} (directive of record)."
    elif per_app:
        primary = max(per_app.items(), key=lambda kv: len(kv[1]))[0]
        source_line = f"Primary copy source: {primary} (densest reverse-engineered evidence)."
    else:
        source_line = "Primary copy source: awaiting Coll extraction."
    return (
        f"  Every app implements `{term_id}` as the same core: {core}. "
        f"That shared shape is the part you must build first; the variations "
        f"({variation}) are optional, adopt only if your surface needs them. "
        f"{source_line}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="list canonical terms")
    c = sub.add_parser("canonicalize", help="map an app-specific name to a canonical term")
    c.add_argument("name")
    s = sub.add_parser("show", help="show a canonical term + aliases + evidence")
    s.add_argument("term")
    syn = sub.add_parser("synth", help="emit a synthesized spec card (one term, or --all)")
    syn.add_argument("term", nargs="?", default=None)
    syn.add_argument("--all", action="store_true", help="emit cards for every backed term")
    z = sub.add_parser("synthesize", help="FULL synthesis: comparison + design pattern + ranked build recs")
    z.add_argument("term")
    args = ap.parse_args()

    ts = terms()
    if args.cmd == "list":
        for t in ts:
            print(f"  {t['id']:18} [{t.get('category', '')}]  {t.get('description', '')[:55]}")
    elif args.cmd == "canonicalize":
        r = canonicalize(args.name, ts)
        print(f"  {args.name}  ->  {r or '(unmapped)'}")
    elif args.cmd == "show":
        t = next((x for x in ts if x["id"].lower() == args.term.lower()), None)
        if not t:
            print(f"  no canonical term '{args.term}'")
            return
        print(f"# {t['id']}  [{t.get('category', '')}]")
        print(f"  {t.get('description', '')}")
        print(f"  aliases ({len(t.get('aliases', []))}): {', '.join(t.get('aliases', []))}")
        ev = evidence().get(t["id"], [])
        if ev:
            print(f"  evidence ({len(ev)} source(s)):")
            for e in ev:
                bits = [f"members={', '.join(entry_members(e)[:6])}"]
                print(f"    - {e['app']}: " + " | ".join(bits))
        else:
            print("  evidence: (none yet — awaiting Coll extraction)")
    elif args.cmd == "synth":
        ev = evidence()
        if args.all:
            backed = [t for t in ts if ev.get(t["id"])]
            print(f"# Comar — {len(backed)} backed of {len(ts)} canonical terms\n")
            for t in sorted(backed, key=lambda x: -len(ev.get(x["id"], []))):
                print(synth_card(t, ev.get(t["id"], [])))
                print()
        else:
            if not args.term:
                print("usage: comar.py synth <term>   (or --all)")
                return
            t = next((x for x in ts if x["id"].lower() == args.term.lower()), None)
            if not t:
                print(f"  no canonical term '{args.term}'")
                return
            print(synth_card(t, ev.get(t["id"], [])))
    elif args.cmd == "synthesize":
        term_id = canonicalize(args.term, ts)
        if not term_id:
            print(f"  no canonical term for '{args.term}'")
            return
        t = next((x for x in ts if x["id"] == term_id), None)
        if not t:
            print(f"  no canonical term for '{args.term}'")
            return
        print(synthesize_report(term_id, t, evidence().get(term_id, []), directives()))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
