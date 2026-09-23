#!/usr/bin/env python3
"""Small local conversational bot for managing a Ludo Star club.

This app manages club data only; it does not automate or control Ludo Star gameplay.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8000
DATA_FILE = Path(__file__).with_name("members.json")


def load_members() -> dict[str, dict]:
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_members(members: dict[str, dict]) -> None:
    DATA_FILE.write_text(json.dumps(members, indent=2, sort_keys=True), encoding="utf-8")


def key_for(name: str) -> str:
    return " ".join(name.strip().lower().split())


def display_name(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split())


def help_text() -> str:
    return (
        "Try: `add member NAME`, `list members`, `stats NAME`, `record win NAME`, "
        "`record loss NAME`, `note NAME TEXT`, or `remove member NAME`."
    )


def handle_message(message: str, members: dict[str, dict]) -> str:
    text = " ".join(message.strip().split())
    lowered = text.lower()
    if not text:
        return "Send a command, or type `help`."
    if lowered in {"help", "hello", "hi", "start"}:
        return "Hi! I manage your Ludo Star club. " + help_text()

    if lowered in {"list", "list members", "members", "show members"}:
        if not members:
            return "There are no club members yet. Add one with `add member NAME`."
        rows = []
        for member in sorted(members.values(), key=lambda item: item["name"].lower()):
            rows.append(
                f"- {member['name']}: {member['wins']}W/{member['losses']}L "
                f"({member['games']} games)"
            )
        return "Club members:\n" + "\n".join(rows)

    match = re.fullmatch(r"add member (.+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        if len(name) < 2 or len(name) > 50:
            return "Member names must be between 2 and 50 characters."
        key = key_for(name)
        if key in members:
            return f"{members[key]['name']} is already a club member."
        members[key] = {"name": name, "wins": 0, "losses": 0, "games": 0, "notes": []}
        save_members(members)
        return f"Added {name} to the club."

    match = re.fullmatch(r"(?:stats|profile) (.+)", text, re.IGNORECASE)
    if match:
        member = members.get(key_for(match.group(1)))
        if not member:
            return "I couldn't find that member."
        notes = "; ".join(member["notes"]) or "none"
        return (
            f"{member['name']}: {member['wins']} wins, {member['losses']} losses, "
            f"{member['games']} games. Notes: {notes}"
        )

    match = re.fullmatch(r"record (win|loss) (.+)", text, re.IGNORECASE)
    if match:
        result, name = match.groups()
        member = members.get(key_for(name))
        if not member:
            return "I couldn't find that member. Add them first with `add member NAME`."
        field = "wins" if result.lower() == "win" else "losses"
        member[field] += 1
        member["games"] += 1
        save_members(members)
        return f"Recorded a {result.lower()} for {member['name']}."

    match = re.fullmatch(r"note (.+?) (.+)", text, re.IGNORECASE)
    if match:
        name, note = match.groups()
        member = members.get(key_for(name))
        if not member:
            return "I couldn't find that member."
        member["notes"].append(note)
        save_members(members)
        return f"Saved a note for {member['name']}."

    match = re.fullmatch(r"remove member (.+)", text, re.IGNORECASE)
    if match:
        key = key_for(match.group(1))
        member = members.pop(key, None)
        if not member:
            return "I couldn't find that member."
        save_members(members)
        return f"Removed {member['name']} from the club."

    return "I didn't recognize that command. " + help_text()


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ludo Star Club Bot</title>
<style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;background:#f5f7fb;color:#172033}
main{background:white;border-radius:14px;padding:1.2rem;box-shadow:0 4px 20px #0001}h1{margin-top:0}
#chat{min-height:260px;white-space:pre-wrap;border:1px solid #dbe1eb;border-radius:10px;padding:1rem;margin-bottom:1rem}
.msg{margin:.6rem 0}.you{color:#315db5}.bot{color:#16805d}form{display:flex;gap:.5rem}input{flex:1;padding:.75rem;border:1px solid #bbc5d4;border-radius:8px}button{padding:.75rem 1rem;border:0;border-radius:8px;background:#315db5;color:white;cursor:pointer}
small{color:#637087}
</style></head><body><main><h1>🎲 Ludo Star Club Bot</h1><small>Club management assistant — it does not play the game.</small><div id="chat"><div class="msg bot"><b>Bot:</b> Hi! Type <code>help</code> to see what I can do.</div></div>
<form id="form"><input id="message" autocomplete="off" placeholder="e.g. add member Fatima"><button>Send</button></form></main>
<script>
const chat=document.querySelector('#chat'), input=document.querySelector('#message');
document.querySelector('#form').addEventListener('submit',async(e)=>{e.preventDefault();const message=input.value.trim();if(!message)return;chat.innerHTML+=`<div class="msg you"><b>You:</b> ${escapeHtml(message)}</div>`;input.value='';const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});const data=await r.json();chat.innerHTML+=`<div class="msg bot"><b>Bot:</b> ${escapeHtml(data.reply)}</div>`;chat.scrollTop=chat.scrollHeight;});
function escapeHtml(value){return value.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
</script></body></html>"""


class BotHandler(BaseHTTPRequestHandler):
    members = load_members()

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/members":
            self.send_json({"members": list(self.members.values())})
            return
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/chat":
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            reply = handle_message(str(payload.get("message", "")), self.members)
            self.send_json({"reply": reply})
        except (ValueError, json.JSONDecodeError):
            self.send_json({"error": "Send JSON with a message field."}, 400)


if __name__ == "__main__":
    print(f"Ludo Star club bot running at http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), BotHandler).serve_forever()
