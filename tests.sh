#!/bin/sh
cd testing
for file in *.music
do
	echo "Compiling $file"
	python ../parser.py --midi < $file > miditext/$file.miditext
	python ../parser.py --lilypond < $file > ly/$file.ly
	~/downloads/midicomp-0.0.4/midicomp -c miditext/$file.miditext midi/$file.midi
	timidity -c ~/composition/soundfont/timidity.cfg -Ow midi/$file.midi -o wav/$file.wav
	cd pdf
	lilypond --pdf ../ly/$file.ly
	rm *.ps
	cd ..
	echo "done"
done
