.PHONY : clean

pdf:
	./knit pdf
	pandoc -s -S --biblio idss-featurelist-roadmap.bib idss-featurelist-roadmap.md --template=xelatex-template.tex --latex-engine=xelatex -o idss-featurelist-roadmap.tex --natbib --number-sections --listings
	latexmk -pdf idss-featurelist-roadmap
	open -a /Applications/Skim.app idss-featurelist-roadmap.pdf


md:
	pandoc -s -S --biblio idss-featurelist-roadmap.bib idss-featurelist-roadmap.md -o idss-featurelist-roadmap.md

docx:
	./knit docx
	pandoc -s -S --biblio idss-featurelist-roadmap.bib idss-featurelist-roadmap.md --reference-docx=template.docx -o idss-featurelist-roadmap.docx



epub:
	./knit epub
	pandoc -s -S --biblio idss-featurelist-roadmap.bib idss-featurelist-roadmap.md -o idss-featurelist-roadmap.epub


clean:
	latexmk -CA
	rm -rf *.log *.bbl *.blg *.out *.md idss-featurelist-roadmap.docx idss-featurelist-roadmap.epub idss-featurelist-roadmap.pdf
