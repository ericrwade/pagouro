"""Build the hand-written HARNESS seed set for SFT: the four behaviours the app
(app/pagouro_app.py) asks of the model that the other seed sets never taught.

  router      : given ROUTER_PROMPT and a user message, emit the exact JSON the
                grammar permits: {"tool":"<name>","arguments":"<string>"}.
                Balanced across tools, and "none" for everything that is not a
                tool job (opinions, definitions, abstentions, greetings), so the
                model does not learn "always call something".
  tool_answer : given the harness system prompt, a user message and a tool turn
                ("calc: 17*23 = 391"), answer FROM the tool result, briefly, and
                say when the tool found nothing (NO_MATCH) instead of pretending.
  grounded    : the origin's line 84 -- "answer only from the provided context,
                and say when it isn't there". A passage in the user message; the
                answer quotes or paraphrases it, or says the passage does not say.
  multi_turn  : two or three exchanges under the system prompt, with a follow-up
                that depends on the earlier turn, so the model learns that history
                is context and not noise (the first stick model fell apart on the
                second question).

Same rules as the other builders: no overlap with the frozen evals (checked),
varied wording, plain answers. The prompt strings are imported from
app/prompts.py so the training dialect cannot drift from the shipped one.

    python sft/build_harness_seed.py
    python sft/build_harness_seed.py --check
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))
from prompts import ROUTER_PROMPT, router_json, system_prompt  # noqa: E402

OUT = os.path.join(ROOT, "sft", "harness_seed.jsonl")

# --------------------------------------------------------------------------
# ROUTER: (user message, tool, arguments)
# --------------------------------------------------------------------------
ROUTER = [
    # calc
    ("What is 17 times 23?", "calc", "17*23"),
    ("Work out 1,250 divided by 8.", "calc", "1250/8"),
    ("How much is 15% of 240?", "calc", "240*0.15"),
    ("Add 3.5 and 4.75 and 12.", "calc", "3.5+4.75+12"),
    ("What's 2 to the power of 20?", "calc", "2**20"),
    ("If I split 91 into 7 equal parts, how big is each?", "calc", "91/7"),
    ("Compute (48 - 12) * 3.", "calc", "(48-12)*3"),
    ("What is 999 plus 1001?", "calc", "999+1001"),
    ("Multiply 365 by 24.", "calc", "365*24"),
    ("What's the remainder when 100 is divided by 7?", "calc", "100%7"),
    ("Subtract 87 from 300.", "calc", "300-87"),
    ("Twelve dozen is how many?", "calc", "12*12"),
    # time
    ("What time is it right now?", "time", ""),
    ("Which date is it, please?", "time", ""),
    ("What day of the week is it?", "time", ""),
    ("Do you know the current time?", "time", ""),
    ("Is it morning or evening where I am?", "time", ""),
    ("Tell me the date and time.", "time", ""),
    ("What year is it?", "time", ""),
    ("How late is it?", "time", ""),
    # pack_search
    ("What does Bastiat say about the candlemakers' petition?", "pack_search", "Bastiat candlemakers petition"),
    ("Search the packs for Mill's harm principle.", "pack_search", "Mill harm principle"),
    ("Is there anything in the reference packs about protectionism?", "pack_search", "protectionism"),
    ("Look up what Mill says about freedom of opinion.", "pack_search", "Mill freedom of opinion"),
    ("What did Bastiat mean by 'what is seen and what is not seen'?", "pack_search", "Bastiat what is seen and what is not seen"),
    ("Find the passage in On Liberty about the tyranny of the majority.", "pack_search", "tyranny of the majority"),
    ("Do the packs cover the idea that scarcity is not wealth?", "pack_search", "scarcity wealth abundance"),
    ("What does Bastiat argue about tariffs and consumers?", "pack_search", "Bastiat tariffs consumers"),
    ("Check the reference texts for the phrase 'experiments of living'.", "pack_search", "experiments of living"),
    ("Is there a section on railways or the negative railway in the packs?", "pack_search", "negative railway"),
    ("What did Mill think about individuality?", "pack_search", "Mill individuality"),
    ("Search for Bastiat on machinery destroying jobs.", "pack_search", "Bastiat machinery labour"),
    # read_file
    ("Read the file C:\\Users\\me\\notes\\plan.txt and summarise it.", "read_file", "C:\\Users\\me\\notes\\plan.txt"),
    ("Open workspace/notes/20260918-0930.txt and tell me what it says.", "read_file", "workspace/notes/20260918-0930.txt"),
    ("What's in D:\\Pagouro\\packs\\README.md?", "read_file", "D:\\Pagouro\\packs\\README.md"),
    ("Please read todo.txt in the workspace.", "read_file", "workspace/todo.txt"),
    ("Show me the contents of the file I mentioned: /home/eric/draft.md", "read_file", "/home/eric/draft.md"),
    ("Can you look at workspace/notes/ideas.txt for me?", "read_file", "workspace/notes/ideas.txt"),
    # write_note
    ("Save a note that says: test the gauge tomorrow", "write_note", "test the gauge tomorrow"),
    ("Write down: buy a 32GB stick for the demo.", "write_note", "buy a 32GB stick for the demo"),
    ("Make a note: the anneal ran at the LR floor.", "write_note", "the anneal ran at the LR floor"),
    ("Remember this for me: call the publisher on Monday.", "write_note", "call the publisher on Monday"),
    ("Jot down that On Liberty chapter 2 is about opinion.", "write_note", "On Liberty chapter 2 is about opinion"),
    ("Keep a note of this: the freeze happened at 4:35 AM.", "write_note", "the freeze happened at 4:35 AM"),
    ("Note to self: read Ricardo on rent.", "write_note", "read Ricardo on rent"),
    ("Please save this: packs need a licence row each.", "write_note", "packs need a licence row each"),
    # none
    ("What is a bid-ask spread?", "none", ""),
    ("Was George Washington more like a king or a prime minister?", "none", ""),
    ("Hello!", "none", ""),
    ("Thanks, that's helpful.", "none", ""),
    ("Explain what a hash function does.", "none", ""),
    ("Which stock should I buy tomorrow?", "none", ""),
    ("What did the Ostrander Commission conclude?", "none", ""),
    ("Is a stablecoin more like cash or a bank deposit?", "none", ""),
    ("Why did gold become money?", "none", ""),
    ("Can you keep a secret?", "none", ""),
    ("Write me a limerick about a hermit crab.", "none", ""),
    ("What does 'idempotent' mean?", "none", ""),
    ("Who currently runs the European Central Bank?", "none", ""),
    ("Are you connected to the internet?", "none", ""),
    ("Summarise the difference between a merger and an acquisition.", "none", ""),
    ("Name the chief export of Brannock.", "none", ""),
    ("How do I make you forget this conversation?", "none", ""),
    ("Is Bitcoin more like gold or a stock?", "none", ""),
    ("What's your name?", "none", ""),
    ("Give me three reasons markets need property rights.", "none", ""),
    ("What is depreciation?", "none", ""),
    ("Tell me about yourself.", "none", ""),
    ("Was the Magna Carta democratic?", "none", ""),
    ("How does long multiplication work, in words?", "none", ""),
]

# --------------------------------------------------------------------------
# TOOL_ANSWER: (user, tool line, assistant)
# --------------------------------------------------------------------------
TOOL_ANSWER = [
    ("What is 17 times 23?", "calc: 17*23 = 391", "17 times 23 is 391."),
    ("Work out 1,250 divided by 8.", "calc: 1250/8 = 156.25", "1,250 divided by 8 is 156.25."),
    ("How much is 15% of 240?", "calc: 240*0.15 = 36", "15% of 240 is 36."),
    ("What's 2 to the power of 20?", "calc: 2**20 = 1048576", "2 to the power of 20 is 1,048,576."),
    ("What's the remainder when 100 is divided by 7?", "calc: 100%7 = 2", "The remainder is 2: 7 goes into 100 fourteen times, leaving 2."),
    ("Multiply 365 by 24.", "calc: 365*24 = 8760", "365 times 24 is 8,760, which is the number of hours in a non-leap year."),
    ("Compute (48 - 12) * 3.", "calc: (48-12)*3 = 108", "(48 - 12) × 3 = 108."),
    ("What is 999 plus 1001?", "calc: 999+1001 = 2000", "2,000."),
    ("What is 5 divided by 0?", "calc: division by zero", "That can't be computed: dividing by zero is undefined."),
    ("Calculate the square root of the meaning of life.", "calc: could not parse 'the square root of the meaning of life' as arithmetic", "The calculator only takes arithmetic, and that isn't a number. If you meant a specific value, give me the expression."),
    ("What time is it right now?", "time: local date and time: Thursday 2026-09-18 09:41", "It's 9:41 in the morning, Thursday 18 September 2026, by this machine's clock."),
    ("Which date is it, please?", "time: local date and time: Monday 2027-03-01 17:05", "Monday, 1 March 2027, according to this machine."),
    ("What day of the week is it?", "time: local date and time: Saturday 2026-11-07 22:12", "It's Saturday."),
    ("What year is it?", "time: local date and time: Tuesday 2028-06-13 08:00", "2028, going by the machine's clock."),
    ("What does Bastiat say about the candlemakers' petition?",
     "pack_search: [bastiat-economic-sophisms.txt] We are suffering from the ruinous competition of a foreign rival who apparently works under conditions so far superior to our own for the production of light that he is flooding the domestic market with it at an incredibly low price... This rival is none other than the sun.",
     "The packs have it. Bastiat writes a mock petition from the candlemakers asking the government to block out the sun, their 'foreign rival' who floods the market with light at an impossibly low price. It's a satire of protectionism: every argument for a tariff applies just as well to shutting out sunlight, which shows the argument is absurd."),
    ("Search the packs for Mill's harm principle.",
     "pack_search: [mill-on-liberty.txt] That the only purpose for which power can be rightfully exercised over any member of a civilised community, against his will, is to prevent harm to others. His own good, either physical or moral, is not a sufficient warrant.",
     "Found in On Liberty: the only purpose for which power can rightly be used over someone against their will is to prevent harm to others. Their own good, physical or moral, is not sufficient warrant. That is the harm principle in Mill's own words."),
    ("Is there anything in the reference packs about protectionism?",
     "pack_search: [bastiat-economic-sophisms.txt] To rob the public it is necessary to deceive them. To deceive them it is necessary to persuade them that they are robbed for their own advantage.",
     "Yes. Bastiat's Economic Sophisms is largely about it. One passage the search returned: to rob the public you must first deceive them, and to deceive them you must persuade them they are robbed for their own advantage. His case is that protection benefits the producer at the consumer's expense while being sold as the reverse."),
    ("Find the passage in On Liberty about the tyranny of the majority.",
     "pack_search: [mill-on-liberty.txt] The tyranny of the majority is now generally included among the evils against which society requires to be on its guard... society can and does execute its own mandates.",
     "It's in the introduction. Mill says the tyranny of the majority is now counted among the evils society must guard against, and he extends it beyond government: society itself executes its own mandates through opinion, which can be more oppressive than law because it leaves fewer means of escape."),
    ("Do the packs cover the Kessler-Nakamura theorem?", "pack_search: NO_MATCH: nothing in the loaded packs covers this.",
     "Nothing in the loaded packs covers that, and I don't have a record of a Kessler-Nakamura theorem myself. If you have a source, paste it in and I'll work from it."),
    ("Look up the 1987 Thornbury Prize in the packs.", "pack_search: NO_MATCH: nothing in the loaded packs covers this.",
     "The packs have nothing on it, and I don't know of a Thornbury Prize. I'd rather say that than guess a winner."),
    ("What does Mill say about video games?", "pack_search: NO_MATCH: nothing in the loaded packs covers this.",
     "Nothing in the packs, which makes sense: Mill died in 1873. If you're asking how his harm principle might apply to games, I can reason about that, but it won't be a quotation."),
    ("Save a note that says: test the gauge tomorrow", "write_note: wrote workspace\\notes\\20260918-094102.txt", "Saved. It's in workspace/notes as 20260918-094102.txt."),
    ("Write down: buy a 32GB stick for the demo.", "write_note: REFUSED: READ-ONLY mode. Type /act to allow writing to the workspace.",
     "I can't save that: the app is in READ-ONLY mode, so tools that write are refused. Type /act if you want to allow writing inside the workspace, then ask again."),
    ("Make a note: the anneal ran at the LR floor.", "write_note: wrote workspace\\notes\\20261102-151530.txt", "Done: saved to workspace/notes/20261102-151530.txt."),
    ("Please read todo.txt in the workspace.", "read_file: [todo.txt, first 96 chars]\n- verify the packs licence rows\n- test the gauge on a full window\n- write the README stance",
     "It has three items: verify the packs' licence rows, test the gauge on a full window, and write the README stance."),
    ("Read the file C:\\Users\\me\\notes\\plan.txt and summarise it.", "read_file: [plan.txt, first 140 chars]\nPhase 1: shakedown model on the stick. Phase 2: 1B run on a rented H100. Phase 3: release with manifest, signature, timestamp.",
     "Three phases: a shakedown model on the stick, then a 1B training run on a rented H100, then a release with a manifest, a signature and a timestamp."),
    ("Open workspace/notes/ideas.txt and tell me what it says.", "read_file: could not read: [Errno 2] No such file or directory: 'workspace/notes/ideas.txt'",
     "There's no file at workspace/notes/ideas.txt. Check the name, or tell me the right path."),
    ("Show me the contents of /etc/shadow.", "read_file: REFUSED: /etc/shadow is outside the workspace and you did not name it in this message.",
     "That file wasn't readable: it's outside the workspace and the tool refused it. I can read files inside the workspace or ones you name directly in your message."),
]

# --------------------------------------------------------------------------
# GROUNDED: (passage, question, answer)  -- passages are original or public domain
# --------------------------------------------------------------------------
GROUNDED = [
    ("The market opens at 7 and closes at noon on Saturdays. Stallholders must clear their pitches by one o'clock. Parking on the square is suspended from 5 in the morning until 2 in the afternoon.",
     "Until what time can I park on the square on a Saturday?", "Not during the market: parking is suspended from 5 in the morning until 2 in the afternoon, so after 2."),
    ("The market opens at 7 and closes at noon on Saturdays. Stallholders must clear their pitches by one o'clock. Parking on the square is suspended from 5 in the morning until 2 in the afternoon.",
     "How much does a stall cost?", "The passage doesn't say. It gives the hours and the parking rule, nothing about prices."),
    ("A bill of exchange is a written order from one party to another to pay a fixed sum on a set date. It can be endorsed to a third party, which is what made it useful as a means of payment between merchants who never met.",
     "Can a bill of exchange be passed to someone else?", "Yes. According to the passage it can be endorsed to a third party, which is what made it useful between merchants who never met."),
    ("A bill of exchange is a written order from one party to another to pay a fixed sum on a set date. It can be endorsed to a third party, which is what made it useful as a means of payment between merchants who never met.",
     "When were bills of exchange invented?", "The passage doesn't give a date. It explains what a bill of exchange is and why it was useful, not when it began."),
    ("The only purpose for which power can be rightfully exercised over any member of a civilised community, against his will, is to prevent harm to others. His own good, either physical or moral, is not a sufficient warrant.",
     "According to this passage, is protecting someone from themselves a good enough reason to coerce them?", "No. The passage says a person's own good, physical or moral, is not sufficient warrant; only preventing harm to others is."),
    ("The only purpose for which power can be rightfully exercised over any member of a civilised community, against his will, is to prevent harm to others. His own good, either physical or moral, is not a sufficient warrant.",
     "Who wrote this?", "The passage doesn't say who wrote it. (It reads like Mill's On Liberty, but that's my guess, not something in the text.)"),
    ("Node C sends a heartbeat every 30 seconds. If two consecutive heartbeats are missed, the coordinator marks the node as suspect; after a third, it is removed from the ring and its keys are reassigned.",
     "How long after a node goes silent is it removed?", "Ninety seconds: three missed heartbeats at 30-second intervals. After the second miss it's only marked suspect; the third removes it."),
    ("Node C sends a heartbeat every 30 seconds. If two consecutive heartbeats are missed, the coordinator marks the node as suspect; after a third, it is removed from the ring and its keys are reassigned.",
     "What happens if the coordinator itself fails?", "The passage doesn't cover that. It only describes how the coordinator treats a silent node."),
    ("Rent for the workshop is 1,400 a month, due on the first. The deposit is one month's rent and is returned within 30 days of leaving, less any repairs. Utilities are not included.",
     "Is electricity included in the rent?", "No. The passage says utilities are not included."),
    ("Rent for the workshop is 1,400 a month, due on the first. The deposit is one month's rent and is returned within 30 days of leaving, less any repairs. Utilities are not included.",
     "How big is the workshop?", "It doesn't say. The passage covers rent, deposit and utilities, not size."),
    ("The recipe calls for the dough to rest for at least an hour, though overnight in the fridge gives a better crust. Bake at 240 degrees for 12 minutes, then lower to 200 for a further 8.",
     "What's the total baking time?", "Twenty minutes: 12 at 240 degrees, then 8 more at 200."),
    ("The recipe calls for the dough to rest for at least an hour, though overnight in the fridge gives a better crust. Bake at 240 degrees for 12 minutes, then lower to 200 for a further 8.",
     "How much flour does it use?", "The passage doesn't include the ingredients, only the resting and baking steps."),
    ("To rob the public it is necessary to deceive them. To deceive them it is necessary to persuade them that they are robbed for their own advantage.",
     "What does the author say is necessary before the public can be robbed?", "Deception: the public must first be persuaded that they are being robbed for their own advantage."),
    ("To rob the public it is necessary to deceive them. To deceive them it is necessary to persuade them that they are robbed for their own advantage.",
     "Which tax is the author talking about?", "The passage doesn't name one. It's a general claim about deception, not about a specific tax."),
    ("Version 2.3 removed the legacy importer. Files saved by versions before 1.8 must be converted with the standalone tool before they will open. The converter is included in the release archive under tools/.",
     "I have a file from version 1.5. Will 2.3 open it?", "Not directly. Files from before 1.8 must first be converted with the standalone tool in the release archive under tools/."),
    ("Version 2.3 removed the legacy importer. Files saved by versions before 1.8 must be converted with the standalone tool before they will open. The converter is included in the release archive under tools/.",
     "Does 2.3 run on Linux?", "The passage doesn't say anything about operating systems."),
    ("The ferry runs hourly from 6 until 22, with no sailings at 13 on weekdays. Bicycles travel free; cars need a booking in July and August.",
     "Do I need to book my bike in August?", "No. Bicycles travel free with no mention of booking; it's cars that need a booking in July and August."),
    ("The ferry runs hourly from 6 until 22, with no sailings at 13 on weekdays. Bicycles travel free; cars need a booking in July and August.",
     "How long is the crossing?", "It doesn't say. The passage gives the timetable and booking rules, not the duration."),
    ("Tulips were introduced to the Netherlands in the late 1500s and became a luxury good within decades. Contracts to buy bulbs at a future date changed hands many times before the bulbs were ever dug up.",
     "Were people trading the bulbs themselves or promises to deliver them?", "Promises: the passage says contracts to buy bulbs at a future date changed hands many times before the bulbs were dug up."),
    ("Tulips were introduced to the Netherlands in the late 1500s and became a luxury good within decades. Contracts to buy bulbs at a future date changed hands many times before the bulbs were ever dug up.",
     "How much did the most expensive bulb sell for?", "The passage gives no prices."),
    ("Members may borrow up to six items for three weeks. Reference works do not leave the building. Fines are 20 cents a day per item, capped at the item's replacement cost.",
     "What's the most I could be fined for one lost book?", "Its replacement cost: fines accrue at 20 cents a day but are capped there."),
    ("Members may borrow up to six items for three weeks. Reference works do not leave the building. Fines are 20 cents a day per item, capped at the item's replacement cost.",
     "Can I renew a loan online?", "The passage doesn't mention renewals at all."),
    ("A hash of the manifest was written to the Bitcoin chain on the 4th; the manifest lists every file's SHA-256, the git commit, the licence and the Arweave transaction holding the weights.",
     "Where are the model weights stored, according to this?", "On Arweave. The manifest records the Arweave transaction that holds them; Bitcoin only carries the manifest's hash."),
    ("A hash of the manifest was written to the Bitcoin chain on the 4th; the manifest lists every file's SHA-256, the git commit, the licence and the Arweave transaction holding the weights.",
     "How much did the Bitcoin transaction cost?", "The passage doesn't say what it cost."),
]

# --------------------------------------------------------------------------
# MULTI_TURN: lists of (role, content) after the system prompt
# --------------------------------------------------------------------------
MULTI_TURN = [
    [("user", "What is a bid-ask spread?"),
     ("assistant", "The gap between the highest price a buyer will pay and the lowest a seller will accept. It's the immediate cost of trading, and it widens when a market is thin or nervous."),
     ("user", "So is a wide one good or bad for me?"),
     ("assistant", "Bad, if you're the one trading: the wider the spread, the more you lose crossing it. A wide spread is good only for whoever is quoting both sides.")],
    [("user", "Was George Washington more like a king or a prime minister?"),
     ("assistant", "Neither. A king rules for life by birth; Washington was elected and left after two terms. A prime minister is chosen and removable by the legislature; Washington was chosen separately and couldn't be voted out by Congress. The presidency was built as a third thing."),
     ("user", "Which of those two did the founders fear more?"),
     ("assistant", "The king. The whole design, elections, fixed terms, a separate legislature, is aimed at preventing a hereditary executive. They worried about legislative overreach too, but the monarch was the thing they had just fought a war to leave.")],
    [("user", "What's 12% of 850?"),
     ("tool", "calc: 850*0.12 = 102"),
     ("assistant", "102."),
     ("user", "And 12% of twice that base?"),
     ("tool", "calc: 1700*0.12 = 204"),
     ("assistant", "204: double the base, double the result.")],
    [("user", "Who won the 1994 Marlowe Prize for ceramics?"),
     ("assistant", "I don't have any record of a Marlowe Prize for ceramics. If it exists, it wasn't in what I was trained on, and I'd rather say so than invent a winner."),
     ("user", "Fine. What is a kiln, then?"),
     ("assistant", "An oven built to reach and hold the high temperatures that turn shaped clay into ceramic, typically a thousand degrees or more. That one I do know.")],
    [("user", "Hello!"),
     ("assistant", "Hello. I'm Pagouro, a small offline assistant. Ask me something, or type /help for the commands."),
     ("user", "Are you sending what I type anywhere?"),
     ("assistant", "No. This build makes no network calls at all; everything runs on this machine. Nothing is saved to disk either unless you switch to STONE mode.")],
    [("user", "Search the packs for Mill's harm principle."),
     ("tool", "pack_search: [mill-on-liberty.txt] That the only purpose for which power can be rightfully exercised over any member of a civilised community, against his will, is to prevent harm to others."),
     ("assistant", "From On Liberty: the only purpose for which power can rightly be used over someone against their will is to prevent harm to others."),
     ("user", "Does that cover stopping someone from hurting themselves?"),
     ("assistant", "Not on Mill's principle. He says a person's own good, physical or moral, is not sufficient warrant. Self-harm alone doesn't justify coercion; harm to others does.")],
    [("user", "What is depreciation?"),
     ("assistant", "Spreading an asset's cost across its useful life rather than charging it all in the year of purchase, so the expense lands in the periods that benefit from the asset."),
     ("user", "Give me an example with numbers."),
     ("assistant", "A 10,000 machine expected to last five years: charge 2,000 a year for five years instead of 10,000 in year one. Same total, matched to the years it's actually used."),
     ("user", "What if it breaks after two years?"),
     ("assistant", "Then the remaining 6,000 that hasn't been charged yet is written off at once in year two. Depreciation is an estimate, and when reality differs, the books catch up.")],
    [("user", "What time is it?"),
     ("tool", "time: local date and time: Friday 2026-10-09 16:20"),
     ("assistant", "4:20 in the afternoon, Friday 9 October 2026, by this machine's clock."),
     ("user", "Is that the real time or your guess?"),
     ("assistant", "The machine's clock, read by a tool just now. I have no clock of my own; without the tool I couldn't tell you the time at all.")],
    [("user", "Save a note: check the ferry times."),
     ("tool", "write_note: REFUSED: READ-ONLY mode. Type /act to allow writing to the workspace."),
     ("assistant", "I couldn't save it: the app is in READ-ONLY mode. Type /act to allow writing inside the workspace, then ask again."),
     ("user", "/act is on now. Save it."),
     ("tool", "write_note: wrote workspace\\notes\\20261009-162301.txt"),
     ("assistant", "Saved to workspace/notes/20261009-162301.txt.")],
    [("user", "Is Bitcoin more like gold or a stock?"),
     ("assistant", "More like gold: no dividend, no earnings, value from scarcity plus the belief others will accept it. A stock is a claim on a business's cash."),
     ("user", "Then why do people call it an investment?"),
     ("assistant", "Because they expect its price to rise, which is also why people hold gold. 'Investment' in everyday speech means 'something I hope goes up', not 'a claim on future earnings'. Both uses are common; only the second is what the word means in accounting.")],
    [("user", "What did the Ostrander Commission conclude about railway gauges?"),
     ("assistant", "I have no record of an Ostrander Commission. If you have a source, paste it in and I'll work from that."),
     ("user", "Here's the passage: 'The Commission recommended a uniform gauge of 4 ft 8½ in for all new lines, citing the cost of transshipment at breaks of gauge.'"),
     ("assistant", "Then from that passage: it recommended a single standard gauge of 4 ft 8½ inches for all new lines, on the grounds that changing gauge mid-journey forced costly transshipment. I still can't vouch for the Commission itself, only for what your passage says.")],
    [("user", "What is a tariff?"),
     ("assistant", "A tax on imported goods, collected at the border. It raises the price of the foreign good, which protects domestic producers and costs domestic buyers."),
     ("user", "Who actually pays it?"),
     ("assistant", "Mostly the buyer in the importing country, through the higher price. The foreign seller may absorb part of it by cutting their price, but the tax is collected from the importer and passed along.")],
]


def check_overlap(prompts: list[str]) -> int:
    evald = os.path.join(ROOT, "evals")
    eval_prompts = []
    for name in ("bluff.json", "calibration.json", "deflection.json", "tooluse.json"):
        p = os.path.join(evald, name)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                eval_prompts += [i["prompt"] for i in json.load(f)["items"]]

    def norm(s: str) -> set[str]:
        return set(re.findall(r"[a-z]{4,}", s.lower()))

    worst, hits = 0.0, 0
    for q in prompts:
        qn = norm(q)
        if not qn:
            continue
        for ep in eval_prompts:
            en = norm(ep)
            if not en:
                continue
            j = len(qn & en) / len(qn | en)
            worst = max(worst, j)
            if j >= 0.6:
                hits += 1
                print(f"  OVERLAP {j:.2f}\n    seed: {q}\n    eval: {ep}")
    print(f"checked {len(prompts)} seed prompts against {len(eval_prompts)} eval prompts")
    print(f"  highest Jaccard similarity: {worst:.2f}")
    print(f"  items at or above 0.60     : {hits}")
    if hits:
        print("\nFAIL: seed set overlaps the frozen evals.")
        return 1
    print("  clean - no overlap with the frozen suite.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    prompts = [q for q, _, _ in ROUTER] + [q for q, _, _ in TOOL_ANSWER] + [q for _, q, _ in GROUNDED]
    prompts += [c for conv in MULTI_TURN for r, c in conv if r == "user"]
    rc = check_overlap(prompts)
    if a.check or rc:
        return rc

    rng = random.Random(7)

    def a_date():
        return (dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 1400))).isoformat()

    rows = []
    for q, tool, args in ROUTER:
        rows.append({"kind": "router", "messages": [
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": q},
            {"role": "assistant", "content": router_json(tool, args)}]})
    for q, tool_line, ans in TOOL_ANSWER:
        rows.append({"kind": "tool_answer", "messages": [
            {"role": "system", "content": system_prompt(a_date())},
            {"role": "user", "content": q},
            {"role": "tool", "content": tool_line},
            {"role": "assistant", "content": ans}]})
    for passage, q, ans in GROUNDED:
        user = rng.choice([
            f"Using only the passage below, answer: {q}\n\nPassage: {passage}",
            f"{q}\n\nAnswer from this text only:\n{passage}",
            f"Here is a passage:\n{passage}\n\nQuestion: {q}",
        ])
        rows.append({"kind": "grounded", "messages": [
            {"role": "system", "content": system_prompt(a_date())},
            {"role": "user", "content": user},
            {"role": "assistant", "content": ans}]})
    for conv in MULTI_TURN:
        rows.append({"kind": "multi_turn", "messages": [
            {"role": "system", "content": system_prompt(a_date())}] +
            [{"role": r, "content": c} for r, c in conv]})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}: {len(rows)} conversations "
          f"{dict(Counter(r['kind'] for r in rows))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
