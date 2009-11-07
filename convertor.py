class Convertor:
	def __init__(self):
		i = 0

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


	def condense(self, parsed):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# for tenors, merge flam notes together

		# annotate with durations
		for (instrument,music) in parsed['instruments'].items():
			dynamic = ''
			for measure in music:
				for beat in measure['beats']:
					# fix tenor flams
					if instrument == 'tenor':
						i = 0
						z = len(beat)
						while i < z:
							note = beat[i]
							if type(note) == dict and 'flam' in note and note['flam'] == True:
								beat[ i+1 ]['flam'] = note['surface']
								del beat[i]
								z -= 1

							i += 1

					notes = len(beat)
					tuple = False
					if notes == 6 or notes == 5:
						duration = 16
						tuple = True
					elif notes == 3:
						duration = 8
						tuple = True
					else:
						duration = 4 * notes

					# annotate with durations
					for note in beat:
						if type(note) == list:
							#print('list')
							for simultaneous in note:
								simultaneous['duration'] = duration
								#print(simultaneous['surface'])
						elif type(note) == dict:
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
						if type(b) == list:
							j = 0
						elif type(b) == dict:
							if 'rest' in b:
								if type(a) == dict:
									a['duration'] /= 2
									del beat[j]
									i -= 1
									z -= 1
								
				
						i += 2

					# set dynamics on accents and next note
					for note in beat:
						if type(note) == dict:
							if 'dynamic' in note:
								dynamic = note['dynamic']
							elif 'accent' in note:
								if dynamic:
									note['dynamic'] = self.accentFrom(dynamic)
								else: # default to mf
									note['dynamic'] = self.accentFrom('M')
									dynamic = 'M'
							elif dynamic:
								note['dynamic'] = dynamic
								dynamic = ''
								
						

		return parsed

	def toLilypond(self, parsed, settings={}):
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

	def accentFrom(self, dynamic):
                if dynamic == 'P':
                        return 'M'
                elif dynamic == 'M':
                        return 'F'
                elif dynamic == 'F':
                        return 'G'
                elif dynamic == 'G':
                        return 'G'

