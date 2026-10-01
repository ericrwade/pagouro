# Full-precision checkpoints, tokenizer and volume files

Added 2026-10-01 after an outside review noted the release carried only the q8_0 and q4_k_m GGUFs. Nothing on the stick changed; these are the files the stick's model was made from, with their SHA-256 as uploaded. Not published: the tokenized training volume's per-shard metadata, which lived on the rented pod's disk and was deleted with it; the plan it was built from is `plans/volume_1b.json` in the repository and every source is a row in `corpus.json`.

| file | what | bytes | sha256 |
|---|---|---|---|
| `full-precision/pagouro-1b-f32.gguf` | the shipped model (D-96 soup) at f32, the file the q8_0 and q4_k_m were made from | 4,145,460,384 | `75f90e9226a0afdaf277bb2196da07ff094f32e558bcc57e0625a24d291d47e5` |
| `full-precision/pagouro-1b-shipped.pt` | the shipped model as the project's own PyTorch checkpoint (loads with pagouro/model.py; continue training with scripts/train_sft.py) | 4,144,369,313 | `9eae7a9abfc5576ce06d70b691b9b7b13a0d2ac6a5d1c7efe9dcfc54bc7a6f9b` |
| `full-precision/pagouro-1b-base-f32.gguf` | the pretrained base before any fine-tuning, f32 | 4,145,460,384 | `0d061df0bd159e345e17979004fad7ff7c57593fa9e341999141e8ae23b96927` |
| `full-precision/pagouro-1b-base.pt` | the pretrained base as a PyTorch checkpoint | 3,875,933,531 | `2c786f1853a99800296ebb9fbc4dc601651c41101022bb26b854e0e61ac8d62d` |
| `tokenizer/tokenizer.json` | the 32,768-entry BPE the 1B run used (`data/tokenizer_real/`, as `scripts/runpod/finish_1b.sh` names it) | 2,302,871 | `af704a62b18bee93fdc477e42b3ae0351657ac8fc5d226d17cf8c55d4fc4a720` |
| `tokenizer/tokenizer_config.json` | its config | 1,539 | `179846c8d74129b3984d257ec7f52ea7e5ff53511d93f477a7cb690215ce4be0` |
| `volume/fineweb_edu_pre2022_dumps.json` | the list of FineWeb-Edu dumps admitted by the date rule | 1,577 | `ce0a6355ca67dec9582378c25e4b24a0f137be78a5e643dc4a8e4331359a8147` |
| `volume/decay_mix.meta.json` | the anneal mixture metadata written by the run | 474 | `f75667b7b41aade4d6f2b9f21ec6123c041c7801d3563a8d11e1a67c02437c17` |
| `volume/CKPT.sha` | the pretraining checkpoint hash written on the pod | 86 | `0327c59ab186b013780de308a5e5a9cba351c85c0705af1823e41c5aab2e9dfc` |
