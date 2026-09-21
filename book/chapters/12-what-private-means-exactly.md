# Chapter 12 — What "private" means, exactly

*Licence: all rights reserved for the story sections; the "Do it" section at the end is
CC BY-SA 4.0 (D-64 — this chapter carries both strands and says where the line is).*

*Draft 1 (2026-09-21), edited from `docs/THREAT_MODEL.md` (locked 2026-09-16), `BUILD_LOG.md`
Day 1, decisions D-12, D-13, D-14, D-19, and the offline audit's own source and results. Every
number is from the file the footnote names.*

---

The brief said the model should "speak freely," and for most of the first day the session read
that as a property of the model: it would engage with contested economics instead of hedging,
which is true and worth having, and it had already warned Eric off the neighbouring
"uncensored model" market as crowded and reputationally expensive. Then Eric explained what he
meant. The *human* speaks freely. Because the thing is local and offline, nothing leaves the
machine, and so a person can ask it what they would not type into a website. He raised the
possibility of someone zipping the whole thing up and hosting it where people in repressive
countries could reach it.[^d12]

That changed the engineering enough to get a document of its own, and the document has an
unusual job. `THREAT_MODEL.md` does not describe features. It governs what the README and the
interface are *allowed to say*, because for this product the failure mode is not a missing
capability. It is a comforting sentence that turns out to be false for someone who relied on
it.[^tm] A person at genuine risk may read the word "private" on the box and act on it. So the
word is defined by a table, and the rule at the top of the table is the only rule: never claim
a protection the table does not grant. If a marketing line and the table disagree, the line is
wrong.

## The table

Seven threats. Three answers.

The provider logging your questions forever: **fully protected**, because there is no provider.
No account, no query leaves the machine, nothing is retained anywhere. A network observer
seeing what you asked: **protected in offline mode**, where nothing transits; in online mode
only the harness's own search queries go out, never the conversation. Your questions linked to
your identity: **protected** — no login, no telemetry, no update check, no identifiers of any
kind.[^rows123]

The device seized and examined: **partial, and it is on you.** Keep the model, the app and all
its state on the stick and remove the stick, and the host computer holds far less. Not nothing:
temporary files, prefetch records and swap may persist on the host, Windows makes a clean
footprint imperfect, and possession of the stick is still possession. Acquiring the thing in
the first place: **partial, and on you again.** Downloading is a network event and is
observable. Copying from a stick someone hands you is not — and inherits the next row's problem,
because a stick from an untrusted party can carry anything, and a tampered build is only
detectable by checking the hash.[^rows46]

Malware, a keylogger, screen capture: **no protection, and no solution.** A compromised
endpoint defeats everything else on the list, offline mode does nothing about it, and the
document's instruction is to say so plainly and tell the user to be extremely careful about the
machine they use. Someone watching the screen — shoulder-surfing, a camera, a person in the
room: **no protection, and no solution.** Out of scope, and it must not be implied
otherwise.[^rows57]

Eric went through the table row by row and refined the partial answers himself. The sentence
that survived is the one that goes on the toggle's tooltip and in the README's privacy
section:

> Your questions never leave this machine. This machine is still your responsibility.[^oneliner]

## What the table made us build

Four things follow from it that were not in the brief.

**Nothing is written to disk unless you ask.** That falls straight out of the seizure row. The
app has two switches and the second one is this: SAND, the default, where nothing is saved, and
STONE, where the chat is written to disk on purpose. The names were argued over more than you
would expect — Jekyll and Hyde implies the model changes personality; Freebird and Prisoner
leaves nobody sure which state keeps the data; Incognito belongs to a browser — and they were
chosen because writing in sand versus carving in stone is instantly legible about *direction*.
But the metaphor is only the label. The plain words are always underneath it, and one status
line carries both switches where the eye already goes: `OFFLINE · SAND` in calm green, `ONLINE ·
STONE` in loud amber. Two poetic toggles side by side would be confused, and under this table a
confused toggle is a safety failure, not a usability note.[^d19]

**The offline audit is the flagship test.** Not a checklist item: the test. A stranger must be
able to reproduce it in minutes, because a person at risk must not have to trust Eric. The
method is deliberately dumb. Run the program, and while it runs, ask the operating system —
not the program — for the process tree's open network endpoints, over and over, and record what
comes back. A program can lie about its log lines; it cannot lie to the OS connection table.
The script ships on the stick with its result.[^audit]

