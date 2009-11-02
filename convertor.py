class Convertor:
	def __init__(self):
		i = 0

	def condense(self, parsed):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# annotate with durations
		for instrument in parsed['instruments'].values():
			for measure in instrument:
				for beat in measure['beats']:
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
							print('list')
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

	def toLilypond(self, parsed):
		a = self.condense(parsed)
		ret = ''

		# duplicate flam placeholders

		instruments = a['instruments']
		snare = instruments['snare']
		for measure in snare:
			beats = len(measure['beats'])
			for beat in measure['beats']:
				if tuple:
					i = 0
				for note in beat:
					if note is list:
						i = 0
					else:
						i = 0
				if tuple:
					i = 0
		return a
