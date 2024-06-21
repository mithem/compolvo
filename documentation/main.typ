#set document(title: "Compolvo Dokumentation")

#set text(lang: "de")

#let current_heading = context [
  #query(selector(heading.where(level: 1)).before(here())).last().body
]

#set page(numbering: "1", footer: context [
  compolvo - #current_heading
  #h(1fr)
  #counter(page).display("1/1", both: true)
])

#set par(justify: true)

#set heading(numbering: "1.1.1")

#align(center, text(24pt)[
  *Compolvo Dokumentation*
])

#v(5em)

#outline(
  depth: 2,
  indent: auto,
)


#pagebreak()

#include("projektdaten.typ")
#include("marktanalyse.typ")
#pagebreak()
#include("anforderungen.typ")
#pagebreak()
#include("architektur.typ")
#pagebreak()
#include("user_guide.typ")
#pagebreak()

#heading("Abbildungsverzeichnis", numbering: none)
#outline(
  target: figure.where(kind: image),
  title: none
)