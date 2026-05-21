#import "../theme/zh-mba.typ": zh_blau, zh_dunkelblau, zh_cyan, zh_soft_blau, zh_black_100, zh_black_80, zh_black_60, zh_black_40, zh_black_20, zh_black_5, body_font, heading_font

// ═══════════════════════════════════════════════════════════════════════════
// Cover page
// ═══════════════════════════════════════════════════════════════════════════

#let cover_page(
  doc_title: [],
  audience: [],
  ipa_line: [],
  version: "",
  org_line: [],
  mba_line: [],
) = page(
  margin: 0pt,
  header: none,
  footer: none,
)[
  // ── Top accent bar ──────────────────────────────────────────────────────
  #rect(fill: zh_blau, width: 100%, height: 6mm)

  #v(1fr)

  // ── Title block ─────────────────────────────────────────────────────────
  #pad(x: 2.6cm)[
    #set par(justify: false, leading: 0.65em)

    #text(
      9pt,
      fill: zh_black_60,
      font: body_font,
      weight: "medium",
      tracking: 0.6pt,
    )[#upper(org_line)]

    #v(6pt)

    #text(
      9pt,
      fill: zh_black_40,
      font: body_font,
    )[#mba_line]

    #v(2cm)

    #text(
      40pt,
      weight: "bold",
      fill: zh_black_100,
      font: heading_font,
    )[#doc_title]

    #v(8pt)

    #text(
      14pt,
      fill: zh_blau,
      weight: "medium",
      font: body_font,
    )[#audience]

    #v(2cm)

    #line(length: 60pt, stroke: 2.5pt + zh_cyan)

    #v(12pt)

    #text(11pt, fill: zh_black_80, font: body_font)[#ipa_line]
    #v(2pt)
    #text(9pt, fill: zh_black_60, font: body_font)[
      Version #version
    ]
  ]

  #v(1fr)

  // ── Bottom: Spickel (45° flag triangle) ─────────────────────────────────
  #place(bottom + left)[
    #polygon(
      fill: zh_cyan,
      (0pt, 100% - 0pt),
      (0pt, 100% - 50mm),
      (50mm, 100% - 0pt),
    )
  ]

]

// ═══════════════════════════════════════════════════════════════════════════
// Body wrapper — sets all global styles for the document interior.
// ═══════════════════════════════════════════════════════════════════════════

#let matter(
  version: "",
  running_footer_title: [],
  running_header: [],
  it,
) = {
  // ── Text defaults ───────────────────────────────────────────────────────
  set text(
    font: body_font,
    size: 10.5pt,
    fill: zh_black_80,
    lang: "de",
    region: "ch",
    hyphenate: true,
    features: ("ss07": 1, "ss08": 1, "cv03": 1, "cv04": 1, "cv10": 1),
  )
  set par(justify: true, leading: 0.80em, spacing: 1.3em, first-line-indent: 0pt)

  // ── Headings ────────────────────────────────────────────────────────────
  set heading(numbering: "1.1.1", bookmarked: true)

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(32pt)
    let num = counter(heading).get()
    let is_numbered = it.numbering != none and num.at(0, default: 0) > 0
    block(below: 1.2em)[
      #if is_numbered {
        text(24pt, weight: "bold", fill: zh_black_20, font: heading_font)[
          #counter(heading).display("1")
        ]
        v(-4pt)
      }
      #text(20pt, weight: "bold", fill: zh_dunkelblau, font: heading_font)[
        #it.body
      ]
      #v(4pt)
      #line(length: 32pt, stroke: 2pt + zh_cyan)
    ]
  }

  show heading.where(level: 2): it => {
    v(1.2em)
    line(length: 100%, stroke: 0.5pt + zh_black_20)
    v(0.6em)
    block(below: 0.8em)[
      #text(10pt, weight: "bold", fill: zh_blau, font: heading_font)[
        #counter(heading).display("1.1")
      ]
      #h(8pt)
      #text(12pt, weight: "black", fill: zh_black_100, font: heading_font)[
        #it.body
      ]
    ]
  }

  show heading.where(level: 3): it => {
    v(0.8em)
    block(below: 0.5em)[
      #text(9pt, weight: "bold", fill: zh_blau, font: heading_font)[
        #counter(heading).display("1.1.1")
      ]
      #h(4pt)
      #text(11pt, weight: "bold", fill: zh_black_80, font: heading_font)[
        #it.body
      ]
    ]
  }

  // ── Lists ───────────────────────────────────────────────────────────────
  set list(marker: text(fill: zh_blau)[--])
  set enum(numbering: n => text(weight: "bold", fill: zh_blau)[#n.])

  // ── Links ───────────────────────────────────────────────────────────────
  show link: set text(fill: zh_blau)

  // ── Tables ──────────────────────────────────────────────────────────────
  set table(
    stroke: none,
    inset: 8pt,
    fill: (_, y) => if y == 0 { zh_soft_blau } else if calc.odd(y) { zh_black_5 },
  )
  show table: set text(size: 9pt)
  show table.cell.where(y: 0): set text(weight: "bold", fill: zh_dunkelblau)
  // Horizontal rules only: below header + at bottom
  show table: it => block(
    width: 100%,
    clip: true,
    {
      set table(stroke: (
        top: 1.2pt + zh_blau,
        bottom: 0.6pt + zh_black_20,
        left: none,
        right: none,
        rest: none,
      ))
      it
    },
  )

  // ── Outline (TOC) ──────────────────────────────────────────────────────
  show outline.entry: it => {
    if it.level == 1 {
      v(0.4em)
      strong(it)
    } else {
      it
    }
  }

  // ── Page layout ────────────────────────────────────────────────────────
  set page(
    paper: "a4",
    margin: (left: 3cm, right: 3cm, top: 2.8cm, bottom: 2.4cm),
    header: context {
      set text(8.5pt, fill: zh_black_60, font: body_font)
      line(length: 100%, stroke: 0.8pt + zh_cyan)
      v(5pt)
      running_header
      v(5pt)
      line(length: 100%, stroke: 0.3pt + zh_black_20)
    },
    footer: context {
      set text(8pt, fill: zh_black_60, font: body_font)
      line(length: 100%, stroke: 0.3pt + zh_black_20)
      v(6pt)
      grid(
        columns: (1fr, auto, 1fr),
        align(left)[#running_footer_title],
        align(center)[#counter(page).display("1 / 1", both: true)],
        align(right)[Version #version],
      )
    },
  )

  it
}
