"""Gemini calls (server side). The API key comes from Streamlit secrets or the environment and never reaches the browser."""
import json
import os
import time

import requests

MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}"


class QuotaExhausted(Exception):
    pass


def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _post(body, timeout=90):
    key = api_key()
    if not key:
        raise QuotaExhausted("no key")
    last = None
    for m in MODELS:
        for attempt in range(3):
            try:
                r = requests.post(URL.format(m=m, k=key), json=body, timeout=timeout)
            except requests.RequestException as e:
                last = e
                time.sleep(2)
                continue
            if r.status_code == 200:
                data = r.json()
                data["_model"] = m
                return data
            if r.status_code == 429 and "PerDay" in r.text:
                break                      # this model's daily quota is used up: try the next model
            if r.status_code in (429, 500, 503):
                time.sleep(4 * (attempt + 1))
                continue
            last = RuntimeError(f"{r.status_code} {r.text[:200]}")
            break
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
