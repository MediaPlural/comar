#!/usr/bin/env python3
"""Comar MCP server — agents drive the feature/UI-UX bank via MCP (stdio JSON-RPC).

Tools: list, canonicalize, show, synth, synth_all
Run: python3 mcp-server.py
Protocol: MCP stdio — JSON-RPC 2.0 over line-delimited messages. No external deps.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMAR = os.path.join(HERE, "comar.py")

TOOLS = [
    {"name": "list",
     "description": "List all canonical feature/UI-UX terms (id + category).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "canonicalize",
     "description": "Map an app-specific name (e.g. 'LeftSidebarView') to its canonical term.",
     "inputSchema": {"type": "object",
                     "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "show",
     "description": "Show one canonical term: definition, aliases, cross-app evidence.",
     "inputSchema": {"type": "object",
                     "properties": {"term": {"type": "string"}}, "required": ["term"]}},
    {"name": "synth",
     "description": "Emit a synthesis-ready spec card for one canonical term.",
     "inputSchema": {"type": "object",
                     "properties": {"term": {"type": "string"}}, "required": ["term"]}},
    {"name": "synth_all",
     "description": "Emit the full synthesized spec (all backed canonical terms).",
     "inputSchema": {"type": "object", "properties": {}}},
]


def call_tool(name, args):
    cmd = ["python3", COMAR]
    if name == "list":
        cmd += ["list"]
    elif name == "canonicalize":
        cmd += ["canonicalize", args.get("name", "")]
    elif name == "show":
        cmd += ["show", args.get("term", "")]
    elif name == "synth":
        cmd += ["synth", args.get("term", "")]
    elif name == "synth_all":
        cmd += ["synth", "--all"]
    else:
        return {"isError": True, "content": [{"type": "text", "text": f"unknown tool: {name}"}]}
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    text = (proc.stdout or "") + ((proc.stderr or "") if proc.returncode != 0 else "")
    return {"content": [{"type": "text", "text": text[-8000:]}], "isError": proc.returncode != 0}


def rpc(result_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": result_id, "result": result}) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        mid = msg.get("id")
        if method == "initialize":
            rpc(mid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "comar", "version": "0.1.0"}})
        elif method == "notifications/initialized" or method is None:
            continue
        elif method == "tools/list":
            rpc(mid, {"tools": TOOLS})
        elif method == "tools/call":
            rpc(mid, call_tool(msg["params"]["name"], msg["params"].get("arguments", {})))
        else:
            if mid is not None:
                sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid,
                                             "error": {"code": -32601, "message": f"unknown method {method}"}}) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
