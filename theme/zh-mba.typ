// ═══════════════════════════════════════════════════════════════════════════
// Kanton Zürich — Design Tokens
// ═══════════════════════════════════════════════════════════════════════════
//
// Official sources:
//   Farben:      zh.ch/…/designsystem/design-grundlagen/farben.html
//   Typografie:  zh.ch/…/designsystem/design-grundlagen/typografie.html
//   CD Manual:   zh.ch/…/kantonale-verwaltung/corporatedesign.html
//
// Typography follows the canton's migration from Helvetica Now → Inter.
// Inter (SIL OFL) ships in assets/fonts/inter/.

// ── Accent colours ─────────────────────────────────────────────────────────
#let zh_blau       = rgb("#0070B4")
#let zh_dunkelblau = rgb("#00407C")
#let zh_cyan       = rgb("#009EE0")

// ── Soft / background colours ──────────────────────────────────────────────
#let zh_soft_blau  = rgb("#EDF5FA")
#let zh_blaugrau   = rgb("#E0E8EE")

// ── Grey scale (official tokens) ───────────────────────────────────────────
#let zh_black_100  = rgb("#000000")
#let zh_black_80   = rgb("#333333")
#let zh_black_60   = rgb("#666666")
#let zh_black_40   = rgb("#949494")
#let zh_black_20   = rgb("#CCCCCC")
#let zh_black_10   = rgb("#F0F0F0")
#let zh_black_5    = rgb("#F7F7F7")

// ── Functional status colours ──────────────────────────────────────────────
#let zh_rot        = rgb("#D93C1A")
#let zh_gruen      = rgb("#1A7F1F")

// ── Tip / callout backgrounds ──────────────────────────────────────────────
#let bg_tip        = rgb("#FFF8E6")
#let stroke_tip    = rgb("#CC9900")

// ── Typography ─────────────────────────────────────────────────────────────
#let body_font    = "Inter"
#let heading_font = "Inter Display"

// ── Reusable components ────────────────────────────────────────────────────

#let callout(body) = block(
  fill: zh_soft_blau,
  stroke: (left: 3pt + zh_blau),
  radius: (right: 3pt),
  inset: (left: 14pt, y: 10pt, right: 12pt),
  spacing: 1.2em,
  width: 100%,
  body,
)

#let tip_block(body) = block(
  fill: bg_tip,
  stroke: (left: 3pt + stroke_tip),
  radius: (right: 3pt),
  inset: (left: 14pt, y: 10pt, right: 12pt),
  spacing: 1.2em,
  width: 100%,
  [*Tipp* #sym.dash.em #body],
)

#let term_block(label, body) = block(
  spacing: 1.4em,
  width: 100%,
)[
  #text(weight: "semibold", fill: zh_dunkelblau)[#label] \
  #body
]

#let timeline_entry(period, body, last: false) = block(
  stroke: (left: 3pt + zh_blaugrau),
  inset: (left: 28pt, top: 14pt, bottom: if last { 4pt } else { 20pt }, right: 0pt),
  spacing: 0pt,
  width: 100%,
)[
  #place(left + top, dx: -31.5pt, dy: 2pt)[
    #circle(radius: 5pt, fill: white, stroke: 2.5pt + zh_blau)
  ]
  #block(below: 4pt)[
    #text(11pt, weight: "bold", fill: zh_dunkelblau, font: heading_font)[#period]
  ]
  #body
]

#let key_statement(body) = block(
  above: 1.4em,
  below: 1.4em,
  width: 100%,
  inset: (x: 2em, y: 0.6em),
)[
  #line(length: 100%, stroke: 0.6pt + zh_black_20)
  #v(0.5em)
  #align(center)[
    #text(11.5pt, style: "italic", fill: zh_black_60)[#body]
  ]
  #v(0.5em)
  #line(length: 100%, stroke: 0.6pt + zh_black_20)
]
