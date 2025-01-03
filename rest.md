/pdf/extract
input: .pdf
output: text

/topics
input: text
output: topic[]

/topics/summarize
input: topic[]
output: topic[12]

/latex
input: topic[12]
output: .latex file

/pdf
input: .tex file
output: .pdf file