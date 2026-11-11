#import "layout.typ": cover_page, matter
#import "meta.typ": version, org_line, mba_line

#set document(title: "QV-Leitfaden", author: "Prüfungskommission 19 · Informatikberufe Kanton Zürich")

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
  running_header: org_line,
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

]
