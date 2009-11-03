INTRODUCTION
----

This is the next generation of my lilyperc project (http://github.com/alanszlosek/lilyperc).

I've redesigned my marching percussion language to be more concise and thus, less tedious to type. You no longer have to specify note durations; whether a note is a 16th note or an 8th note can be deduced by how many notes are present within a given beat.

It's still a work in progress, so I don't have any examples to show just yet. The parser works, but outputting in lilypond format is incomplete.

USAGE
----

This will change, but for now:

python parser.py --lilypond MUSICFILE > MUSICFILE.ly
