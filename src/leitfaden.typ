#import "../theme/zh-mba.typ": zh_dunkelblau
#import "layout.typ": cover_page, matter
#import "meta.typ": version, org_line, mba_line

#cover_page(
  doc_title: [QV-Leitfaden],
  audience: [für Informatikerinnen und Informatiker],
  ipa_line: [Individuelle Praktische Arbeit (IPA)],
  version: version,
  org_line: org_line,
  mba_line: mba_line,
)

#matter(
  version: version,
  running_footer_title: [QV-Leitfaden],
  running_header: [Prüfungskommission 19 · Informatikberufe Kanton Zürich],
)[
  #outline(title: [Inhaltsverzeichnis], depth: 3)

  #include "changelog.typ"
  #pagebreak()

  #include "chapters/ch01.typ"
  #include "chapters/ch02.typ"
  #include "chapters/ch03.typ"
  #include "chapters/ch04.typ"
  #include "chapters/ch05.typ"
  #include "chapters/ch06.typ"

  #v(3em)
  #align(center)[
    #text(13pt, weight: "bold", fill: zh_dunkelblau)[
      Wir wünschen ein gutes Gelingen der IPA!
    ]
  ]
]
