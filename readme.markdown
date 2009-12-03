INTRODUCTION
====

This is the next generation of my [lilyperc project](http://github.com/alanszlosek/lilyperc).

I've redesigned my marching percussion language to be more concise and thus, less tedious to type. You no longer have to specify note durations; whether a note is a 16th note or an 8th note can be deduced by how many notes are present within a given beat.

This project is getting much better! We're no longer depending on lilypond for MIDI output: we have more control; can make flams play back properly (lilypond is screwy). We could also better suited to swap out lilypond for something that creates PDFs better in the future.


USAGE
====

This will change, but for now:

	python parser.py --lilypond MUSICFILE > MUSICFILE.ly
