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

// ── Tip / callout backgrounds ──────────────────────────────────────────────
#let zh_bg_tip     = rgb("#FFF8E6")
#let zh_stroke_tip = rgb("#CC9900")

// ── Typography ─────────────────────────────────────────────────────────────
#let body_font    = "Inter"
#let heading_font = "Inter Display"

// ── Reusable components ────────────────────────────────────────────────────

#let callout(body) = block(
  fill: zh_soft_blau,
  stroke: (left: 4pt + zh_blau, top: 0.5pt + zh_blaugrau, right: 0.5pt + zh_blaugrau, bottom: 0.5pt + zh_blaugrau),
  radius: (right: 3pt),
  inset: (left: 16pt, y: 12pt, right: 12pt),
  spacing: 1.2em,
  width: 100%,
  body,
)

#let tip_block(body) = block(
  fill: zh_bg_tip,
  stroke: (left: 4pt + zh_stroke_tip, top: 0.5pt + zh_stroke_tip.transparentize(60%), right: 0.5pt + zh_stroke_tip.transparentize(60%), bottom: 0.5pt + zh_stroke_tip.transparentize(60%)),
  radius: (right: 3pt),
  inset: (left: 16pt, y: 12pt, right: 12pt),
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
  stroke: (left: 3pt + zh_black_20),
  inset: (left: 24pt, top: 16pt, bottom: if last { 4pt } else { 20pt }, right: 0pt),
  spacing: 0pt,
  width: 100%,
)[
  #place(left + top, dx: -27pt, dy: 2pt)[
    #circle(radius: 6pt, fill: white, stroke: 2.5pt + zh_blau)
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
  inset: (x: 24pt, y: 8pt),
)[
  #line(length: 100%, stroke: 0.6pt + zh_black_10)
  #v(0.5em)
  #align(center)[
    #text(11pt, style: "italic", fill: zh_black_60)[#body]
  ]
  #v(0.5em)
  #line(length: 100%, stroke: 0.6pt + zh_black_10)
]
