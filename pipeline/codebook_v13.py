"""Codebook v1.3: identical to v1.2 except the relevance rule, tightened after the golden set (31 Oct 2026)
showed every relevance disagreement was AI = relevant, human = not relevant (forum replies, staff answers,
general or regulatory questions). Corpus tags remain v1.2; v1.3 is measured on the golden set and used by
the live 'Tag a comment' page."""
import copy
from codebook import CODEBOOK as _CB12, SYSTEM as _SYS12, RESPONSE_SCHEMA, ITEM_SCHEMA  # noqa: F401

PROMPT_VERSION = "v1.3-2026-11-01"

RELEVANCE_V12 = ("""- relevant = true only if the writer describes their OWN experience, behaviour, question, worry or need about
  SIPs or mutual-fund investing. Generic praise or abuse with no SIP/MF detail ("good app for MF") = false.
  Stock trading, F&O, IPO, loans, brokerage = false unless SIP/MF experience is also described.""")

RELEVANCE_V13 = ("""- relevant = true only if the writer describes their OWN SIP or mutual-fund experience: something they did,
  something that happened to their SIP or money, or a problem they personally hit.
  relevant = false for: replies that explain, answer or advise someone else without describing the writer's own
  SIP/MF experience; answers from platform staff, moderators, support teams or fund houses; general or regulatory
  questions and opinions (how does X work, is X good, what should I buy) with no first-person experience described;
  promotional text; generic praise or abuse with no SIP/MF detail ("good app for MF").
  Stock trading, F&O, IPO, loans, brokerage = false unless SIP/MF experience is also described.""")

assert RELEVANCE_V12 in _SYS12, "v1.2 relevance rule not found verbatim"
SYSTEM = _SYS12.replace(RELEVANCE_V12, RELEVANCE_V13)

CODEBOOK = copy.deepcopy(_CB12)
CODEBOOK["relevant"] = ("true only if the text describes the writer's OWN SIP/mutual-fund experience (something they did or that "
                        "happened to their SIP or money); false for replies to others, staff answers, general questions or opinions "
                        "without own experience, promotion, and stock trading, F&O, IPO or loans")
