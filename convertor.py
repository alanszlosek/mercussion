class Convertor:
	def condense(self, score):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# for tenors, merge flam notes together

		# expand unison surface into simultaneous based on number of basses?

		# if timeSignature per measure is not specified, deduce into x/4
		basses = 'abcdef'
		if 'basses' in score:
			unison = basses[0: int(score['basses']) ]
		else:
			unison = basses[0:5]

		# annotate with durations
		for (instrument,music) in score['instruments'].items():
			dynamic = False 
			dynamicChange = False
			for measure in music:
				for beat in measure['beats']:
					# fix tenor flams
					if instrument == 'tenor':
						i = 0
						z = len(beat)
						# the note with the flam flag will have the modifiers we want
						while i < z: # for each note in the beat
							note = beat[i]
							if 'flam' in note and note['flam'] == True:
								note['flam'] = note['surface']
								note['surface'] = beat[ i+1 ]['surface']
								#print('del' + str(i+1))
								del beat[i+1]
								z -= 1
							else: # only advance if we didn't just delete a beat
								i += 1
					# end tenor-specific

					# convert bass unisons to simultaneous notes
					if instrument == 'bass':
						for note in beat:
							if 'surface' in note and note['surface'] == 'u':
								# how many basses should we expand to?
								note['surface'] = 'abcde'
					# end bass-specific

					# this is really geared toward midi output
					# annotate with durations
					duration = len(beat)
					for note in beat:
						# duration is the denominator of the fraction,
						# how much of the beat the note owns
						# 4 would be 1/4 of a beat, thus a 16th note
						note['duration'] = duration

					# condense rests
					i = 0
					z = len(beat)
					while i < z:
						j = i + 1
						if not j < z:
							i += 2
							continue
						a = beat[i]
						b = beat[j]
						if 'rest' in b:
							if type(a) == dict:
								a['duration'] /= 2
								del beat[j]
								i -= 1
								z -= 1
				
						i += 2
					# end condense rests

					# set dynamicChangeEnd
					for note in beat:
						if dynamicChange and 'dynamic' in note:
							note['dynamicChangeEnd'] = True
							dynamicChange = False
						if 'dynamicChange' in note:
							dynamicChange = True
						

		return score 

class MidiConvertor(Convertor):
	# will need to hard-code volume levels for crescendos and decrescendos

	def convert(self, score, settings):
		instrumentProgramMap = {
			"bass": "0",
			"cymbal": "3",
			"snare": "2",
			"tenor": "1"
		}
		instrumentVolumeMap = {
			"bass": "127",
			"cymbal": "127",
			"snare": "127",
			"tenor": "127"
		}
		noteMap = {
			# snare
			"h": "c6",
			"x": "d6",

			# bass and tenor
			"a": "e6",
			"b": "c6",
			"c": "a5",
			"d": "f5",
			"e": "d5"
		}
		volumeMap = {
			"P": 32, # pianissimo
			"M": 64, # mezzo-forte
			"F": 95, # forte
			"G": 127 # ff
		}

		if 'tempo' in score:
			tempo = 60000000 / int(score['tempo'])
		else:
			tempo = 500000

		# MFile format tracks division
		out = "MFile 1 " + str(len(score['instruments']) + 1) + " 384\n" # +1 tracks because of tempo track
		# tempo track
		out += "MTrk\n"
		out += "0 Tempo " + str(tempo) + "\n"
		out += "0 TimeSig 4/4 18 8\n"
		out += "TrkEnd\n"

		# set counter a second into the future for blank space padding

		channel = 1
		startingCounter = 30 # calculate how much time would yield a second
		flamPosition = -20 # calculate based on tempo
		accentIncrease = int(127/4)
		perBeat = 384

		for (instrument,music) in score['instruments'].items():
			volume = volumeMap['M']
			counter = startingCounter
			nextBeat = counter + perBeat

			channelString = str(channel)
	
			out += "MTrk\n"
			# map instrument to a channel
			out += "0 PrCh ch=" + channelString + " prog=" + instrumentProgramMap[instrument] + "\n"
			# set main track volume
			out += "0 Par ch=" + channelString + " con=7 val=" + instrumentVolumeMap[instrument] + "\n"
			# could set panning here too!

                        for measure in music:
                                for beat in measure['beats']:
					c1 = counter
					for note in beat:
						c2 = str(c1)
						if 'rest' in note:
							pass
						else:
							if 'flam' in note:
								#go back a bit, from current counter value
								pass
							
							# prepare volume
							if 'dynamic' in note:
								volume = volumeMap[ note['dynamic'] ]
							tempVolume = volume
							if 'accent' in note:
								tempVolume += accentIncrease # go up a quarter
								if tempVolume > 127:
									tempVolume = 127

							# expand diddle/tremolo
							if 'diddle' in note:
								pass

							for surface in note['surface']:
								out += c2 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(tempVolume) + "\n"
							# when do we turn off
							# divide
							c3 = str(c1 + (perBeat / note['duration']))
							for surface in note['surface']:
								# why do i sometimes see the note off volume at 64?
								out += c3 + " Off ch=" + channelString + " n=" + noteMap[ surface ] + " v=0\n"
								pass

							# i bet some cymbal notes we'll have to avoid turning off until we get an explicit choke note

						c1 += (perBeat / note['duration']) # how long does this note last?
					nextBeat += perBeat
					counter += perBeat
				# end beat loop
			# end measure loop
			out += "TrkEnd\n"

			channel += 1
		# end instrument loop
		return out

