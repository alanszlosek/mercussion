#!/bin/sh
python ~/coding/projects/mercussion/parser.py --lilypond < $1 > ~/coding/projects/mercussion/testing/ly/$1.ly
lilypond -f pdf -o ~/coding/projects/mercussion/testing/pdf/$1 ~/coding/projects/mercussion/testing/ly/$1.ly
