# Can QStorage compete with Arweave for the release?

Assessed 2026-09-16 against Quilibrium's own documentation. Eric asked directly, and rates the
project and its founder highly, so this is worth answering properly rather than deferring to D-36.

**Short answer: not for this job, and the reason is category rather than quality.** The mirror role
in D-40 stands and is genuine.

## What the job actually is

One requirement, and it is unusual:

> A stranger, ten years from now, fetches a ~700 MB file from a link in a manifest, and checks it
> against a hash anchored to Bitcoin.

That is not a storage requirement. It is a **permanence** requirement. Nobody will be renewing a
subscription, because the project explicitly promises no maintenance (`00_ORIENTATION.md`). The file
has to outlive Eric's attention, which is the entire point of freezing and anchoring the release.

## What each one is

| | Arweave | QStorage |
|---|---|---|
| Product category | permanence | object storage service |
| Model | pay once, stored permanently, endowment-funded | S3-compatible service |
| Addressing | content-addressed, public gateway by transaction ID | S3-style API |
| Encryption | none needed; content is public | **built in** |
| Pricing | published, single-digit dollars for this size | **not published** |
| Durability guarantee | stated and quantified | **not published** |
| Permanence model | stated | **not published** |

Quilibrium's own description: *"An S3-compatible decentralized object storage service built on the
Quilibrium Network with built-in encryption and censorship resistance."*

Every word of that is a good thing. None of it is a permanence claim.

## The three problems, in order

**1. The numbers are not published.** I checked the QStorage category page, the API overview, and
searched the documentation. Pricing, durability, replication factor and the permanence model are all
absent. This is not an accusation — the docs are developer-focused and early. But a claim that
cannot be quantified cannot go in a ledger whose whole value is that a stranger can check it.

**2. Service versus permanence.** S3-compatible object storage is a service. Services have terms,
billing relationships, and the ability to stop. Arweave's model is specifically designed to survive
its operator's disinterest, which is exactly the property this release needs and exactly what the
no-maintenance promise demands.

**3. Encryption is a feature mismatch.** Our release is public by design — open weights, open
corpus ledger, published hashes. Built-in encryption solves a problem we do not have and introduces
a key-management question we do not want. A key that must survive a decade to make the model
retrievable is a new single point of failure in a design built to eliminate them.

## What would change this answer

Concretely, three things:

1. **A published permanence model.** Is stored data permanent, or does it depend on continued
   payment? This is the whole question.
2. **Published pricing** in QUIL or dollars per gigabyte, once.
3. **A stated durability and replication guarantee** that can be quoted in the manifest.

With those, it becomes comparable rather than incomparable, and the comparison should be measured
and published rather than argued.

## What it gets instead, which is not a consolation prize

Per D-40, Quilibrium hosts a **full documented mirror** of the release.

That is real. In the threat model that matters most — someone in a hostile network environment
fetching Pagouro from wherever they can reach — **more independent mirrors is the single most
valuable property after the anchored hash.** Censorship resistance is exactly the axis where
Quilibrium's design is pointed, and the mirror inherits the Bitcoin-anchored hash so it is
verifiable regardless of who hosts it.

And it produces first-hand measurement nobody else has: what it actually cost, how retrieval
performed, whether it was still there six months later, published beside the same numbers for
Arweave. That is Eric's day job written from primary data instead of secondhand claims.

If Quilibrium measures better on the axes above, that is a finding worth publishing, and the
canonical slot can move in a later release. Making that switch on evidence would be a better story
than picking it on affinity now.

## Recommendation

Arweave keeps the canonical storage slot. Quilibrium ships as a first-class mirror, measured and
published. Revisit if the permanence and pricing terms appear.

Eric should disclose holdings in both, per D-14.
