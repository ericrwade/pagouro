"""House-palette candidates for Pagouro Draws (O-28, D-67). Standard library only.

The palette *is* the style in pixel art. Each candidate is 32 colours in eight ramps of four,
dark to light, named after the print world they come from: the Victorian / Gilded Age trade
card, catalogue cut and natural-history plate (1880-1928), plus the shell / sea range the hermit
crab needs. "Modernised" is what the renderer does: one-pixel outlines in the ink ramp's darkest
colour, 32 or 64 px, nearest-colour quantisation (ordered dither optional).

Three candidates are here so Eric can pick from rendered sheets (scripts/palette_sheet.py);
the chosen one becomes HOUSE and is listed in the release manifest. Nothing here is generated
by a model; the values were chosen by hand from the reference print colours named in each brief.
"""

from __future__ import annotations

Pixel = tuple[int, int, int]


def _hex(s: str) -> Pixel:
    s = s.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


class Palette:
    def __init__(self, name: str, brief: str, ramps: dict[str, list[str]]):
        self.name, self.brief = name, brief
        self.ramps = {k: [_hex(c) for c in v] for k, v in ramps.items()}
        self.colors: list[Pixel] = [c for v in self.ramps.values() for c in v]
        assert len(self.colors) == 32 and len(set(self.colors)) == 32, name
        self.ink: Pixel = self.colors[0]           # outline colour: darkest of the first ramp
        self.paper: Pixel = self.ramps[list(self.ramps)[1]][-1]  # lightest of the second ramp

    def nearest(self, px: Pixel) -> Pixel:
        r, g, b = px
        # weighted RGB distance (eye is most sensitive to green); good enough at 32 colours
        return min(self.colors, key=lambda c: 2 * (c[0] - r) ** 2 + 4 * (c[1] - g) ** 2 + 3 * (c[2] - b) ** 2)

    def quantize(self, img: list[list[Pixel]], transparent: Pixel | None = None, dither: bool = False) -> list[list[Pixel]]:
        """Snap every pixel to the palette; optional 2x2 ordered dither for the in-between tones."""
        bayer = ((0, 2), (3, 1))
        out = []
        for y, row in enumerate(img):
            line = []
            for x, px in enumerate(row):
                if transparent is not None and px == transparent:
                    line.append(px); continue
                if dither:
                    t = (bayer[y & 1][x & 1] / 4.0 - 0.375) * 24
                    px = tuple(max(0, min(255, int(c + t))) for c in px)  # type: ignore[assignment]
                line.append(self.nearest(px))
            out.append(line)
        return out

    def as_dict(self) -> dict:
        return {"name": self.name, "brief": self.brief,
                "ramps": {k: ["#%02x%02x%02x" % c for c in v] for k, v in self.ramps.items()}}


CANDIDATES: dict[str, Palette] = {
    "tradecard": Palette(
        "Trade Card",
        "The chromolithographed trade card and catalogue cut, ~1885: black ink on cream stock, oxblood "
        "and brass for the ornament, verdigris for the borders; shell coral and a harbour blue for the crab. "
        "Brightest of the three; reads well on white and on dark terminals.",
        {
            "ink":       ["#14100e", "#2b2420", "#4a3f38", "#6e625a"],
            "cream":     ["#a89a80", "#cfc2a4", "#e9dfc4", "#f8f2e2"],
            "oxblood":   ["#4a1219", "#7a1e28", "#a83a3c", "#d0705e"],
            "brass":     ["#6b4a12", "#a67a1e", "#d4a83a", "#f0d47a"],
            "verdigris": ["#12403a", "#1f6b5c", "#3f9a82", "#8ccbb0"],
            "coral":     ["#7a3a3a", "#b86050", "#e08a72", "#f4c0a4"],
            "harbour":   ["#102438", "#1e4a6a", "#3a7ea0", "#8ac4d8"],
            "slate":     ["#2a2438", "#4c4468", "#7a6f98", "#b3a9c8"],
        }),
    "gaslight": Palette(
        "Gaslight",
        "The Gilded Age after dark: night ink, gaslight amber, plum velvet, deep teal, bone white, "
        "silver for the modern edge; copper and sea-glass for the crab. Darkest of the three; built for a "
        "dark terminal and for profile pictures against dark app chrome.",
        {
            "night":    ["#0b0a10", "#1a1722", "#2c2838", "#45405a"],
            "bone":     ["#8e8676", "#b8ae9a", "#dcd3bd", "#f5efdf"],
            "amber":    ["#5c2e0a", "#9a5514", "#d8892a", "#f7c15c"],
            "plum":     ["#3a1030", "#6a2050", "#9c3c78", "#cf7aa8"],
            "teal":     ["#0c3038", "#145a62", "#2a8a90", "#6ec4c4"],
            "copper":   ["#5a2a1a", "#92472c", "#c6764c", "#eaab84"],
            "seaglass": ["#1c3a40", "#2e6a66", "#56a090", "#a8d8c4"],
            "silver":   ["#4a4e58", "#767c88", "#a8aeb8", "#d8dce4"],
        }),
    "naturalist": Palette(
        "Naturalist Plate",
        "The hand-coloured natural-history lithograph (the Biodiversity Heritage Library shelf): sepia "
        "ink on warm paper, coral, ochre, olive, cerulean, rose; the hermit crab is a Victorian plate "
        "subject to begin with. Warmest of the three; the most 'illustrated', least 'poster'.",
        {
            "sepia":    ["#1c1410", "#3c2c20", "#5e4a38", "#806a54"],
            "paper":    ["#b0a284", "#d2c6a6", "#ece3c8", "#fbf6e8"],
            "coral":    ["#8a2a22", "#c0402e", "#e46a46", "#f9a07a"],
            "ochre":    ["#7a5410", "#b07e1e", "#dcae3c", "#f5d878"],
            "olive":    ["#2c3a14", "#4e6420", "#7e9838", "#b8cc70"],
            "cerulean": ["#143a5c", "#1e6690", "#3c9ac4", "#8ed0ea"],
            "rose":     ["#7c3050", "#b05070", "#dc8098", "#f6b8c4"],
            "shadow":   ["#2e3440", "#505868", "#7c8494", "#b4bac8"],
        }),
}

HOUSE: str | None = None   # set when Eric picks (O-28); until then the app's /art uses artkit's small palettes
