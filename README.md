# NL-Groww Discovery Engine

An AI discovery engine for one question: **why do first-time mutual fund investors in India keep, pause or stop their SIPs?**

Independent student research for a NextLeap course project. Not affiliated with Groww. **Not investment advice:** the engine describes what investors wrote in public comments and never recommends a fund, stock or action.

## What it does
- **Ask the engine:** a chat that answers any question about SIP behaviour from 21,445 AI-tagged public comments. Every reply goes through four checks:
  1. a rule check on the question (abuse in English, Hinglish and Hindi; personal data; attempts to override the rules; advice and off-topic requests);
  2. an AI intent check;
  3. a grounded answer built from counting tools;
  4. an output check (every number must trace to the counts; no fund names, advice wording, urgency or personal data).
- **Basic terms:** "what is a SIP / NAV / XIRR / mandate" and similar get a plain definition (not advice) plus a counted fact from the data.
- **Findings, Opportunities, Evidence explorer:** theme counts, the opportunity comparison and the verbatim evidence behind them.
- **Quality and evals:** a 169-question eval suite (development set plus two held-out sets) with results per category.
- **How it works:** the pipeline, sources, volumes and limits.

## Data
344,872 public items were collected from Play Store and App Store reviews (Groww and 9 comparison apps), Reddit, YouTube comments, TradingQnA, Zerodha Varsity and Team-BHP. After cleaning, 33,457 remained; 27,678 were AI-tagged and 21,445 judged relevant. No usernames, account details or screenshots are stored.

## Layout
| Folder | Contents |
|---|---|
| `app.py`, `views/` | Streamlit app |
| `engine/` | Guardrails (`guard.py`), counting tools (`data.py`), Gemini calls (`llm.py`), chat pipeline (`pipeline.py`) |
| `pipeline/` | Collection, cleaning, AI tagging and analysis scripts |
| `evals/run_evals.py` | Eval runner: `python -m evals.run_evals basic` or `python -m evals.run_evals ai` |
| `data/` | Tagged corpus, analysis outputs, eval cases and results |

## Run locally
```
pip install -r requirements.txt
export GEMINI_API_KEY=...   # optional; without it the chat runs in basic mode (direct counts, same checks)
streamlit run app.py
```
On Streamlit Community Cloud, add `GEMINI_API_KEY` under the app's **Secrets**. Never commit keys.
