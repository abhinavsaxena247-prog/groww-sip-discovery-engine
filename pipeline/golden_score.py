"""Score AI tags against the human golden labels with the same rules as the first pass (Golden Set Results workbook):
relevant = exact; event = labeller's event among AI events (none = AI has none); drop-off = exact; reason = labeller's
reason among AI drivers (none = AI has none). Practice items GS01-GS02 excluded. Guardrail check uses the same
fund-name and advice patterns as the first pass, on the AI-written fields."""
import json, re
from openpyxl import load_workbook
FUND = re.compile(r"\b(parag parikh|ppfas|nippon|hdfc|icici|sbi|axis|mirae|quant|kotak|uti|motilal|tata|nifty ?50|small ?cap|mid ?cap|flexi ?cap)\b", re.I)
ADVICE = re.compile(r"(you should (buy|invest|stop|continue)|invest in |switch to |best fund|recommend(ed)? fund|don't stop|keep investing)", re.I)

def labels():
    ws = load_workbook("/home/claude/groww-sip-discovery-engine/data/NL-Groww_Golden_Set_Results.xlsx")["Items"]
    out = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0]: out.append({"gs": r[0], "practice": r[1] == "Yes", "stratum": r[2], "source": r[3], "text": r[4],
                             "h": {"relevant": r[5], "event": r[6], "drop": r[7], "reason": r[8]}})
    return out

def score(tags_by_index):
    L = labels(); rows = []; tot = {"relevant": 0, "event": 0, "drop": 0, "reason": 0}; n = 0; viol = 0
    for i, l in enumerate(L):
        t = tags_by_index[i]
        ai = {"relevant": "yes" if t["relevant"] else "no", "event": t.get("event") or [], "drop": t.get("dropoff_type", "none"), "reason": t.get("drivers") or []}
        m = {"relevant": int(l["h"]["relevant"] == ai["relevant"]),
             "event": int(l["h"]["event"] in ai["event"] or (l["h"]["event"] == "none" and not ai["event"])),
             "drop": int(l["h"]["drop"] == ai["drop"]),
             "reason": int(l["h"]["reason"] in ai["reason"] or (l["h"]["reason"] == "none" and not ai["reason"]))}
        txt = " ".join([t.get("unmet_need", ""), t.get("expectation_gap", ""), t.get("emergent_theme", "")])
        v = bool(FUND.search(txt) or ADVICE.search(txt)); viol += v
        if not l["practice"]:
            n += 1
            for k in tot: tot[k] += m[k]
        rows.append({"gs": l["gs"], "practice": l["practice"], "h": l["h"], "ai": ai, "match": m, "violation": v})
    return {"n": n, "fields": tot, "overall": sum(tot.values()), "guardrail_violations": viol, "rows": rows}

if __name__ == "__main__":
    G = json.load(open("/home/claude/engine/out/golden_selection.json"))
    R = json.load(open("/home/claude/engine/out/golden_retag.json"))
    runs = {"first_pass_corpus_v1.2": [g for g in G], "rerun_v1.2": [R["v1.2"][g["id"]] for g in G], "v1.3": [R["v1.3"][g["id"]] for g in G]}
    res = {k: score(v) for k, v in runs.items()}
    for k, v in res.items():
        print(k, "n", v["n"], v["fields"], "overall", v["overall"], "/", 4 * v["n"], f"{100*v['overall']/(4*v['n']):.0f}%", "viol", v["guardrail_violations"])
    json.dump({k: {kk: vv for kk, vv in v.items()} for k, v in res.items()}, open("/home/claude/engine/out/golden_scores.json", "w"), ensure_ascii=False, indent=1)
    print("\nper item (scored only): first-pass vs v1.3 relevant/event/drop/reason")
    for a, b in zip(res["first_pass_corpus_v1.2"]["rows"], res["v1.3"]["rows"]):
        if a["match"] != b["match"] or a["ai"]["relevant"] != b["ai"]["relevant"]:
            print(a["gs"], "practice" if a["practice"] else "", "human", a["h"], "| v1.2 rel", a["ai"]["relevant"], a["match"], "| v1.3 rel", b["ai"]["relevant"], b["ai"]["event"], b["ai"]["drop"], b["ai"]["reason"], b["match"])
