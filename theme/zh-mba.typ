// ═══════════════════════════════════════════════════════════════════════════
// Canton of Zurich design system: design tokens and components
// ═══════════════════════════════════════════════════════════════════════════
//
// Adopted from pk19-typst-theme (src/tokens.typ, src/components.typ, 0.3.0).
// NOT an official Canton of Zurich package: PK19's own theme, built to follow the
// canton's published design. No lion, no flag.
//
// Source of truth:
//   https://www.zh.ch/de/webangebote-entwickeln-und-gestalten.html
//     …/designsystem/design-grundlagen/farben.html
//     …/designsystem/design-grundlagen/typografie.html
//     …/designsystem/design-grundlagen/abstaende.html
//
// Rules carried over from the pk19 deep dive:
//   - only canton colours; a soft background matches its accent (tone on tone)
//   - red only for errors, green only for success
//   - two weights only: Black and Regular
//   - all text left-aligned
//   - spacing on the 8pt grid, no shadows

// ── Accent colours ─────────────────────────────────────────────────────────
#let zh_blau = rgb("#0070B4")
#let zh_dunkelblau = rgb("#00407C")
#let zh_tuerkis = rgb("#00797B")
#let zh_gruen = rgb("#1A7F1F")
#let zh_bordeaux = rgb("#B01657")
#let zh_magenta = rgb("#D40053")
#let zh_violett = rgb("#7F3DA7")

// ── Soft accent colours (tone on tone with the accent above) ─────────────────
#let zh_softblau = rgb("#EDF5FA")
#let zh_blaugrau = rgb("#E0E8EE")
#let zh_softtuerkis = rgb("#E8F3F2")
#let zh_softgruen = rgb("#EBF6EB")
#let zh_softbordeaux = rgb("#F6E3EA")
#let zh_softrot = rgb("#FCEDF3")
#let zh_softviolett = rgb("#ECE2F1")
#let zh_soft_blau = zh_softblau // old name, still imported by src/layout.typ

// ── Greys ──────────────────────────────────────────────────────────────────
#let zh_black_100 = rgb("#000000")
#let zh_black_80 = rgb("#333333")
#let zh_black_60 = rgb("#666666")
#let zh_black_40 = rgb("#949494")
#let zh_black_20 = rgb("#CCCCCC")
#let zh_black_10 = rgb("#F0F0F0")
#let zh_black_5 = rgb("#F7F7F7")
#let zh_white = rgb("#FFFFFF")

// ── Functional colours ─────────────────────────────────────────────────
// Red is used for error messages only, green for success messages only.
// Cyan is only the thin brand rule under titles.
#let zh_cyan = rgb("#009EE0")
#let zh_rot = rgb("#D93C1A")
#let zh_gruen_funktion = rgb("#1A7F1F")

// ── Purpose layer: name what a colour is FOR (contrast on white) ──────────
#let ink_text = zh_black_100 // body, headings, labels, 21:1
#let ink_soft = zh_black_80 // lead, sender lines, 12.6:1
#let ink_secondary = zh_black_60 // hints, metadata, footers, 5.74:1
#let line_rule = zh_black_20 // hairlines and dividers, decorative only
#let line_brand = zh_cyan
#let fill_info = zh_softblau
#let fill_table_header = zh_softblau
#let fill_table_stripe = zh_black_5
#let accent = zh_blau // PK19 is an organisational unit, so its colour is blue

// ── Typography ─────────────────────────────────────────────────────────────
// Inter is sanctioned for digital use with exactly these features. The
// fallbacks keep the build working where a face is missing.
#let body_font = ("Inter", "Helvetica", "Arial")
#let heading_font = ("Inter Display", "Inter", "Helvetica", "Arial")
#let text_features = ("ss07": 1, "ss08": 1, "cv03": 1, "cv04": 1, "cv10": 1)
#let weight_regular = "regular"
#let weight_black = "black"

// ── Spacing: 8pt grid ─────────────────────────────────────────────────────
#let sp_half = 4pt // inside a component only
#let sp_1 = 8pt
#let sp_2 = 16pt
#let sp_3 = 24pt

// ── Components (names unchanged, the chapters import them) ────────────────

// Inside a callout `*emphasis*` is Black ink: accent blue would out-shout the
// callout's own title.
#let _kb(body) = {
  show strong: it => text(weight: weight_black, fill: ink_text)[#it.body]
  body
}

