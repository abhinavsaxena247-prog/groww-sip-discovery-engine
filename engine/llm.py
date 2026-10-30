"""Gemini calls (server side). The API key comes from Streamlit secrets or the environment and never reaches the browser."""
import json
import os
import re
import time

import requests

MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3-flash-preview"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}"


class QuotaExhausted(Exception):
    pass


_COOLDOWN = {"until": 0.0}   # process-wide: after the free quota runs out, skip AI calls for a while instead of waiting on errors


def ai_available():
    return bool(api_key()) and time.time() >= _COOLDOWN["until"]


def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    try:
        from streamlit.runtime.secrets import secrets_singleton
        if not secrets_singleton.load_if_toml_exists():   # avoids Streamlit's "No secrets found" banner
            return None
        return secrets_singleton.get("GEMINI_API_KEY")
    except Exception:
        return None


def _post(body, timeout=60):
    key = api_key()
    if not key:
        raise QuotaExhausted("no key")
    if time.time() < _COOLDOWN["until"]:
        raise QuotaExhausted("cooling down after the free quota ran out")
    last, daily_out, wait = None, set(), 0
    for rnd in range(3):                       # round 1: switch model on any limit; later rounds: wait as Gemini asks, then retry
        if rnd:
            time.sleep(min(max(wait, 5), 20))
        for m in MODELS:
            if m in daily_out:
                continue
            try:
                r = requests.post(URL.format(m=m, k=key), json=body, timeout=timeout)
            except requests.RequestException as e:
                last = e
                continue
            if r.status_code == 200:
                data = r.json()
                data["_model"] = m
                return data
            if r.status_code == 429 and "PerDay" in r.text:
                daily_out.add(m)               # this model's daily quota is used up
                last = RuntimeError("PerDay quota used")
                continue
            if r.status_code in (429, 500, 503):
                mm = re.search(r'"retryDelay":\s*"(\d+)', r.text)
                wait = max(wait, int(mm.group(1)) + 1 if mm else 8)
                last = RuntimeError(f"{r.status_code} rate limited or busy")
                continue
            last = RuntimeError(f"{r.status_code} {r.text[:200]}")
        if len(daily_out) == len(MODELS):
            break
    _COOLDOWN["until"] = time.time() + (20 * 60 if len(daily_out) == len(MODELS) else 60)
    raise QuotaExhausted(str(last) if last else "all free models are at their daily limit")


def json_call(prompt, schema, system=None):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schema}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    d = _post(body)
    txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"].get("parts", []))
    return json.loads(txt), d["_model"]


def tool_chat(system, turns, tools, executors, max_rounds=5):
    """Function-calling loop. `executors` maps tool name -> python function(args) -> dict."""
    contents = [{"role": t["role"], "parts": [{"text": t["text"]}]} for t in turns]
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
            "tools": [{"functionDeclarations": tools}], "generationConfig": {"temperature": 0}}
    model = None
    for _ in range(max_rounds):
        d = _post(body)
        model = d["_model"]
        cand = d["candidates"][0]["content"]
        parts = cand.get("parts", [])
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if not calls:
            return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip(), model
        contents.append(cand)
        responses = []
        for c in calls:
            try:
                out = executors[c["name"]](c.get("args") or {})
            except Exception as e:        # tool errors go back to the model, the call does not fail
                out = {"error": str(e)}
            responses.append({"functionResponse": {"name": c["name"], "response": {"result": out}}})
        contents.append({"role": "user", "parts": responses})
    body["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
    d = _post(body)
    parts = d["candidates"][0]["content"].get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip(), d["_model"]
