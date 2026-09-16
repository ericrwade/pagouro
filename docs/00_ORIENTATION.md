# Pagouro — orientation

The 60-second answer for a session with no other context. Written 2026-09-16 after reading the
design transcript and the brief with Eric.

## What it is

A ~1B parameter language model, trained from random weights on a fully open and fully documented
corpus, packaged as a portable app that runs offline from a USB stick on any machine. Roughly
700 MB at 4-bit.

## Why it exists

Three claims no frontier model can make, and one it structurally cannot.

1. **It does not bluff.** It says "I don't know" instead of inventing an answer. Small models are
   notoriously the worst at this, which is exactly why a small model that does it is remarkable.
2. **Every training byte is accounted for** — source, license, token count, hash — in a public
   ledger anyone can check and anyone could rebuild from.
3. **The person using it can ask anything**, because the conversation never leaves their machine.
4. The structural part: the big labs **cannot** publish a complete licensed corpus ledger, because
   they cannot disclose their training data that way. That gap does not close as their models get
   better. It is the one axis where a hobbyist budget beats a billion-dollar one.

## What "done" looks like

A GitHub Release containing a zip: the model, the chat app, the trainer, the ledger, the eval
results. Signed. Hash-anchored to Bitcoin so someone downloading from an unknown mirror in a
hostile network can verify they got the real thing. Then the repo is archived. Finished on
purpose, not abandoned.

Success is not downloads. Ranked by how hard they are to fake: someone independently reruns the
bluff-rate test and posts their numbers; someone ships a pack; someone forks it into their own
tradition.

## The shape of the thing

Two executables plus data. A chat app with an unmissable ONLINE/OFFLINE toggle, retrieval over
local document packs, and a small tool harness with grammar-constrained calls. A trainer that
lets a user extend the model on their own files locally, or export a job bundle for a rented GPU.
No server, no accounts, no telemetry, no update check.

## The personality

Opinionated where it has grounds, silent where it does not. It engages seriously with contested
economics — capitalism, sovereignty, money, debt, ownership — rather than deflecting the way
commercial models do. That comes from the fine-tuning stage, not from removing safety training.
The "uncensored model" niche is explicitly rejected (D-12).

Its domain knowledge comes from the written tradition the crypto ethos descends from: Smith,
Bastiat, Mill, Locke, the Austrians, the founding documents, the chain source code. Mostly public
domain, which is what makes the ledger possible. Bitcointalk supplies contemporary voice, not
substance.

## What it is NOT

Not a frontier competitor. Not a general coder. Not a chatbot that knows the news. Not a hosted
service. No token, no DRM, no on-chain gating, no website beyond a redirect. Not maintained after
release, and it says so in the first paragraph of the README.

It will lose to Qwen on general capability at any budget Eric would spend, by roughly a hundredfold
in training data. That is expected and is not the game being played.

## The scope boundary that prevents the most wasted work

Pagouro is a **finished artifact and a template**, not a product and not a company. Anything that
creates an ongoing obligation — a server, an account system, a maintained service, a dependency on
a network that must keep working — is out of scope by construction, because it contradicts the
no-maintenance promise the release is built on.

---

*Hermit crab: carries a home it can leave. Ouroboros: needs nothing from outside. Both are the
product.*