class LilypondConvertor(Convertor):
	# lilypond specific
	# inserts flam spacers in the rest of the score
	# fucking hate that i have to do this
	def flams(self, parsed):
		instruments = parsed['instruments'].keys()
		measure = 0
		beat = 0
		note = 0
		done = False

		flams = []

		while not done:
			measureNotFound = False
			beatNotFound = False
			foundFlam = False
			for instrument in instruments:
				print(instrument)
				# if we've gone past beats
				# if we've gone past measures
				if measure >= len(parsed['instruments'][ instrument ] ):
					measureNotFound = True
					print('measure not found: ' + str(measure) )
					continue
				if beat >= len( parsed['instruments'][ instrument ][ measure ]['beats'] ):
					beatNotFound = True
					print('beat not found: ' + str(beat) )
					continue
				notes = parsed['instruments'][ instrument ][ measure ]['beats'][ beat ]

				i = 0
				z = len(notes)
				while i < z:
					note = notes[ i ]
					if type(note) == dict:
						if 'flam' in note:
							foundFlam = True
							flams.append( (instrument, measure, beat, i) )
					i += 1

			# somehow fill in flam spacers

			if measureNotFound and beatNotFound:
				done = True
			elif measureNotFound:
				done = True
			elif beatNotFound:
				beat = 0
				measure += 1
			else:
				beat += 1
		
		print( repr( flams ))
		return {}
		return parsed

	def convert(self, parsed, settings={}):
		#a = self.flams(parsed)
		#return ''
		a = self.condense(parsed)
		#print( repr(a) )
		#return

		ret = '\\version "2.8.7"\n'

		# not sure if this would work with timidity
		ret += '#(define (myDynamics dynamic) (if (equal? dynamic "p") 0.20 (default-dynamic-absolute-volume dynamic)) (if (equal? dynamic "mf") 0.60 (default-dynamic-absolute-volume dynamic)) (if (equal? dynamic "f") 1.00 (default-dynamic-absolute-volume dynamic)))\n'

		# but this didn't work with timidity
		#ret += '#(define my-instrument-equalizer-alist \'())\n'
		#ret += '#(set! my-instrument-equalizer-alist\n'
		#ret += '\t(append\n'
		#ret += '\t\t\'(\n'
		#ret += '\t\t\t("electric grand" . (0.01 . 1.0))\n' # snare. this doesn't seem to work
		#ret += '\t\t\t("bright acoustic" . (0.01 . 1.0))\n' # bring tenor volume down?
		#ret += '\t\t\t("acoustic grand" . (0.01 . 1.0))\n' # bass
		#ret += '\t\t\t("honky-tonk" . (0.01 . 1.0))\n' # cymbal
		#ret += '\t\t)\n'
		#ret += '\t\tmy-instrument-equalizer-alist\n'
		#ret += '\t)\n'
		#ret += ')\n'
		#ret += '#(define (my-instrument-equalizer s)\n'
		#ret += '\t(let ((entry (assoc s my-instrument-equalizer-alist)))\n'
		#ret += '\t(if entry\n'
		#ret += '(cdr entry))))\n\n'

		if settings['fixFlams']:
			ret += 'appoggiatura = #(define-music-function (parser location grace main) (ly:music? ly:music?) (let* ( (maindur (ly:music-length main))  (grace-orig-len (ly:music-length grace)) (numerator (ly:moment-main-numerator maindur)) (factor (ly:make-moment 1 15)) ) (ly:music-compress grace factor) (ly:music-compress main (ly:moment-sub (ly:make-moment 1 1) factor))  (set! (ly:music-property grace \'elements) (append (ly:music-property grace \'elements) (list (make-music \'SlurEvent \'span-direction -1)) ) ) (set! (ly:music-property main \'elements) (append (ly:music-property main \'elements) (list (make-music \'SlurEvent \'span-direction 1)) ) ) (make-sequential-music (list grace main)) ) )\n\n'

		ret += 'flam = {\n'
		ret += '\t\\override Stem #\'length = #4\n'
		#print('\t\\acciaccatura c\'\'8\n'
		#print('\t\\grace c\'\'8\n'
		ret += '\t\\appoggiatura c\'\'8 \n'
		ret += '\t\\revert Stem #\'length\n'
		ret += '}\n\n'

		ret += '\\header {\n'
		if 'title' in a:
			print('title')
			ret += '\ttitle="' + a['title'] + '"\n'
		if 'author' in a:
			ret += '\tauthor="' + a['author'] + '"\n'
			ret += '\tcopyright = \\markup {"Copyright" \\char ##x00A9 "' + a['author'] + '"}\n'
		ret += '}\n\n'

		ret += '\\score {\n'
		ret += '\t<<\n'

		mapping = {
			'h': 'c\'\'',
			'x': 'c\'\'', # rim shot

			'a': 'e\'\'',
			'b': 'c\'\'',
			'c': 'a\'',
			'd': 'f\'',
			'e': 'd\'',
			'f': 'b',
	
			'r': 'r', # rest
			'u': 'b\'', # unison b'
	
			# dynamics
			'P': '\\p',
			'M': '\\mf',
			'F': '\\f',
			'G': '\\ff',
	
			'<': '\\<',
			'>': '\\>',
			':': '\\!'
		}

		# annotate with flamRest placeholders

		# set this flag when we encounter one of them
		# unset it when we encounter the first dynamic that's not one
		crescendoDecrescendo = False
		dynamic = 'M'

		for (instrument,music) in a['instruments'].items():

			if instrument == 'snare':
				ret += '\t% Snare\n'
				ret += '\t\\new Staff {\n'
				ret += '\t\t\\set Staff.midiInstrument = "electric grand"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Snare "\n'
				ret += '\t\t\\set Staff.midiMinimumVolume = #0.01\n'
				ret += '\t\t\\set Staff.midiMaximumVolume = #0.60\n'

				#self.beaming()
				#print('\\time ' + self.timeSignature)
			elif instrument == 'tenor':
				ret += '\t% Tenor\n'
				ret += '\t\\new Staff {\n'
				ret += '\t\t\\set Staff.midiInstrument = "bright acoustic"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Tenor "\n'
				ret += '\t\t\\set Staff.midiMinimumVolume = #0.01\n'
				ret += '\t\t\\set Staff.midiMaximumVolume = #0.90\n'
			elif instrument == 'bass':
				ret += '\t% Bass\n'
				ret += '\t\\new Staff {\n'
				ret += '\t\t\\set Staff.midiInstrument = "acoustic grand"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Bass "\n'
				ret += '\t\t\\set Staff.midiMinimumVolume = #0.01\n'
				ret += '\t\t\\set Staff.midiMaximumVolume = #1.00\n'
			elif instrument == 'cymbal':
				ret += '\t% Cymbals\n'
				ret += '\t\\new Staff {\n'
				ret += '\t\t\\set Staff.midiInstrument = "honky-tonk"\n'
				ret +='\t\t\\set Staff.instrumentName = #"Cymbals "\n'
				ret += '\t\t\\set Staff.midiMinimumVolume = #0.01\n'
				ret += '\t\t\\set Staff.midiMaximumVolume = #0.80\n'

			# this doesn't seem to work
			#ret += '\t\t#(set! absolute-volume-alist\n'
			#ret += '\t\t\t(append\n'
			#ret += '\t\t\t\t\'(\n'
			#ret += '\t\t\t\t\t("ff" . 1.00)\n'
			#ret += '\t\t\t\t\t("f" . 0.70)\n'
			#ret += '\t\t\t\t\t("mf" . 0.40)\n'
			#ret += '\t\t\t\t\t("p" . 0.10)\n'
			#ret += '\t\t\t\t)\n'
			#ret += '\t\t\t\tabsolute-volume-alist\n'
			#ret += '\t\t\t)\n'
			#ret += '\t\t)\n'

			# this didn't work with timidity
			#ret += '\t\t\\set Score.instrumentEqualizer = #my-instrument-equalizer\n'
			ret += '\t\t\\stemUp\n'

			iMeasure = 1
			for measure in music:
				beats = len(measure['beats'])
				# output measure's time signature
				for beat in measure['beats']:
					for note2 in beat:
						notes = []
						if type(note2) == list:
							#print('simul')
							notes = note2
							ret += '<< '
						elif type(note2) == dict:
							#print('note')
							notes.append(note2)
						
						for note in notes:
							# i actually think dynamics are supposed to go after notes. ugh
							# new dynamic:
							if 'dynamic' in note and crescendoDecrescendo:
								# end it
								crescendoDecrescendo = False
								ret += '\! '

							if 'flam' in note:
								if instrument == 'snare':
									ret += '\\override Stem #\'length = #4 \\appoggiatura c\'\'8 \\revert Stem #\'length \stemUp '
								else:
									ret += '\\override Stem #\'length = #4 \\appoggiatura ' + mapping[ note['flam'] ] + '8 \\revert Stem #\'length \stemUp '

							elif 'flamRest' in note:
								ret += '\\appoggiatura r8 '

							# note or rest?
							if 'rest' in note:
								ret += 'r' + str(note['duration'])
							else:
								ret += mapping[ note['surface'] ] + str(note['duration'])

							# diddle?
							# check flag for whether to expand tremolos
							if 'diddle' in note:
								ret += ':' + str(note['duration']*2)

							# fours?
							if 'fours' in note:
								ret += ':' + str(note['duration']*4)

							if 'decrescendo' in note:
								crescendoDecrescendo = True
								ret += mapping['>'] + ' '
							if 'dynamic' in note:
								ret += mapping[ note['dynamic'] ] + ' '
							# crescendo after the dynamic because it specifies the starting dynamic
							if 'crescendo' in note:
								crescendoDecrescendo = True
								ret += mapping['<'] + ' '

							# should note be accented?
							if 'accent' in note:
								ret += ' \\accent'

						if type(note2) == list:
							ret += '>>'
						ret += ' '

				ret += ' \n '
				if iMeasure == 4:
					ret += ' \\break '
					iMeasure = 1
				else:
					iMeasure += 1
		
			ret += '}\n'

		ret += '>>\n'
		ret += '\t\\layout {\n'
		#print('\t\tindent = 0')
		ret += '\t}\n'
		ret += '\t\\midi {\n'
		ret += '\t\t\\context {\n'
		ret += '\t\t\t\\Score\n'
		ret += '\t\t\ttempoWholesPerMinute = #(ly:make-moment 120 4)\n'
		ret += '\t\t\tmidiMinimumVolume = #0.05\n'
		ret += '\t\t\tmidiMaximumVolume = #1.00\n'
		ret += '\t\t}\n'
		ret += '\t}\n'
		ret += '}\n'
		return ret
