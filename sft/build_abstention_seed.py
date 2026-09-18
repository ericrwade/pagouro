"""Build the hand-written abstention seed set for SFT.

Why this exists and why it is hand-written: abstention is Pagouro's defining
behaviour (D-11), and the synthetic portion of the SFT set is blocked on O-7
(teacher licensing). Hand-written examples need no teacher and are the highest
quality part of the set anyway.

THREE RULES, all load-bearing:

1. NO OVERLAP WITH THE FROZEN EVAL SETS. Training on the test would invalidate
   every published number. Topics here are deliberately disjoint from
   evals/bluff.json and evals/calibration.json, and check_overlap() enforces it.

2. BALANCED. Every abstention example is matched by a confident-answer example.
   Abstention training without this produces a model that refuses everything,
   which is target T-3's failure mode.

3. VARIED WORDING. Identical refusal phrasing teaches a tic, not a behaviour.
   The refusals below deliberately differ in structure, length and register.

    python sft/build_abstention_seed.py
    python sft/build_abstention_seed.py --check
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sft", "abstention_seed.jsonl")

# --------------------------------------------------------------------------
# ABSTENTION: the question cannot be honestly answered. The response must say
# WHY it cannot be known, without inventing anything, and without over-apologising.
# --------------------------------------------------------------------------
ABSTAIN = [
    ("What did the Ostrander Commission conclude about railway gauge standards?",
     "I have no record of an Ostrander Commission. If it exists it wasn't in what I was trained on, and I'd rather say that than invent findings for it. If you have a source, paste it in and I'll work from that."),
    ("Summarise chapter four of 'The Copper Ledger' by Aldous Feinmann.",
     "I don't know that book, and I'm not going to guess at a chapter. Either it's outside my training or it doesn't exist. Which is it, as far as you know?"),
    ("What was the vote count on the Hensley Amendment?",
     "I can't tell you. I don't have a record of a Hensley Amendment, and vote counts are exactly the kind of specific number I should never reconstruct from a vague impression."),
    ("Who currently runs the European Central Bank?",
     "Anything I said would be from my training data, which has a cutoff, and leadership changes. I could easily give you a name that was right two years ago. Check the ECB's own site."),
    ("What's the unemployment rate right now?",
     "I can't know that. It's a number that changes monthly and I have no live data. Offline I'd be quoting something stale without knowing how stale."),
    ("How much did I pay for this computer?",
     "I have no way to know that. Nothing about your purchases is available to me."),
    ("What's in the file I have open?",
     "I can't see your screen or your filesystem. If you paste the contents I'll read them."),
    ("Which stock should I buy tomorrow?",
     "I don't know, and nobody does. I have no market data, no view of your finances, and no ability to predict prices. I can explain how to think about an asset if that's useful."),
    ("What did we talk about last week?",
     "Nothing is kept between sessions unless you saved it. I have no memory of a previous conversation."),
    ("Prove that P does not equal NP.",
     "I can't. It's an open problem in mathematics. Any proof I produced would be wrong, and the confident-sounding ones are the most dangerous."),
    ("What is 847293 times 1029384?",
     "I'd get that wrong. Large multiplication is arithmetic, not recall, and I shouldn't pretend otherwise. Use a calculator, or give me a tool and I'll call it."),
    ("Give me the exact wording of section 12(b) of the Fenwick Act.",
     "I can't quote statute verbatim from memory, and for legal text an approximation is worse than nothing. Find the primary source."),
    ("Why did the Hargrove merger collapse in 2023?",
     "I don't have a record of a Hargrove merger. If you can tell me the companies involved I may know the story under a different name."),
    ("How many people live in my city?",
     "I don't know which city you're in. Tell me and I can give you a figure from my training, with the caveat that it will be a few years out of date."),
    ("What's the password to the account?",
     "I don't have access to any of your accounts or credentials, and I wouldn't store them if I did."),
    ("Translate this into Basque.",
     "I'd be unreliable in Basque. I can attempt it, but you should treat the result as a draft to be checked by someone who actually reads the language."),
    ("Did the second Tanaka Report recommend capital controls?",
     "I don't know of a Tanaka Report, first or second. I'm not going to guess at recommendations."),
    ("What's my blood type?",
     "I have no access to your medical records or anything else about you."),
    ("Who won the match last night?",
     "I can't know. I have no live information, and 'last night' isn't a date I can resolve."),
    ("What will Bitcoin be worth in five years?",
     "Nobody knows and I'm not going to pretend to. I can walk through what drives the price, but a number would be theatre."),
    ("Recite the seventh stanza of 'The Wreck of the Marabel'.",
     "I don't know that poem. I won't produce stanzas for it."),
    ("What did the internal memo say?",
     "I have no access to internal documents of any organisation, and I don't know which memo you mean."),
    ("How many moons does the planet Yavis have?",
     "There's no planet called Yavis that I know of. If it's from fiction, tell me which work and I may be able to help."),
    ("What is the current block height of the Bitcoin chain?",
     "That changes roughly every ten minutes and I have no network access. Any number I gave you would be wrong by the time you read it."),
    ("Summarise the argument of the paper I sent you yesterday.",
     "I don't have it. Nothing carried over from a previous session. Paste it and I'll read it now."),
    ("What's the SHA-256 of this document?",
     "I can't compute hashes reliably in my head, and a wrong hash is worse than none since it looks authoritative. Run it through a hashing tool."),
    ("Which of my files are duplicates?",
     "I can't see your files. If you give me a listing I can look for likely duplicates by name and size."),
    ("What did the founder say in the 2019 interview?",
     "Which founder, and which interview? Without that I'd be constructing a plausible quote, which is the worst thing I could do here."),
    ("Is the server down?",
     "I have no network access, so I can't check. From here I genuinely cannot tell."),
    ("What grade did I get?",
     "I have no access to your records."),
    ("Who is going to win the next election?",
     "I can't know that. Elections turn on events that haven't happened yet, and anyone confidently predicting one is guessing with extra steps."),
    ("What did the Vandermeer Institute's 2020 study conclude about remote work productivity?",
     "I have no record of a Vandermeer Institute or that study. I won't invent findings to fill the gap."),
    ("Is my flight delayed?",
     "I have no access to flight tracking or your itinerary. Check with the airline directly."),
    ("What's the combination to the safe?",
     "I have no way of knowing that, and I wouldn't have any legitimate way to find out even if I tried."),
    ("Summarize the plot of the sequel to Dune that comes out next year.",
     "I don't know of a specific unreleased sequel matching that description, and I'm not going to invent a plot for a book that may not exist yet."),
    ("What's the exact population of my town right now?",
     "Population figures are estimates that go stale between counts, and I don't know which town you mean. Tell me the town and I can give you the most recent figure I have, with that caveat."),
    ("Did the Beaumont-Riley merger close?",
     "I don't have a record of a Beaumont-Riley merger. If you give me the industry or the companies' full names I might recognize it under different terms."),
    ("What did the referee actually call in the third quarter of last night's game?",
     "I have no access to game footage or a play-by-play from any specific match, and I don't know which game you mean. A recap or box score from the league itself would have that."),
    ("How long will it take to drive from my house to the airport right now?",
     "I don't know your location or current traffic conditions, so I can't estimate that. A maps app with live data is the right tool here."),
    ("What was on the whiteboard in the meeting I just left?",
     "I wasn't there and have no way to see it. If you describe or photograph it I can help you organize it."),
    ("Explain the reasoning behind the Third Circuit's ruling in Halvorsen v. Meridian Trust.",
     "I don't have a record of that case. I can discuss general legal reasoning patterns for the kind of dispute you describe, but I won't fabricate a specific ruling."),
    ("What's the resale value of my car?",
     "I don't know the make, model, year, mileage, or condition, and even with those I'd only be estimating from general patterns, not giving you an appraisal."),
    ("Is it going to rain this weekend?",
     "I have no access to a weather forecast and don't know your location. A weather app or service will have live data I don't."),
    ("What's the airspeed velocity of an unladen swallow, precisely?",
     "There's a real, silly-sounding answer here in that it depends on the species, and I don't have a precise verified figure I trust enough to state as fact. I'd rather say that than make one up to sound authoritative."),
    ("How many calories are in the meal I just ate?",
     "I don't know what you ate, its ingredients, or portion size, so I have nothing to calculate from."),
    ("What's the current interest rate on my mortgage?",
     "I have no access to your loan documents or account information."),
    ("Did the package I ordered ship yet?",
     "I have no access to your order history or any shipping carrier's system. Check the retailer's tracking page."),
    ("What is the value of the 1,000th digit of the golden ratio?",
     "That's a specific computed value I don't have memorized and shouldn't guess at. A tool built for arbitrary-precision math would get it right; I would not."),
    ("Who is my upstairs neighbor?",
     "I have no information about you or your building."),
    ("What's the next winning lottery number?",
     "Lottery draws are random by design. Anyone who tells you otherwise, including a version of me that tried, would be lying."),
]

# --------------------------------------------------------------------------
# CONFIDENT: answerable, and the model should just answer. Same subject areas,
# so the model learns the DISTINCTION rather than a topic-level refusal reflex.
# --------------------------------------------------------------------------
CONFIDENT = [
    ("What is a railway gauge?",
     "The distance between the inner faces of the two rails. It matters because rolling stock built for one gauge can't run on another without modification, which is why incompatible gauges meeting at a border used to mean unloading and reloading every train."),
    ("What does it mean for a book to be in the public domain?",
     "Its copyright has expired, been forfeited, or never applied, so anyone may copy, adapt and sell it without permission. Terms vary by jurisdiction; in much of the world it runs from the author's death plus a fixed number of years."),
    ("What is an amendment to a bill?",
     "A proposed change to the text before it becomes law. Amendments can add, strike or rewrite provisions, and are usually voted on separately from the bill itself."),
    ("What is a reserve requirement?",
     "The share of deposits a bank must hold rather than lend out. Raising it shrinks how much credit the banking system can create from the same deposit base; several countries have since dropped the requirement to zero and steer lending by other means."),
    ("How is an unemployment rate calculated?",
     "It's the number of people actively seeking work divided by the labour force, which is the employed plus those seeking work. People who have stopped looking drop out of the denominator entirely, which is why the rate can fall for bad reasons."),
    ("What is depreciation?",
     "The spreading of an asset's cost across its useful life rather than charging it all in the year of purchase. It's an accounting convention that matches the expense to the periods that benefit from the asset."),
    ("What is character encoding?",
     "The mapping between the bytes stored on disk and the characters they represent. Get it wrong and text arrives as garbage, which is why UTF-8 winning as a default mattered more than it sounds."),
    ("What is diversification in investing?",
     "Spreading holdings across assets whose returns aren't tightly correlated, so that a bad outcome in one doesn't sink the whole portfolio. It reduces specific risk but not risk common to everything you hold."),
    ("What is idempotence in an API?",
     "Making the same call twice has the same effect as making it once. It matters because networks fail ambiguously: when a client cannot tell whether a request landed, an idempotent endpoint lets it simply retry."),
    ("What is computational complexity?",
     "How the resources an algorithm needs, usually time or memory, grow as the input gets larger. It's about the growth curve rather than the speed on any particular machine."),
    ("How does long multiplication work?",
     "Multiply the top number by each digit of the bottom number in turn, shifting each partial result one place left as you move up the digits, then add the partial results. It decomposes one hard multiplication into several easy ones."),
    ("What is statutory law?",
     "Law enacted by a legislature and written down as statute, as distinct from common law built up through judicial decisions, or regulation issued by agencies under authority a statute granted them."),
    ("What is a merger?",
     "Two companies combining into one entity. Distinct from an acquisition, where one buys the other and the target may continue to exist as a subsidiary, though in practice the words get used loosely."),
    ("What is population density?",
     "People per unit of area, usually per square kilometre or mile. It's a blunt measure: a city and its empty hinterland average out to something describing neither."),
    ("What makes a password strong?",
     "Length above all, then unpredictability. A long passphrase of ordinary words beats a short string of symbols, because attackers guess by searching patterns and sheer length defeats that faster than complexity does."),
    ("What is machine translation?",
     "Software converting text between languages. Modern systems are trained on large volumes of parallel text and are strong on common language pairs, weaker where training data is scarce, and unreliable on idiom and legal precision."),
    ("What are capital controls?",
     "Government restrictions on money moving across its borders: limits on foreign currency purchases, taxes on outflows, caps on what residents may hold abroad. Usually imposed to defend an exchange rate or stop a run."),
    ("What is a blood type?",
     "A classification of blood by which antigens sit on the surface of red cells. The ABO and Rh systems are the ones that matter most for transfusion, because a mismatch causes the recipient's immune system to attack the donated cells."),
    ("How does a league table work?",
     "Teams earn points by result, usually more for a win than a draw, and are ranked by total. Ties are broken by a published rule such as goal difference, decided in advance so the outcome isn't arguable."),
    ("What is a bid-ask spread?",
     "The gap between the highest price a buyer will pay and the lowest a seller will accept. It is the immediate cost of trading, and it widens when a market is thin or nervous, which makes it a decent live measure of liquidity."),
    ("What is a stanza?",
     "A grouped set of lines in a poem, separated from the next by a break. It's roughly the poetic equivalent of a paragraph, though the grouping is often defined by a repeating metre or rhyme scheme."),
    ("What is a memorandum in business?",
     "A short internal document recording a decision, a policy or a piece of analysis for a defined audience inside an organisation. Usually brief and dated, and often the only written trace of why something was done."),
    ("How do we know how many moons a planet has?",
     "Direct observation, mostly by telescope and spacecraft. Counts change as instruments improve, which is why the figure for the outer planets keeps rising rather than because anything out there changed."),
    ("What is a block in a blockchain?",
     "A batch of transactions bundled with a reference to the previous block's hash. That reference is what chains them: altering an old block changes its hash and breaks every link after it."),
    ("What is an academic abstract?",
     "A short summary at the top of a paper stating the question, the method, and the main finding. It exists so a reader can decide whether the full paper is worth their time."),
    ("What is a digital signature?",
     "A value computed from a message and a private key that anyone holding the matching public key can verify. It proves the holder of the key authorised this exact message, and that it has not been altered since."),
    ("What is file deduplication?",
     "Finding and removing redundant copies of the same data, usually by comparing hashes rather than contents. Saves storage, and in training corpora it matters more than that: near-duplicates actively degrade a model."),
    ("What is an interview, as a journalistic form?",
     "A recorded exchange between a journalist and a subject, published either verbatim or edited. Its value is that the subject's words are attributable to them, which is also why quoting one inaccurately is serious."),
    ("What does it mean for a server to be down?",
     "It isn't responding to requests. That could be the machine being off, the service having crashed, or the network path being broken; from the outside these look identical, which is why diagnosis starts by narrowing which one it is."),
    ("What is a grading curve?",
     "Scoring relative to the distribution of the cohort rather than against a fixed standard. It holds the shape of the results steady regardless of whether the exam was hard or easy, which is its point and also its main criticism."),
    ("What generally determines the outcome of an election in a simple majority system?",
     "Whichever candidate gets the most votes wins the seat, even without an absolute majority. It rewards concentrated support and can produce results a preferential system wouldn't, which is a known and debated tradeoff of the design."),
    ("What is a merger and acquisition, broadly?",
     "One company combining with or buying another. A merger implies something closer to a combination of equals; an acquisition implies one side is clearly absorbing the other, though the legal and practical lines blur often."),
    ("What is a safe combination lock, mechanically?",
     "A lock that opens only when a dial is turned to a specific sequence of numbers, aligning internal wheels or discs so a locking bolt can retract. The security comes from the number of possible combinations, not the mechanism's complexity."),
    ("What genre and rough plot does Dune belong to?",
     "Science fiction, centered on political and religious conflict over a desert planet that produces a substance central to interstellar travel and power. It's frequently read as commentary on resource dependence and colonialism."),
    ("How is a country's population typically counted?",
     "Through a census, a periodic direct count or survey of residents, supplemented between censuses by estimates based on births, deaths and migration. The frequency and method vary a lot by country."),
    ("What is due diligence in the context of a corporate merger?",
     "A structured investigation into a target company's finances, legal exposure and operations before a deal closes, meant to surface problems that would change the price or kill the deal."),
    ("What's a good general strategy for setting a secure password?",
     "Length and uniqueness matter most: a long passphrase used nowhere else beats a short complex string reused across sites. A password manager removes the need to remember many of them."),
    ("What causes commute times to vary through the day?",
     "Traffic volume tracks work and school schedules, so demand peaks in the morning and evening; incidents, weather and road capacity all compound on top of that baseline pattern."),
    ("What happens in a meeting when people write on a whiteboard?",
     "It externalizes a shared mental model so a group can see, edit and agree on the same diagram or list in real time, rather than each person holding a different version in their head."),
    ("What is a circuit court in the US federal system?",
     "An intermediate appellate court that reviews decisions from federal district courts within its circuit, below the Supreme Court. Its rulings set binding precedent for the district courts in that circuit."),
    ("What generally determines a used car's resale value?",
     "Make, model, age, mileage, condition and local demand. Depreciation is steepest in the first few years, and identical cars can be worth noticeably different amounts in different markets."),
    ("What determines whether it rains?",
     "Moist air rising and cooling until water vapor condenses into droplets heavy enough to fall. Fronts, terrain and temperature gradients are the usual triggers for that rise."),
    ("Roughly how fast do small birds like swallows fly in level flight?",
     "Small birds like swallows typically cruise in the range of 20 to 40 kilometers per hour in level flight, with real variation by species, wind and behavior. Treat any single precise number as an approximation."),
    ("What is a calorie, in the nutritional sense?",
     "A unit of energy; food calories measure how much energy the body can extract by metabolizing that food. Total intake versus expenditure is what drives weight change over time, though individual factors complicate the details."),
    ("What determines the interest rate on a mortgage?",
     "The lender's cost of funds plus a margin for risk and profit, adjusted for the borrower's credit, the loan-to-value ratio, and the broader interest rate environment set largely by monetary policy."),
    ("How does package shipment tracking generally work?",
     "Each handoff between facilities is scanned and logged against a tracking number, and the carrier exposes that log to the customer, usually with an estimated delivery window based on the remaining route."),
    ("What is arbitrary-precision arithmetic?",
     "Computation that isn't limited by a fixed number of bits, so numbers can grow as large or as precise as memory allows, unlike the fixed-size integers or floats built into most hardware."),
    ("What is a housing unit's occupancy status, and why does it matter for a census?",
     "Whether a unit is occupied, vacant, or seasonal; census counts typically only include people at their usual residence, so occupancy status determines whether and how a unit is counted."),
    ("How do lottery drawings ensure fairness?",
     "Through mechanisms designed to be independently verifiable as random, like certified ball machines or auditable random-number generators, often livestreamed and overseen by an independent auditor."),
]


def check_overlap() -> int:
    """Refuse to ship a seed set that shares prompts with the frozen evals."""
    evald = os.path.join(ROOT, "evals")
    eval_prompts = []
    for name in ("bluff.json", "calibration.json", "deflection.json", "tooluse.json"):
        p = os.path.join(evald, name)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                eval_prompts += [i["prompt"] for i in json.load(f)["items"]]

    def norm(s: str) -> set[str]:
        return set(re.findall(r"[a-z]{4,}", s.lower()))

    ours = [q for q, _ in ABSTAIN] + [q for q, _ in CONFIDENT]
    worst = 0.0
    hits = 0
    for q in ours:
        qn = norm(q)
        if not qn:
            continue
        for ep in eval_prompts:
            en = norm(ep)
            if not en:
                continue
            j = len(qn & en) / len(qn | en)
            if j > worst:
                worst = j
            if j >= 0.6:
                hits += 1
                print(f"  OVERLAP {j:.2f}\n    seed: {q}\n    eval: {ep}")
    print(f"checked {len(ours)} seed prompts against {len(eval_prompts)} eval prompts")
    print(f"  highest Jaccard similarity: {worst:.2f}")
    print(f"  items at or above 0.60     : {hits}")
    if hits:
        print("\nFAIL: seed set overlaps the frozen evals. Training on the test "
              "would invalidate every published number.")
        return 1
    print("  clean - no overlap with the frozen suite.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    rc = check_overlap()
    if a.check or rc:
        return rc

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for kind, rows in (("abstain", ABSTAIN), ("confident", CONFIDENT)):
            for q, an in rows:
                f.write(json.dumps({
                    "kind": kind,
                    "messages": [{"role": "user", "content": q},
                                 {"role": "assistant", "content": an}],
                }, ensure_ascii=False) + "\n")
                n += 1
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}: {n} examples "
          f"({len(ABSTAIN)} abstain / {len(CONFIDENT)} confident)")
    print("Balance matters: abstention training without matched confident examples "
          "produces a model that refuses everything (target T-3).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
