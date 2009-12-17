#!/bin/sh
python /home/alan/coding/_checkouts/mercussion/parser.py --midi < $1 > /home/alan/coding/_checkouts/mercussion/testing/miditext/$1.miditext
~/downloads/midicomp-0.0.4/midicomp -c /home/alan/coding/_checkouts/mercussion/testing/miditext/$1.miditext /home/alan/coding/_checkouts/mercussion/testing/midi/$1.midi
