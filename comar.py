#!/usr/bin/env python3
"""Comar — the unified feature/UI-UX bank.

Standardizes app-specific names into one canonical term, and stores the
reverse-engineered evidence (which app, which class/method, how implemented)
against that canonical term.

Pipeline: Coll extracts -> Comar standardizes -> Bradán synthesizes.

Usage:
  python3 comar.py list                              # all canonical terms
  python3 comar.py canonicalize "LeftSidebarView"    # -> sidebar
  python3 comar.py show sidebar                      # term + aliases + evidence
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TERMS = os.path.join(HERE, "canon", "terms.json")
EVIDENCE = os.path.join(HERE, "store", "evidence.json")


def load(p: str):
    with open(p) as f:
        return json.load(f)


def terms() -> list:
    return load(TERMS)["terms"]


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


def evidence() -> dict:
    return load(EVIDENCE)


def synth_card(t: dict, ev: list) -> str:
    """Emit one canonical term as a synthesis-ready spec card."""
    lines = [f"## {t['id']}  [{t.get('category', '')}]"]
    lines.append(t.get("description", ""))
    aliases = [a for a in t.get("aliases", []) if " " in a or len(a) > 12] or t.get("aliases", [])
    lines.append(f"aliases: {', '.join(aliases)}")
    if ev:
        lines.append(f"evidence ({len(ev)} apps):")
        for e in ev:
            members = list(e.get("members") or e.get("classes") or [])
            if e.get("methods"):
                members += e["methods"]
            if e.get("state"):
                members += e["state"]
            lines.append(f"  - {e['app']}: {', '.join(members[:8])}")
    else:
        lines.append("evidence: none yet (awaiting extraction)")
    return "\n".join(lines)


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
                bits = [f"classes={', '.join(e.get('classes', []))}"]
                if e.get("members"):
                    bits.append(f"members={', '.join(e['members'])}")
                if e.get("methods"):
                    bits.append(f"methods={', '.join(e['methods'])}")
                if e.get("state"):
                    bits.append(f"state={', '.join(e['state'])}")
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
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