// Source of truth for binding rules (follows pk19 pattern).
#let quellen = (
  gesetz: [Gesetz],
  rqv: [RQV],
  ab: [AB QV],
  wegleitung: [Wegleitung],
  kk: [Kriterienkatalog],
  pk19: [PK19-Regel],
)

// Binds the reader: law, Ausführungsbestimmungen, a binding Leitfaden rule, or
// a PK19 rule that changes what must be done.
#let verbindlich(body, quelle: none, label: none) = {
  assert(
    quelle != none,
    message: "verbindlich needs `quelle:` — one or more of " + quellen.keys().join(", "),
  )
  let keys = if type(quelle) == array { quelle } else { (quelle,) }
  for k in keys {
    assert(k in quellen, message: "verbindlich: unknown quelle " + repr(k) + "; use " + quellen.keys().join(", "))
  }
  block(
    breakable: false,
    fill: fill_info,
    stroke: (left: 6pt + line_binding, rest: 1.5pt + line_binding),
    radius: (right: 3pt),
    inset: (left: sp_2, y: sp_1, right: sp_1),
    spacing: sp_2,
    width: 100%,
  )[
    #text(weight: weight_black, fill: line_binding)[
      Verbindlich (#keys.map(k => quellen.at(k)).join([ · ]))#if label != none [ · #label]:#h(4pt)
    ]
    #_kb(body)
  ]
}
#let line_binding = zh_dunkelblau

// How PK19 usually does it; not law.
#let praxis(body, label: none) = {
  block(
    fill: fill_info,
    stroke: (left: 4pt + accent),
    inset: (left: sp_2, y: sp_1, right: sp_1),
    spacing: sp_2,
    width: 100%,
    breakable: false,
  )[
    #text(weight: weight_black, fill: accent)[PK19-Praxis#if label != none [ · #label]:#h(4pt)]
    #_kb(body)
  ]
}

// Context, instruction for filling, advice; nothing follows from ignoring it.
// One look for every emphasised line: tip, key statement and closing wish.
#let _bar(body) = block(
  breakable: false,
  stroke: (left: 1.5pt + accent),
  inset: (left: sp_2, y: sp_1, right: sp_1),
  spacing: sp_2,
  width: 100%,
  body,
)

#let hinweis(body, label: none) = _bar[
  #text(weight: weight_black, fill: ink_text)[#if label != none [#label] else [Hinweis]:#h(4pt)]
  #_kb(body)
]

// Kept as a box: the pk19 theme's "PK19 practice" look, soft blue fill with a
// 4pt accent bar. No rounded corners, no shadow.
// DEPRECATED: use `praxis` instead.
#let callout(body) = praxis(body)

// The pk19 theme's "note" style: no fill, 1.5pt accent bar, label in Black.
// Replaces the former yellow box (#FFF8E6 / #CC9900), which is not a canton
// colour.
// DEPRECATED: use `hinweis` instead.
#let tip_block(body) = hinweis(body, label: [Tipp])

#let term_block(label, body) = block(spacing: sp_3, width: 100%)[
  #text(weight: weight_black, fill: ink_text)[#label] \
  #body
]

// One entry is one thing: its label never stays alone at a page foot.
#let timeline_entry(period, body, last: false) = block(
  breakable: false,
  stroke: (left: 3pt + line_rule),
  inset: (left: sp_3, top: sp_2, bottom: if last { sp_half } else { sp_3 }, right: 0pt),
  spacing: 0pt,
  below: if last { sp_2 } else { 0pt },
  width: 100%,
)[
  // Centre the dot on the rule (the rule sits on the block's left edge,
  // sp_3 left of the content) and on the label's first line.
  #place(left + top, dx: -sp_3 - 6pt, dy: -0.5pt)[
    #circle(radius: 6pt, fill: zh_white, stroke: 2.5pt + accent)
  ]
  #block(below: sp_half)[
    #text(11pt, weight: weight_black, fill: accent, font: heading_font)[#period]
  ]
  #body
]

// Left-aligned, upright and in Black: the design system has no centred text
// and no italic cut. Same bar as the tip.
#let key_statement(body) = _bar(text(weight: weight_black, fill: ink_text, body))
