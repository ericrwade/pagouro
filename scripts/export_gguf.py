"""Export a Pagouro checkpoint directly to GGUF.

Written against the official `gguf` library rather than llama.cpp's
convert_hf_to_gguf.py, which now imports from a `conversion` package whose layout
moves between releases. Owning ~150 lines here removes a fragile dependency from
the one step that must never break, and this project is meant to still build in
ten years (brief section 13: avoid clever dependencies that will be dead in two).

THE ROPE PERMUTATION IS THE SUBTLE PART. Our attention uses the rotate-half
convention (the same one Hugging Face Llama uses). llama.cpp's llama architecture
expects the interleaved convention. The q and k projections must therefore be
permuted on the way out, exactly as the official converter does. Get this wrong
and the model loads, runs, and produces confident gibberish -- so scripts/verify_gguf.py
checks PyTorch and llama.cpp agree on the same prompt rather than trusting it.

Usage:
    python scripts/export_gguf.py --checkpoint checkpoints/latest.pt --out data/gguf/pagouro-m1-f32.gguf
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def permute_for_llamacpp(w: torch.Tensor, n_head: int, head_dim: int) -> torch.Tensor:
    """Rotate-half (HF) layout -> interleaved layout that llama.cpp's llama arch expects."""
    out_dim = w.shape[0]
    assert out_dim == n_head * head_dim, f"{out_dim} != {n_head}*{head_dim}"
    return (
        w.reshape(n_head, 2, head_dim // 2, *w.shape[1:])
         .swapaxes(1, 2)
         .reshape(w.shape)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=os.path.join(ROOT, "checkpoints", "latest.pt"))
    ap.add_argument("--tokenizer", default=os.path.join(ROOT, "data", "tokenizer", "tokenizer.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "gguf", "pagouro-m1-f32.gguf"))
    ap.add_argument("--name", default="Pagouro-M1")
    a = ap.parse_args()

    import gguf

    for p in (a.checkpoint, a.tokenizer):
        if not os.path.exists(p):
            raise SystemExit(f"missing: {p}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    ck = torch.load(a.checkpoint, map_location="cpu", weights_only=False)
    cfg = ck["config"]
    sd = ck["model"]
    n_head = cfg["n_heads"]
    n_kv = cfg["n_kv_heads"]
    dim = cfg["dim"]
    head_dim = dim // n_head

    print(f"checkpoint step {ck['step']}, val loss {ck.get('val_loss', float('nan')):.4f}")
    print(f"config: dim={dim} layers={cfg['n_layers']} heads={n_head} kv_heads={n_kv} "
          f"vocab={cfg['vocab_size']} ffn={cfg['ffn_hidden']} ctx={cfg['max_seq_len']}")

    w = gguf.GGUFWriter(a.out, "llama")
    w.add_name(a.name)
    w.add_context_length(cfg["max_seq_len"])
    w.add_embedding_length(dim)
    w.add_block_count(cfg["n_layers"])
    w.add_feed_forward_length(cfg["ffn_hidden"])
    w.add_head_count(n_head)
    w.add_head_count_kv(n_kv)
    w.add_rope_dimension_count(head_dim)
    w.add_rope_freq_base(cfg["rope_theta"])
    w.add_layer_norm_rms_eps(cfg["norm_eps"])
    w.add_file_type(gguf.LlamaFileType.ALL_F32)

    # ---- tokenizer ----
    with io.open(a.tokenizer, encoding="utf-8") as f:
        tj = json.load(f)
    vocab = tj["model"]["vocab"]
    merges = tj["model"].get("merges", [])
    id_to_tok = [None] * len(vocab)
    for tok, idx in vocab.items():
        id_to_tok[idx] = tok
    if any(t is None for t in id_to_tok):
        raise SystemExit("tokenizer vocab has gaps; cannot export")

    specials = {"<|endoftext|>", "<|im_start|>", "<|im_end|>", "<|tool_call|>",
                "<|tool_result|>", "<|unknown|>"}
    toktypes = [
        int(gguf.TokenType.CONTROL) if t in specials else int(gguf.TokenType.NORMAL)
        for t in id_to_tok
    ]

    w.add_tokenizer_model("gpt2")          # byte-level BPE
    w.add_tokenizer_pre("default")
    w.add_token_list(id_to_tok)
    w.add_token_types(toktypes)
    if merges:
        w.add_token_merges([" ".join(m) if isinstance(m, (list, tuple)) else m for m in merges])
    eot = vocab["<|endoftext|>"]
    w.add_bos_token_id(eot)
    w.add_eos_token_id(eot)
    w.add_pad_token_id(eot)
    w.add_add_bos_token(False)
    w.add_add_eos_token(False)

    # The chat template must travel inside the GGUF, not just in tokenizer_config.json.
    # llama.cpp reads it from here; without it the app has to hardcode the format and
    # the two can silently drift apart.
    tok_cfg = os.path.join(os.path.dirname(a.tokenizer), "tokenizer_config.json")
    if os.path.exists(tok_cfg):
        with io.open(tok_cfg, encoding="utf-8") as f:
            tmpl = json.load(f).get("chat_template")
        if tmpl:
            w.add_chat_template(tmpl)
            print("  chat template : embedded")

    # ---- tensors ----
    def put(name: str, t: torch.Tensor):
        w.add_tensor(name, t.to(torch.float32).numpy().astype(np.float32))

    put("token_embd.weight", sd["embed_tokens.weight"])
    put("output_norm.weight", sd["norm.weight"])
    # Tied embeddings: lm_head shares storage, so emit the embedding again as output.
    out_w = sd.get("lm_head.weight", sd["embed_tokens.weight"])
    put("output.weight", out_w)

    n_permuted = 0
    for i in range(cfg["n_layers"]):
        p = f"layers.{i}."
        b = f"blk.{i}."
        q = permute_for_llamacpp(sd[p + "self_attn.q_proj.weight"], n_head, head_dim)
        k = permute_for_llamacpp(sd[p + "self_attn.k_proj.weight"], n_kv, head_dim)
        n_permuted += 2
        put(b + "attn_q.weight", q)
        put(b + "attn_k.weight", k)
        put(b + "attn_v.weight", sd[p + "self_attn.v_proj.weight"])
        put(b + "attn_output.weight", sd[p + "self_attn.o_proj.weight"])
        put(b + "attn_norm.weight", sd[p + "input_layernorm.weight"])
        put(b + "ffn_gate.weight", sd[p + "mlp.gate_proj.weight"])
        put(b + "ffn_up.weight", sd[p + "mlp.up_proj.weight"])
        put(b + "ffn_down.weight", sd[p + "mlp.down_proj.weight"])
        put(b + "ffn_norm.weight", sd[p + "post_attention_layernorm.weight"])

    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()

    size = os.path.getsize(a.out)
    print(f"\nwrote {a.out}")
    print(f"  size          : {size/1e6:.1f} MB")
    print(f"  tensors       : {3 + cfg['n_layers']*9}")
    print(f"  rope-permuted : {n_permuted} (q and k per layer)")
    print(f"  vocab         : {len(id_to_tok):,}  merges: {len(merges):,}")
    print("\nNext: python scripts/verify_gguf.py   (proves llama.cpp agrees with PyTorch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
