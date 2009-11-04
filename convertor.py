class Convertor:
	def __init__(self):
		i = 0

	def condense(self, parsed):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# for tenors, merge flam notes together

		# annotate with durations
		for (instrument,music) in parsed['instruments'].items():
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
						

		return parsed

	def toLilypond(self, parsed, settings={}):
		a = self.condense(parsed)
		#print( repr(a) )
		#sys.exit()
		ret = ''
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

		for (instrument,music) in a['instruments'].items():
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
							# new dynamic:
							if 'dynamic' in note:
								ret += mapping[ note['dynamic'] ] + ' '

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
							if 'diddle' in note:
								ret += ':' + str(note['duration']*2)

							# fours?
							if 'fours' in note:
								ret += ':' + str(note['duration']*4)

							# should note be accented?
							if 'accent' in note:
								ret += ' \\accent'
						if type(note2) == list:
							ret += '>>'
						ret += ' '

				ret += ' | '
		return ret
