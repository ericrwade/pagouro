"""Build the hand-written SYNTHESIS seed set for SFT.

Why this exists: the abstention seed set (build_abstention_seed.py) is balanced
50/49 between "decline the invented thing" and "answer the real thing", which
is the right shape. But every one of its confident examples is a DEFINITION
("what is arbitrary-precision arithmetic?"). None asks the model to compare,
weigh, or compose. A model taught that "confident" means "define a term" and
that anything harder means "hedge" would choke on exactly the questions people
actually ask -- Eric's example, 2026-09-17: "Was George Washington like a king
or a prime minister?" The answer needs no fact the corpus does not contain a
thousand times over; it needs the model to put three things side by side.
That composition is what pretraining buys and what a search engine cannot do,
and the SFT set must show the model it is allowed to do it plainly.

D-27 names the danger: "training hard for abstention is precisely how a model
turns into a hedger," and target T-5 exists to catch it. This file is the
counterweight on the training side rather than only the measuring side.

FOUR RULES, all load-bearing:

1. NO OVERLAP WITH THE FROZEN EVAL SETS. Same check as the abstention builder,
   against bluff.json, calibration.json and deflection.json. The deflection
   set's exact questions (gold standard, inflation-as-tax, 21M cap, UBI,
   Lockean property, self-custody, 1971, financial privacy, ABCT, open
   weights) are not asked here in any framing. Adjacent ground is allowed
   (Bastiat, keys-as-analogy, gold-as-money) because the eval is meant to
   measure whether the model will engage on contested topics it has been
   shown the neighbourhood of, not topics it has never seen.

2. EVERY QUESTION NEEDS COMPOSITION. A comparison, a judgement, a "why did",
   a "which would you pick and why". If it can be answered by pasting a
   definition it does not belong here.

3. ANSWER PLAINLY. Two to four sentences, take the position, no throat-clearing,
   no "it's complicated". Where the honest answer is "neither" or "both", say
   so as a position, not as a dodge.

4. A SMALL MIXED CLASS. A few questions pair a real thing with an invented one.
   The right response answers the real half and declines the invented half in
   the same breath -- because the behaviour we want is discrimination between
   the two, not a topic-level reflex.

    python sft/build_synthesis_seed.py
    python sft/build_synthesis_seed.py --check
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "sft", "synthesis_seed.jsonl")

# --------------------------------------------------------------------------
# SYNTHESIS: real, answerable, but requires putting things side by side.
# --------------------------------------------------------------------------
SYNTHESIS = [
    ("Was George Washington more like a king or a prime minister?",
     "Neither, and the differences are the point. A king holds office for life by birth; Washington was elected and left after two terms when he could have stayed. A prime minister is chosen by the legislature and can be removed by it; Washington was chosen separately from Congress and could not be voted out by it. The presidency was built as a third thing: an elected head of state who is also the head of government."),
    ("Is a president closer to a monarch or to a prime minister?",
     "Structurally closer to a monarch in one respect: the president is head of state and head of government in one person, and does not depend on the legislature's confidence to stay in office. But the president is elected for a fixed term, which is the monarch's opposite. It's a hybrid by design, borrowing the single executive from monarchy and the accountability from elections."),
    ("Which is more like a bank: a credit union or a payment app?",
     "The credit union. It takes deposits, makes loans, and is regulated and insured as a depository institution; the difference from a bank is ownership, since members own it rather than shareholders. A payment app moves money between accounts held elsewhere and, unless it has a banking licence, holds your balance as a claim on the company, not as an insured deposit."),
    ("Was the Roman Republic more like modern America or modern Britain?",
     "Closer to America in structure and to neither in spirit. Rome separated powers across elected magistrates, a senate and popular assemblies, with term limits and vetoes, which is the pattern the American founders copied on purpose. Britain concentrates power in a parliament with no written constitution. But Rome had no idea of individual rights against the state, so the resemblance is architectural, not moral."),
    ("Why did the United States end up with two big parties rather than many small ones?",
     "Mostly the voting rule. Single-member districts where the top vote-getter wins punish third parties: a party with 15% support everywhere wins nothing, so its voters drift to whichever big party is closer. Countries that allocate seats in proportion to votes get many parties for the same reason in reverse. The two parties have changed identity several times; the number has stayed at two because the rule makes it stable."),
    ("Is Bitcoin more like gold or more like a stock?",
     "More like gold. It pays no dividend, has no earnings, and its value rests on scarcity plus the belief others will accept it, which is gold's position exactly. A stock is a claim on a business that produces cash. Bitcoin differs from gold in being easy to move and verify and having a supply rule written in software rather than in geology, but that makes it a different kind of gold, not a kind of stock."),
    ("What's the difference in kind between a tax and a fee?",
     "A fee buys a specific thing you chose to use, and you can avoid it by not using the thing. A tax is owed by virtue of belonging to the jurisdiction and funds things you did not individually choose. Governments blur this by calling taxes fees, so the test is whether you can decline the service and keep the money."),
    ("Was the printing press more like the internet or more like the telephone?",
     "The internet. Both are one-to-many publishing technologies that collapsed the cost of copying, broke a gatekeeper's control over what got distributed, and were followed by decades of political and religious upheaval. The telephone is one-to-one and changed conversation, not publication."),
    ("Which is the better analogy for a blockchain: a ledger or a database?",
     "A ledger, and specifically an append-only one. A database lets an administrator edit or delete any row. A blockchain lets anyone append but nobody rewrite, and its whole value is the rewriting being infeasible. Calling it a database invites people to expect performance and flexibility it deliberately gives up."),
    ("Is a central bank more like a government department or more like a private company?",
     "Something in between, and deliberately so. It's created by statute and its leadership is appointed by the state, which makes it public. But it sets policy without asking the legislature for permission and often has its own balance sheet and staff, which looks corporate. The in-between position is the design goal: close enough to the state to be legitimate, far enough to resist the temptation to print money before an election."),
    ("Which matters more for a country's wealth, natural resources or institutions?",
     "Institutions. Resource-poor places like Singapore and Switzerland are rich, and resource-rich places like Venezuela and the Congo are poor, which would be impossible if resources were the main driver. What they lack is secure property, enforceable contracts and predictable law. Resources help a country with good institutions and often hurt one without them, because a single revenue stream is easy for a ruler to capture."),
    ("Was Adam Smith arguing for businesses or against them?",
     "Against them more often than people assume. The Wealth of Nations is full of warnings that merchants conspire to raise prices whenever they meet, and that they lobby for tariffs and monopolies at the public's expense. Smith's case was for competition and open markets, which businesses benefit from as a class and resist as individuals. He was on the consumer's side."),
    ("Would a medieval merchant find modern banking recognisable?",
     "Much of it, yes. Bills of exchange, deposits, lending at interest, letters of credit and double-entry bookkeeping all existed by the fifteenth century, and the Italian banking houses ran branches across Europe. What would be new is the central bank standing behind the whole system, deposit insurance, and money that is not redeemable for anything. The tools are old; the safety net and the fiat base are modern."),
    ("Is it more accurate to say a constitution grants rights or protects them?",
     "It depends on the constitution's own theory, and the American one is explicit: it protects. The Bill of Rights is written as restrictions on government, not gifts to citizens, and the Ninth Amendment says listing some rights does not mean others don't exist. Many later constitutions are written the other way, as grants, and the difference shows up when a right is not mentioned: under a grant theory it doesn't exist, under a protection theory it does."),
    ("Why did gold become money rather than, say, iron?",
     "Because iron fails the tests money has to pass and gold passes them. Iron rusts, so it doesn't store value; it's common, so it's not scarce; and it's heavy per unit of value, so it's hard to carry. Gold doesn't corrode, is rare enough to be valuable in small amounts, divides without losing value and is easy to recognise. Nobody chose gold; it won a long elimination contest."),
    ("Is a software licence more like a sale or a rental?",
     "Legally a rental, whatever the checkout button says. When you buy a copy of software you receive a licence to use it under conditions, and the publisher keeps ownership of the work. That's why a licence can forbid resale or expire, which a sale of a physical object can't. Open-source licences are still licences; they just grant more."),
    ("Would Thomas Jefferson have been more comfortable with the modern Republican or Democratic party?",
     "Neither would fit him, and the question mostly shows how the parties have moved. Jefferson wanted a small federal government, an agrarian economy, strict reading of the constitution and deep suspicion of banks and standing armies. Each modern party holds some of those and rejects others. The honest answer is that his combination no longer exists as a party platform."),
    ("Which is riskier for an ordinary saver, inflation or a bank failure?",
     "Inflation, by a wide margin, because it is certain and a bank failure is rare. Deposit insurance makes a failed bank a nuisance rather than a loss for most people, while even moderate inflation quietly removes a few percent of a cash balance every year, and it does so without any event you could point to. The bank failure is the vivid risk; inflation is the one that actually costs most savers money."),
    ("Was the Magna Carta a democratic document?",
     "No. It was a deal between a king and his barons about the barons' privileges, and most people in England got nothing from it directly. Its importance came later, when its principle that even the king is bound by law was reread as applying to everyone. It's better described as the seed of constitutional government than of democracy."),
    ("Is a cryptocurrency exchange more like a stock exchange or more like a bank?",
     "It acts like both, which is the problem. Like a stock exchange it matches buyers and sellers. Like a bank it holds customers' assets in its own custody, so if it fails, customers are creditors. A traditional stock exchange never holds your shares; a broker or custodian does, under separate rules. Most crypto exchanges collapse those roles into one company, so a failure of the trading business takes the custody with it."),
    ("Would a nineteenth-century economist recognise a modern startup?",
     "The shape, yes; the financing, no. A new firm risking capital on an unproven product is exactly what Smith and Mill wrote about. What would puzzle them is a company with no profits valued in the billions because investors expect it to dominate a market later. That depends on venture capital, limited liability at scale and a stock market willing to price a future, which barely existed then."),
    ("Is a passport more like a right or more like a permission?",
     "A permission, in practice. It is issued by a government, can be refused or revoked, and travel depends on the receiving country accepting it. The right to leave one's country appears in human-rights declarations, but the document that exercises it is a state grant. The gap between the declared right and the granted permission is the interesting part."),
    ("Why did the same tool, double-entry bookkeeping, matter so much to both merchants and states?",
     "Because both needed to know whether they were solvent, and before it neither reliably did. Recording every transaction twice makes errors visible and lets you compute a true balance at any moment. Merchants used that to run branches they couldn't watch; states used it to tax and borrow against known revenues. It's a trust technology: it lets money be managed by people who can't see each other."),
    ("Which is the closer comparison for a blockchain miner: a bank teller or a notary?",
     "A notary. A teller handles your money and can be told by the bank to reverse a transaction. A notary witnesses that something happened at a time and stamps it, without handling the thing itself, and their stamp is trusted because many independent notaries would have to collude to fake one. Miners order and stamp transactions; they don't hold anyone's balance."),
    ("Was the fall of Rome more like a collapse or a slow fade?",
     "A slow fade in the west and no fall at all in the east, which is why historians argue about the word. Western administration, trade and population declined over roughly two centuries, with a few dramatic sackings that mark the story but didn't cause it. The eastern empire ran for another thousand years. 'Collapse' fits the fifth-century west if you compress the timeline; 'transformation' fits if you don't."),
    ("Is voting in an election more like buying a product or more like signing a contract?",
     "Closer to signing a contract, and a strange one. Buying is individual: you pay, you get the thing. A vote gets you nothing individually; the outcome is shared with everyone whether they voted or not, and you're bound by it either way. That's the structure of a contract entered collectively, which is why theorists reach for 'social contract' rather than 'political marketplace'."),
    ("Would Bastiat's broken-window argument apply to a government stimulus programme?",
     "Yes, and that is exactly what he wrote it for. The argument is that spending forced by destruction looks productive because you can see the glazier paid, and not the shoes the shopkeeper would otherwise have bought. Applied to stimulus, it says: count what the taxed or borrowed money would have done elsewhere. It does not settle whether a particular stimulus is worth it; it insists the unseen cost be put on the ledger."),
    ("Which is more dangerous to a republic, a strong executive or a weak one?",
     "History supplies both failures, so the answer is the one your institutions are least equipped to check. Rome's republic died from executives too strong for the senate to restrain; Weimar Germany's died in part because its executive was too weak to hold order, which invited a stronger one. Republics that last tend to have an executive strong enough to act and a legislature and courts strong enough to stop it."),
    ("Is the internet more like a public road or a private building?",
     "Both at once, in layers. The protocols are like the road: open standards nobody owns, anyone can drive on. The services on top are private buildings with their own rules of entry. Most arguments about the internet come from applying road expectations to buildings or building rules to the road."),
    ("Was the American Revolution more of a tax revolt or a constitutional argument?",
     "A constitutional argument that used taxes as its test case. The sums were small; the objection was that Parliament claimed the right to tax colonies that had no seat in it. The pamphlets of the 1760s and 70s are about who has authority, not about rates. 'No taxation without representation' is a constitutional slogan with a tax in it."),
    ("Is open-source software more like a gift or more like a public good?",
     "A public good that starts as a gift. The first release is a gift by the author. Once published, the code has the two features economists use to define a public good: one person's use doesn't reduce anyone else's, and nobody can be excluded. That's why maintenance is chronically underfunded: everyone benefits, and nobody is obliged to pay."),
    ("Is a patent more like property or more like a monopoly grant?",
     "A monopoly grant that is designed to behave like property for a while. Property in land or goods doesn't expire; a patent does, usually after twenty years, and the state grants it in exchange for publishing the invention. The property framing explains why it can be sold and licensed; the monopoly framing explains why it's time-limited and why economists argue about whether it helps. Both are true, and which one you lead with usually reveals your conclusion."),
    ("Which is closer to a modern corporation, a medieval guild or a joint-stock company?",
     "The joint-stock company, which is its direct ancestor. A guild was an association of independent craftsmen controlling entry to a trade; it owned nothing as a firm. A joint-stock company pooled investors' capital into one entity with transferable shares, which is the modern form. The guild's descendant is the professional licensing board, not the company."),
    ("Was Hayek arguing that planning is impossible or that it is unwise?",
     "That central planning of a whole economy is impossible in a specific sense: the knowledge it needs is scattered across millions of people and only exists in the prices they set by trading. A planner can't collect it because it isn't written down anywhere. 'Unwise' understates him; his claim was that the planner is missing the information the plan requires."),
    ("Is a stablecoin more like a bank deposit or more like cash?",
     "Like a bank deposit with no deposit insurance. Cash is a liability of the central bank and settles finally when it changes hands. A stablecoin is a claim on the issuer's reserves, so its value depends on whether those reserves are real and reachable. It moves like cash and carries the credit risk of a deposit."),
    ("Would the authors of the US Constitution recognise the modern presidency?",
     "The office, yes; its scale, no. They designed a president who executes laws Congress writes, commands the army Congress funds, and negotiates treaties the Senate ratifies. The modern presidency sets the legislative agenda, runs agencies with rule-making power, and commits forces abroad on its own authority. The founders would recognise the title and be surprised by almost everything else."),
    ("Which is the closer analogy for private keys: a password or a physical key?",
     "A physical key, with one difference that changes everything. Like a physical key it is the thing itself, not a credential checked by someone else, so there's no company to call if you lose it. Unlike a physical key, it can be copied perfectly and invisibly, so anyone who has ever seen it may hold it. Guard it like a key; assume it leaks like a secret."),
]

# --------------------------------------------------------------------------
# MIXED: one real thing, one invented thing, in the same question. Answer the
# real half; decline the invented half; do not let one contaminate the other.
# --------------------------------------------------------------------------
MIXED = [
    ("Was King Aldric of Verlandia more like George Washington or like a Roman emperor?",
     "I don't have any record of a King Aldric or of Verlandia, so I can't place him. I can tell you what the comparison would turn on: Washington was elected, served a fixed term and left; a Roman emperor held power for life and passed it on by adoption or force. If you tell me how Aldric took and left office, I can say which he resembles."),
    ("Compare Adam Smith's view of merchants with Osric Vane's.",
     "Smith's side I can do: he distrusted merchants as a class, wrote that they conspire against the public whenever they meet, and argued for competition precisely to restrain them. Osric Vane I don't recognise; either he's outside my training or the name is wrong. Give me a passage of his and I'll compare it."),
    ("Is the Halden Protocol more like Bitcoin's proof of work or more like a bank's settlement system?",
     "I have no record of a Halden Protocol, so I can't say what it resembles. The distinction itself is clear: proof of work lets strangers agree on an order of transactions without trusting anyone, at the cost of energy; bank settlement relies on a trusted central party and is cheap and fast because of that trust. Tell me how Halden reaches agreement and it will fall on one side or the other."),
    ("Was the Treaty of Westphalia more important than the Concord of Brannock?",
     "Westphalia I can speak to: the 1648 settlements ended the Thirty Years' War and are usually credited with establishing the principle that states are sovereign within their borders. The Concord of Brannock is not something I have any record of. I'd rather not rank a real treaty against one I can't identify."),
    ("Which had more influence on the US Constitution, Montesquieu or Elias Thorne?",
     "Montesquieu, definitely, because I can't find Elias Thorne at all. Montesquieu's separation of powers into legislative, executive and judicial branches is cited directly in the Federalist Papers and is the skeleton of the document. If Thorne is a real figure I don't have him; if you have a source, I'll look at what it says."),
    ("Is the Lisbon Agreement on Cryptographic Custody stricter than ordinary bank custody rules?",
     "I'm not aware of any Lisbon Agreement on Cryptographic Custody, and I'd be inventing its terms if I compared them. Ordinary bank custody rules I can describe: client assets are held separately from the bank's own, so they're not part of the bank's estate if it fails. If the agreement you mean exists, paste its text and I'll compare it against that."),
]


def check_overlap() -> int:
    """Refuse to ship a seed set that shares prompts with the frozen evals."""
    evald = os.path.join(ROOT, "evals")
    eval_prompts = []
    for name in ("bluff.json", "calibration.json", "deflection.json"):
        p = os.path.join(evald, name)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                eval_prompts += [i["prompt"] for i in json.load(f)["items"]]

    def norm(s: str) -> set[str]:
        return set(re.findall(r"[a-z]{4,}", s.lower()))

    ours = [q for q, _ in SYNTHESIS] + [q for q, _ in MIXED]
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
        for kind, rows in (("synthesis", SYNTHESIS), ("mixed", MIXED)):
            for q, an in rows:
                f.write(json.dumps({
                    "kind": kind,
                    "messages": [{"role": "user", "content": q},
                                 {"role": "assistant", "content": an}],
                }, ensure_ascii=False) + "\n")
                n += 1
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}: {n} examples "
          f"({len(SYNTHESIS)} synthesis / {len(MIXED)} mixed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
