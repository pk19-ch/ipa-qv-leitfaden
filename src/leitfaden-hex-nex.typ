#import "layout.typ": cover_page, matter
#import "meta.typ": version, org_line, mba_line

#cover_page(
  doc_title: [QV-Leitfaden],
  audience: [
    für Hauptexpertinnen und Hauptexperten (HEX) \
    sowie Nebenexpertinnen und Nebenexperten (NEX)
  ],
  ipa_line: [Ergänzung zum allgemeinen QV-Leitfaden · Individuelle Praktische Arbeit (IPA)],
  version: version,
  org_line: org_line,
  mba_line: mba_line,
)

#matter(
  version: version,
  running_footer_title: [QV-Leitfaden HEX/NEX],
  running_header: [Prüfungskommission 19 · Informatikberufe Kanton Zürich],
)[
  #outline(title: [Inhaltsverzeichnis], depth: 3)

  #include "changelog.typ"
  #pagebreak()

  #include "body-hex-nex.typ"
]
