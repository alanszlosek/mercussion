INTRODUCTION
====

This project allows tech-savvy marching percussion composers to input music FAST and generate audio, PDF and MusicXML versions of their compositions. It uses the [Python 3](http://python.org) programming language, [midicomp](http://midicomp.opensrc.org) and [lilypond](http://lilypond.org) to get the job done. For playback and generating audio files I use [this soundfont](http://www.drumputer.com/soundfont/) and the [Timidity++](http://timidity.sourceforge.net/) MIDI player.

My marching percussion language is designed to be concise, facilitating swift input. You do not have to specify note durations; whether a note is a 16th note or an 8th note can be deduced by how many notes are present within a given beat. Beats (as in "4 beats per measure in 4/4 time") are separated by spaces.

This project is getting much better! We're no longer depending on lilypond for MIDI output: we have more control; can make flams play back properly (lilypond is screwy). We could also better suited to swap out lilypond for something that creates PDFs better in the future.


USAGE
====

For notation examples see this [wiki page](http://wiki.github.com/alanszlosek/mercussion/notation)

This will change, but for now:

Print internal data structure for input:

	python parser.py < MUSICFILE

Output to lilypond format:

	python parser.py --lilypond < MUSICFILE > MUSICFILE.ly

Midi doesn't work natively. I make use of the [midicomp project](http://midicomp.opensrc.org/) and text-based MIDI files, so you'll need to use that project for the time being:

	python parser.py --midi < MUSICFILE > MUSICFILE.miditext

HISTORY
====

I have this little venture I've dubbed [Flam Swiss](http://www.flamswiss.com), wherein I'm rekindling some of my high school 
creativity. During those years I wrote music for (and played in) our marching band's drumline. In early 2009 I decided to start seriously composing marching percussion music again, and planned to do it with the help of a computer. This project is the main tool that enables me to do that.

The main goal of Flam Swiss is to provied high school drumlines with new music to play.