And then, on the nineteenth, it lied anyway. Not about connections — about having run. The
binary it was pointed at had started in conversation mode, found nothing on its input, and
exited in six-tenths of a second. The audit took zero samples of a process that no longer
existed, observed no connections, and printed PASS. A pass with nothing observed is worth
exactly nothing, and the rebuilt script says so: fewer than ten samples or under two seconds of
running and the verdict is INCONCLUSIVE, never PASS. Run for real the same day it took
forty-nine samples over a minute and saw nothing; the stick's current audit is thirty-nine
samples over sixty seconds, zero connections.[^vacuous] It is the same lesson as the bluff scorer
that flattered a model for saying nothing: a test can only be trusted once you have seen it
fail, and "we found nothing" has to be distinguished from "we did not look."

**Keep the artifact small, and put the hash next to it.** File size is a safety property when
acquiring the thing is watched; a billion-parameter model at four-bit is about seven hundred
megabytes, which is why that is the size. And because the redistribution case — someone
rehosting the stick where it can be reached — is the point rather than a nuisance, a person
downloading from an unknown mirror on a hostile network has to be able to check they got the
real thing. That is the manifest, its signature, and the Bitcoin anchor, and it is why the
anchor stopped being ceremony on the first day: it is the check doing work for a real person.
It is also why the release is frozen rather than maintained. Every mirror of a maintained
project drifts, and drift destroys the check.[^anchor]

The last thing the table did was set the tone of every sentence about privacy in the project,
this book included. Where a claim could be read more generously than the table allows, the
project cuts the claim rather than adding a footnote. That is why you will not find the word
"anonymous" anywhere on the stick, and why the honest one-liner has a second sentence.

## Do it: check a stick someone gave you

*This section is CC BY-SA 4.0.*

You have been handed a USB stick, or a zip file from a mirror, that claims to be Pagouro.
Before you type anything into it:

1. **Check the manifest.** In the folder, run `python verify_manifest.py`. It hashes every file
   and compares it with `MANIFEST.md`. You should see `VERDICT: every listed file matches the
   manifest`. Anything else means a file was changed or added after the release was built.[^verify]
2. **Check the manifest is the real one.** The manifest is signed; `MANIFEST.md.minisig` sits
   beside it and the public key line is printed in the README and in `MANIFESTO.txt`. Compare
   the key against a copy you got from somewhere else — the project page, the anchor, a friend —
   and verify the signature with `minisign -Vm MANIFEST.md -p minisign.pub`. A matching manifest
   with the wrong key is a matching *forgery*.
3. **Run the audit yourself.** `python evals/offline_audit.py` with the stick's runner and model,
   as the README shows. You should see `PASS` with a sample count in the dozens and an elapsed
   time near a minute. `INCONCLUSIVE` means the program did not run long enough to be watched;
   run it again. Any connection listed is a release blocker, not a percentage.[^audit]
4. **Read the table.** It is in `docs/THREAT_MODEL.md` on the stick. Rows 5 and 7 are about
   your machine and your room, and nothing on the stick can help with them.

What you should see, in order: a matching manifest, a valid signature under a key you have
checked independently, an audit with real samples and no connections. If all three hold, the
stick is what it claims to be, and what it claims is exactly the table — no more.

---

[^d12]: `BUILD_LOG.md` Day 1, "The correction that mattered most"; D-12 ("speak freely" means the HUMAN speaks freely).
[^tm]: `docs/THREAT_MODEL.md`, preamble: "The failure mode is not a missing feature — it is a comforting claim that turns out to be false for someone who relied on it."
[^rows123]: `docs/THREAT_MODEL.md`, table rows 1–3.
[^rows46]: `docs/THREAT_MODEL.md`, rows 4 and 6.
[^rows57]: `docs/THREAT_MODEL.md`, rows 5 and 7.
[^oneliner]: `docs/THREAT_MODEL.md`, "The honest one-liner"; `BUILD_LOG.md` Day 1: "Eric went through it row by row and refined the partial answers himself."
[^d19]: D-19 (2026-09-16), SAND / STONE and the two-toggle constraint; `app/pagouro_app.py` defaults to SAND.
[^audit]: `evals/offline_audit.py`, docstring and method; D-13; `docs/THREAT_MODEL.md` requirement 2. The script states its own limitation: it observes sockets opened by the process tree and does not prove the absence of exotic channels; a release audit pairs it with a packet capture.
[^vacuous]: `evals/offline_audit.py`, the comment above the INCONCLUSIVE guard (2026-09-19: exited in 0.6 s with 0 samples and said PASS); `docs/SESSION_LOG.md` 2026-09-18: "Offline audit re-run for real (49 samples, 0 connections)"; `book/chapters/08-…` footnote 1: 39 samples over 60 s, 0 connections on the stick.
[^anchor]: `docs/THREAT_MODEL.md`, requirements 4 and 5 and "Why the Bitcoin anchor is required, not ceremony"; D-14.
[^verify]: `docs/RELEASE_RUNBOOK.md` steps 2–3 and the signing step (minisign).
