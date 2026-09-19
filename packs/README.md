# Reference packs

Plain-text files in this folder are searchable offline by the `pack_search` tool. Each one must
be public domain or openly licensed, with its provenance row in `corpus.json`. The four US-Government packs added 2026-09-18 are
byte-identical to their ledgered files (same hash); the survival manual has its own pack-only row.

| File | Work | Basis |
|---|---|---|
| `bastiat-economic-sophisms.txt` | Economic Sophisms, Frédéric Bastiat, tr. P. J. Stirling (1845–48; translator d. 1891) | Public domain; Project Gutenberg #44145, header stripped (D-32). *The Law* was NOT used: its only Gutenberg edition is a 2007 Mises Institute translation under an unspecified CC licence (O-14) |
| `mill-on-liberty.txt` | On Liberty, John Stuart Mill (1859) | Public domain; Project Gutenberg, header stripped (D-32) |
| `us-army-fm21-76-survival.txt` | FM 21-76 / MCRP 3-02F *Survival*, US Army & Marine Corps (1992) | Public domain: US Government work (17 U.S.C. §105). OCR from archive.org `MCRP_3-02F_FM_21-76_Survival`; OCR errors present. **Chapters 9–10 and Appendices B–C (edible/medicinal/poisonous plants) omitted on purpose** (origin line 92); the app adds a fixed notice on foraging-shaped queries |
| `usda-home-canning-2015.txt` | Complete Guide to Home Canning, USDA AIB-539 (2015 revision) | Public domain: US Government work (17 U.S.C. §105); archive.org `usda-complete-guide-to-home-canning-2015-revision`; OCR errors present (rotated page headers) |
| `us-navy-neets-01-dc-electricity.txt` | NEETS Module 1: Matter, Energy, and Direct Current, US Navy NAVEDTRA 14173 (1998) | Public domain: US Government work; archive.org `NEETSModule01` (Public Domain Mark); OCR errors present in formulas |
| `us-armed-forces-recipe-service-2003.txt` | TM 10-412 Armed Forces Recipe Service (2003), ~1,700 recipes scaled to 100 portions | Public domain: US Government work; archive.org `tm-10-412-armed-forces-recipe-service-2003` (Public Domain Mark); OCR errors present in tables |
| `us-fhwa-mutcd-2009.txt` | Manual on Uniform Traffic Control Devices, 2009 edition, US FHWA | Public domain: US Government work; archive.org `mutcd2009edition_202401`; OCR errors present |

Drop any `.txt` here to make it searchable. The search is deliberately simple (paragraph chunks,
keyword overlap); swapping in an embedding index is the obvious upgrade and the interface stays
the same. Retrieval, not training, is where verbatim text belongs (origin: "train on things that
teach concepts and voice; retrieve things that should be quoted verbatim").
