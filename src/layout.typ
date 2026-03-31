#import "../theme/zh-mba.typ": *

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

    #v(2.8cm)

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

    #v(2.8cm)

    #line(length: 60pt, stroke: 2.5pt + zh_cyan)

    #v(12pt)

    #text(11pt, fill: zh_black_80, font: body_font)[#ipa_line]
    #v(4pt)
    #text(10pt, fill: zh_black_60, font: body_font)[
      Version #version
    ]
  ]

  #v(1fr)

  // ── Bottom: Spickel (45° flag triangle) ─────────────────────────────────
  #place(bottom + left)[
    #polygon(
      fill: zh_cyan,
      (0pt, 100% - 0pt),
      (0pt, 100% - 60mm),
      (60mm, 100% - 0pt),
    )
  ]

  #place(bottom + right, dx: -2.6cm, dy: -18mm)[
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
  )
  set par(justify: true, leading: 0.82em, spacing: 1.2em, first-line-indent: 0pt)

  // ── Headings ────────────────────────────────────────────────────────────
  set heading(numbering: "1.1.1", bookmarked: true)

  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(0.4em)
    let num = counter(heading).get()
    let is_numbered = it.numbering != none and num.at(0, default: 0) > 0
    block(below: 1.2em)[
      #if is_numbered {
        text(32pt, weight: "bold", fill: zh_blaugrau, font: heading_font)[
          #counter(heading).display("1")
        ]
        v(-4pt)
      }
      #text(20pt, weight: "bold", fill: zh_dunkelblau, font: heading_font)[
        #it.body
      ]
      #v(4pt)
      #line(length: 40pt, stroke: 2pt + zh_cyan)
    ]
  }

  show heading.where(level: 2): it => {
    v(1em)
    block(below: 0.7em)[
      #text(10pt, weight: "bold", fill: zh_blau, font: heading_font)[
        #counter(heading).display("1.1")
      ]
      #h(6pt)
      #text(13pt, weight: "bold", fill: zh_black_100, font: heading_font)[
        #it.body
      ]
    ]
  }

  show heading.where(level: 3): it => {
    v(0.6em)
    block(below: 0.5em)[
      #text(9pt, weight: "semibold", fill: zh_black_40, font: heading_font)[
        #counter(heading).display("1.1.1")
      ]
      #h(5pt)
      #text(11pt, weight: "semibold", fill: zh_black_60, font: heading_font)[
        #it.body
      ]
    ]
  }

  // ── Lists ───────────────────────────────────────────────────────────────
  set list(marker: text(fill: zh_blau)[•])
  set enum(numbering: n => text(weight: "bold", fill: zh_blau)[#n.])

  // ── Links ───────────────────────────────────────────────────────────────
  show link: set text(fill: zh_blau)

  // ── Tables ──────────────────────────────────────────────────────────────
  set table(
    stroke: none,
    inset: 8pt,
    fill: (_, y) => if y == 0 { zh_blaugrau } else if calc.odd(y) { zh_black_5 },
  )
  show table: set text(size: 9.5pt)
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
    margin: (left: 2.6cm, right: 2.2cm, top: 2.8cm, bottom: 2.4cm),
    header: context {
      set text(8.5pt, fill: zh_black_60, font: body_font)
      running_header
      v(5pt)
      line(length: 100%, stroke: 0.4pt + zh_blau)
    },
    footer: context {
      set text(8.5pt, fill: zh_black_60, font: body_font)
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
