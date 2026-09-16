# Pagouro threat model

Locked 2026-09-16. **This file governs what the README and the UI are allowed to claim.**

Pagouro may be used by people for whom a leaked question carries real consequences. That makes
honesty here a safety property, not a documentation preference. The failure mode is not a missing
feature — it is a comforting claim that turns out to be false for someone who relied on it.

**Rule: never claim protection this table does not grant.** If a marketing line and this table
disagree, the line is wrong.

---

## What "speak freely" means

The **human** speaks freely, because the conversation is local and offline. That is the primary
meaning and the reason the property matters.

A secondary and compatible property: the model itself engages with contested economic and
political ideas rather than deflecting them. See `DECISIONS.md` D-12. Do not let the second
meaning crowd out the first in any user-facing text.

---

## The table

| # | Threat | Protected? | Detail |
|---|---|---|---|
| 1 | Provider logs your questions forever | **Yes, fully** | No account, no query leaves the machine, no retention anywhere. |
| 2 | Network observer sees what you asked | **Yes, in offline mode** | Nothing transits. In online mode, only harness-generated search queries go out, never the conversation. |
| 3 | Questions linked to your identity | **Yes** | No login, no telemetry, no update check, no identifiers. |
| 4 | Device seized and examined | **Partial — user-mitigable** | Keep the model, the app and all state on the USB stick and remove it. The host then holds far less. Not complete: OS artifacts (temp files, prefetch, swap) may persist on the host, and possession of the stick itself is still possession. |
| 5 | Malware, keylogger, screen capture | **No. No solution.** | A compromised endpoint defeats everything else here. Offline mode does nothing against it. Say so plainly and tell the user to be extremely careful about the machine they use. |
| 6 | Acquiring it is observed | **Partial — user-mitigable** | Downloading is a network event and is observable. Copying from a known-good USB stick is not. Sideloading is the safer path, and it inherits the risk in #5: a stick from an untrusted party can carry malware, and a tampered build is only detectable by checking the hash (see below). |
| 7 | Someone watching your screen | **No. No solution.** | Shoulder surfing, cameras, physical presence. Out of scope, and must not be implied otherwise. |

## The honest one-liner

> Your questions never leave this machine. This machine is still your responsibility.

That sentence, or something equally precise, belongs in the README's privacy section and in the
tooltip on the ONLINE/OFFLINE toggle.

---

## What the threat model requires the build to do

These are requirements, not suggestions. Each follows directly from a row above.

1. **No conversation history written to disk by default.** Ephemeral by default; saving is a
   deliberate opt-in with a plain-language warning attached. Follows from #4.
2. **The offline audit is the flagship test, not a checklist item.** It must be reproducible by a
   third party in minutes. A person at risk must not have to trust Eric. Ship the script, publish
   the result. Follows from #1 and #2.
3. **Minimize host footprint.** Run from the stick; write nothing to the host that is not required.
   Document honestly that Windows makes this imperfect. Follows from #4.
4. **Keep the artifact small.** File size is a safety property when acquisition is constrained or
   monitored. A 1B model at 4-bit is roughly 700 MB. Follows from #6.
5. **Hash verification must be a documented one-liner.** Not an exercise for the reader. Follows
   from #6 and the mirror case below.

## Why the Bitcoin anchor is required, not ceremony

The redistribution case is the point: someone zips Pagouro and rehosts it where people can reach
it. That is the best outcome available and the release is designed for it.

It only works if a person downloading from an unknown mirror on a hostile network can verify they
got the real thing and not a build with something added. The signed manifest plus the
Bitcoin-anchored hash is exactly that check. This is the anchor doing real work for a real person,
and it is why the release is a frozen, signed artifact rather than a maintained project — every
mirror of a maintained project drifts, and drift destroys verifiability.

Requirements that follow:
- Publish SHA-256 next to every download, and the manifest signature alongside.
- Document verification as a single copy-pasteable command per platform.
- Anchor **after** the weights are final, so the IDs inside the manifest are real.
