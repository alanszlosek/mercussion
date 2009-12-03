#!/bin/sh
cd testing
for file in *.music
do
	echo "Compiling $file"
	python ../parser.py --midi < $file > miditext/$file.miditext
	~/downloads/midicomp-0.0.4/midicomp -c miditext/$file.miditext midi/$file.midi
	timidity -c ~/composition/soundfont/timidity.cfg -Ow midi/$file.midi -o wav/$file.wav
	echo "done"
done
