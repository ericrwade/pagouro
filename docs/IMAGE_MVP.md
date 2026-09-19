# Pagouro Draws — an image generator on the stick (proposal, O-21)

Eric, 2026-09-18, from the road: "Is there any level of image generator that could be part
of Pagouro? Even if it's small and MVP, could we build a framework for image creation? Pixel
art or low res? Or is that out of range?"

**Answer: in range, as long as the target is low-resolution pixel art and the claim is the
same one the text model makes — every training byte licensed, nothing leaves the machine,
and it says when it can't.** Not in range: anything that competes with Stable Diffusion on
photorealism. Nobody needs that on a USB stick, and the corpus it would take cannot be
ledgered.

## Why pixel art is the right target, not a consolation prize

1. **Low resolution is where a small model is honest.** A 32×32 or 64×64 image is a few
   thousand values. A 20–40M-parameter model can learn that distribution well on a rented A40
   in hours; the same model at 512×512 learns nothing usable. Pixel art is the one visual
   style where the resolution ceiling is the aesthetic, not a limitation to apologise for.
2. **The terminal can show it.** The app is a terminal program. With Unicode half-block
   characters (`▀`, two pixels per character cell) and 24-bit ANSI colour, a 32×32 sprite is a
   16-row, 32-column block that renders in Windows Terminal, and a 64×64 fits in a normal
   window. No image viewer, no GUI, nothing new to ship. `/act` lets it also write a PNG into
   `workspace/art/` (PNG writing is ~40 lines of standard library: zlib + struct).
3. **CPU inference is seconds, not minutes.** A 30M-parameter diffusion model at 32×32 with
   30–50 denoising steps is ~1–3 s on a desktop CPU in plain PyTorch; exported to ONNX or
   ggml it is faster still. The weights are 60–120 MB in fp16 — well inside the stick budget.
4. **It fits the agent framework we already built.** It is one more tool: `draw` takes a
   short prompt string, the router grammar already only lets the model name real tools, the
   CAN ACT switch already governs writing files, the exit line already lists files written.
   The harness does not change shape; it gains a verb.

## The corpus: this is the good news

Licensed image data with a nameable basis is *more* available than licensed text, because
museums and asset makers publish it that way on purpose:

| Source | Licence | What | Pre-2022 |
|---|---|---|---|
| Kenney.nl asset packs | CC0 | ~40,000 game sprites, tiles, UI, 16–64 px, consistent style | most packs |
| OpenGameArt (CC0 filter) | CC0 per asset | thousands of sprites/tilesets with tags | yes |
| Smithsonian Open Access | CC0 | 2.8M+ images of objects, art, specimens | yes |
| The Met Open Access | CC0 | ~470k artworks with titles, tags, dates | yes |
| Rijksmuseum, Art Institute of Chicago, Cleveland MoA | CC0 | hundreds of thousands, with metadata | yes |
| NASA, USGS, NOAA image libraries | US Gov PD | photos, maps, diagrams | yes |
| Program-generated (O-18) | ours, synthetic by construction | procedurally drawn shapes, dithers, palettes, labelled exactly | n/a |

Every row gets the same ledger treatment: source, licence, count, hash, date. Photographs
and paintings get downsampled to 32×32/64×64 and palette-quantised — at that size they *become*
pixel art, which is why museum CC0 collections are useful even though they are not sprites.
The text conditioning ("a red castle", "a small boat at night") comes from the metadata those
collections already carry (titles, tags, object names), not from a captioning model — so the
captions are licensed too, and pre-2022 holds for the whole set.

**Never:** scraped fan art, game rips, "found on the internet" sprite sheets, anything NC or
ND, anything a model captioned. Same rule as the text: unclear = no.

## The model, two candidates (pick by measurement, D-29 style)

**A. Tiny latent/pixel diffusion (DiT-S or a small UNet, 20–40M params).** The known-good
recipe for small images. Conditioning: a frozen text encoder — and the honest small option is
Pagouro's own embedding table plus a small learned pooler, so the drawing model speaks the
same vocabulary as the chat model. Sample quality at 32×32 on a few hundred thousand images:
recognisable objects and styles, weak on composition and text-in-image (fine: pixel art).

**B. Image tokens through the Pagouro transformer itself.** Train a small VQ-VAE (codebook
512–1024, 8×8 latent for 32×32 images), then treat the 64 image tokens as extra vocabulary
and fine-tune the *same* Pagouro language model to emit them after a caption. One model
draws and talks. Slower to sample than A (64 autoregressive steps, still ~1 s on CPU),
weaker fidelity at MVP scale, but the story — "the same brain, one vocabulary" — is very
Pagouro, and it reuses every piece of infrastructure we have (tokenizer, train.py, GGUF).

Recommendation for the MVP: **A** for the first result (it will look better sooner), with B as
the ablation once A exists, because B is the one that would make the book chapter.

## What it will cost, measured against what we know

- Data: 1–2 sessions to fetch, downsample, palette-quantise and ledger ~200–500k images
  (the museum APIs are paged and polite; Kenney is a handful of zips).
- Code: `art/` module — VQ-VAE or DiT in plain PyTorch, ~600 lines; sampler; ANSI renderer;
  PNG writer; `draw` tool in the harness. 1–2 sessions.
- Training: 32×32 diffusion, 30M params, ~300k images × 50 epochs ≈ small. On the A40 we
  measured at 38–62k text tokens/s, expect **2–6 GPU-hours ≈ $1–3**. 64×64 is 4× that. Both
  inside the current $165 without touching the 1B budget.
- Eval: FID against a held-out CC0 slice for the number on the box; plus a frozen prompt set
  of 40 captions rendered and kept (the visual equivalent of the bluff set — and a "can't"
  case: prompts outside the training distribution should produce a stated refusal from the
  text side, not a confident smear).

## What it will not be, said now so the box can say it later

- Not photorealistic, not high resolution, not fast at anything above 64×64.
- Text-to-image alignment will be loose at MVP scale: "a blue bird" will be blue and
  bird-shaped; "a blue bird holding a sword facing left" will not be reliable.
- It cannot bluff in the text sense, but it can produce mush; the eval must count mush.

## Where it sits in the plan

After the Flash results and the SFT re-run, before the 1B launch decision — it is cheap,
it reuses the harness, and it gives the stick a second reason to exist. Logged as **O-21**;
Eric's call whether it goes into v1.0 or ships as v1.1 on the same stick.
