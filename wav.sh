#!/bin/sh
python /home/alan/coding/_checkouts/mercussion/parser.py --midi < $1 > ~/coding/_checkouts/mercussion/testing/miditext/$1.miditext
~/downloads/midicomp-0.0.4/midicomp -c ~/coding/_checkouts/mercussion/testing/miditext/$1.miditext ~/coding/_checkouts/mercussion/testing/midi/$1.midi
timidity -c ~/composition/soundfont/timidity.cfg -Ow ~/coding/_checkouts/mercussion/testing/midi/$1.midi -o ~/coding/_checkouts/mercussion/testing/wav/$1.wav
