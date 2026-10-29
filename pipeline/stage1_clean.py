"""Stage 1: merge sources, de-duplicate, filter promo/noise, keep SIP/MF-relevant items.
Writes out/stage1.json and out/stage1_stats.json (feeds the Evidence Log)."""
import json, re, hashlib, collections, glob

RAW = "/home/claude/engine/raw"
rows = []
for f in sorted(glob.glob(f"{RAW}/*.json")):
    if f.endswith("/reddit.json"): continue  # full Reddit dump; the stratified sample (reddit_sample.json) is used instead
    rows += json.load(open(f))
stats = {"collected": collections.Counter(r["source"] for r in rows)}

def norm(t): return re.sub(r"[^a-z0-9ऀ-ॿ ]", "", (t or "").lower()).strip()

# 1. exact + near-exact duplicates (same normalised text) and repeated IDs
seen_id, seen_txt, dedup = set(), set(), []
dup = collections.Counter()
for r in rows:
    k = norm(r["text"])
    h = hashlib.md5(k[:300].encode()).hexdigest()
    if r["id"] in seen_id or h in seen_txt:
        dup[r["source"]] += 1; continue
    seen_id.add(r["id"]); seen_txt.add(h); dedup.append(r)
stats["duplicates_removed"] = dup

# 2. too short / promotional / spam
PROMO = re.compile(r"(refer(ral)? code|use my code|join (my|our) (telegram|whatsapp)|t\.me/|bit\.ly|"
                   r"earn \d+ ?(k|rs|₹) (daily|per day)|guaranteed returns? of|dm me for tips|call \+?\d{10})", re.I)
short, promo, kept = collections.Counter(), collections.Counter(), []
for r in dedup:
    t = r["text"] or ""
    if len(norm(t).split()) < 6: short[r["source"]] += 1; continue
    if PROMO.search(t): promo[r["source"]] += 1; continue
    kept.append(r)
stats["too_short_removed"] = short
stats["promotional_removed"] = promo

# 3. relevance to SIP / mutual-fund investing (English + Hinglish + Devanagari)
SIP = re.compile(r"(\bsips?\b|systematic invest|mutual ?funds?|\bmfs?\b|\bnav\b|elss|index fund|"
                 r"instal+ment|\bkisht|mandate|auto ?-?pay|e-?nach|\bnach\b|step.?up|\bxirr\b|folio|"
                 r"redeem|redemption|lump ?sum|\bamc\b|direct plan|regular plan|"
                 r"एसआईपी|म्यूचुअल|किस्त|निवेश)", re.I)
TRADING_ONLY = re.compile(r"(\bf&o\b|\bf ?and ?o\b|option chain|intraday|scalp|candle|chart|\bmtf\b|"
                          r"brokerage|stop ?loss|\bipo\b|futures|greeks|\boi\b)", re.I)
rel, irr = [], collections.Counter()
for r in kept:
    t = r["text"]
    if r["source"] == "tradingqna" and r.get("thread") and SIP.search(r["thread"]) and not TRADING_ONLY.search(t):
        rel.append(r); continue
    if SIP.search(t):
        # drop items that only mention MF in passing inside a trading complaint
        if TRADING_ONLY.search(t) and len(SIP.findall(t)) < 2 and not re.search(r"\bsips?\b", t, re.I):
            irr[r["source"]] += 1; continue
        rel.append(r)
    else:
        irr[r["source"]] += 1
stats["not_relevant_removed"] = irr

# 4. language tag (for Hinglish / regional handling)
DEV = re.compile(r"[ऀ-ॿ]")
HINGLISH = re.compile(r"\b(hai|nahi|nhi|kya|kar|karo|kaise|paisa|paise|mera|meri|bhai|ho gaya|hota|chahiye|band|kyu|kyun)\b", re.I)
for r in rel:
    r["lang"] = "hindi_devanagari" if DEV.search(r["text"]) else ("hinglish" if len(HINGLISH.findall(r["text"])) >= 2 else "english")
stats["relevant_kept"] = collections.Counter(r["source"] for r in rel)
stats["relevant_by_app"] = collections.Counter(r["app"] for r in rel)
stats["lang"] = collections.Counter(r["lang"] for r in rel)
stats["date_window"] = {s: [min(x["date"] for x in rel if x["source"] == s and x["date"]),
                            max(x["date"] for x in rel if x["source"] == s and x["date"])]
                        for s in stats["relevant_kept"]}
json.dump(rel, open("/home/claude/engine/out/stage1.json", "w"), ensure_ascii=False)
json.dump({k: dict(v) if isinstance(v, collections.Counter) else v for k, v in stats.items()},
          open("/home/claude/engine/out/stage1_stats.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: dict(v) if isinstance(v, collections.Counter) else v for k, v in stats.items()}, indent=1, ensure_ascii=False))
