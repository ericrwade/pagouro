# Reference packs

Plain-text files in this folder are searchable offline by the `pack_search` tool. Each one must
be public domain or openly licensed, with its provenance row in `docs/corpus.json`.

| File | Work | Basis |
|---|---|---|
| `bastiat-economic-sophisms.txt` | Economic Sophisms, Frédéric Bastiat, tr. P. J. Stirling (1845–48; translator d. 1891) | Public domain; Project Gutenberg #44145, header stripped (D-32). *The Law* was NOT used: its only Gutenberg edition is a 2007 Mises Institute translation under an unspecified CC licence (O-14) |
| `mill-on-liberty.txt` | On Liberty, John Stuart Mill (1859) | Public domain; Project Gutenberg, header stripped (D-32) |
| `us-army-fm21-76-survival.txt` | FM 21-76 / MCRP 3-02F *Survival*, US Army & Marine Corps (1992) | Public domain: US Government work (17 U.S.C. §105). OCR from archive.org `MCRP_3-02F_FM_21-76_Survival`; OCR errors present. **Chapters 9–10 and Appendices B–C (edible/medicinal/poisonous plants) omitted on purpose** (origin line 92); the app adds a fixed notice on foraging-shaped queries |

Drop any `.txt` here to make it searchable. The search is deliberately simple (paragraph chunks,
keyword overlap); swapping in an embedding index is the obvious upgrade and the interface stays
the same. Retrieval, not training, is where verbatim text belongs (origin: "train on things that
teach concepts and voice; retrieve things that should be quoted verbatim").
