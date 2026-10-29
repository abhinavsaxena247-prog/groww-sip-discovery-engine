"""Reddit-specific narrowing + stratified sample (free-tier tagging budget).
Step 1: personal-experience SIP filter (first-person + SIP/MF behaviour words).
Step 2: stratified random sample (subreddit x post/comment), fixed seed, target N.
Output: raw/reddit_sample.json (fed into stage1 as a normal source) + out/reddit_sample_stats.json."""
import json, re, random, collections, sys

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
random.seed(20261029)
rows = json.load(open("/home/claude/engine/raw/reddit.json"))
stats = {"collected": len(rows)}

FIRST_PERSON = re.compile(r"\b(i|i'm|i am|i've|i have|my|me|mine|i was|we)\b", re.I)
SIP_BEHAV = re.compile(r"(\bsips?\b.{0,60}(stop|paus|skip|cancel|fail|bounc|miss|start|continu|increas|step.?up|reduc|redeem|band|mandate|autopay|debit)|"
                       r"(stop|paus|skip|cancel|start|started|continu|increas|reduc).{0,40}\bsips?\b|"
                       r"(autopay|auto-pay|mandate|e-?nach|instal+ment).{0,60}(fail|bounc|miss|not|reject|declin|cancel)|"
                       r"(first|new to|beginner|just started|started investing).{0,60}(sip|mutual fund|mf|invest)|"
                       r"(red|negative|loss|down).{0,40}(sip|portfolio|mutual fund)|(groww).{0,80}(sip|mutual|mf))", re.I)
DROP = re.compile(r"\[(removed|deleted)\]")
f = [r for r in rows if not DROP.search(r["text"]) and len(r["text"].split()) >= 8
     and FIRST_PERSON.search(r["text"]) and SIP_BEHAV.search(r["text"])]
stats["after_personal_sip_filter"] = len(f)

strata = collections.defaultdict(list)
for r in f:
    strata[(r["app"], "post" if r.get("is_op") else "comment")].append(r)
total = len(f)
sample = []
for k, v in strata.items():
    n = max(1, round(TARGET * len(v) / total)) if total > TARGET else len(v)
    sample += random.sample(v, min(n, len(v)))
stats["sample"] = len(sample)
stats["strata"] = {f"{a}|{b}": {"pool": len(v), "sampled": sum(1 for s in sample if (s['app'], 'post' if s.get('is_op') else 'comment') == (a, b))}
                   for (a, b), v in strata.items()}
json.dump(sample, open("/home/claude/engine/raw/reddit_sample.json", "w"), ensure_ascii=False)
json.dump(stats, open("/home/claude/engine/out/reddit_sample_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
