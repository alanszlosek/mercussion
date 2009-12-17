import sys
from lexer import *
from convertor import *

# what i'd like is for each method to return a data structure
# or empty if there were no matches
# what do i do when input is exhausted?

class Parser:
	# defines
	NotFound = -1

	state = []
	token = ''
	value = ''
	tree = []

	def __init__(self, tokens, settings={}):
		self.tokens = tokens
		self.token, self.value = self.tokens.next()
		self.debug = ('debug' in settings)
		self.debug2 = ('debug2' in settings)

	def die(self, message):
		sys.stderr.write(message)
		sys.exit()

	def accept(self, a):
		if self.token == a:
			if self.debug2:
				sys.stderr.write('Accept ' + self.token + ':' + self.value + "\n")
			# self.next() might not have anymore input
			self.next()
			return True
		return False

	def expect(self, a):
		if self.accept(a):
			return True
		self.die('Unexpected token')
		return False

	def next(self):
		try:
			self.token,self.value = self.tokens.next()
		except StopIteration:
			self.token = self.value = False
			if self.debug:
				sys.stderr.write('No more\n')
			return False

		except UnknownTokenError:
			self.token = self.value = False
			self.die('Unknown token')
			return False
		if self.debug:
			sys.stderr.write('At ' + self.token + ':' + self.value + "\n")
		return True


	def score(self):
		ret = {}
		a = self.details()
		if len(a):
			ret.update(a)
		a = self.instruments()
		ret['instruments'] = a
		return ret

	def details(self):
		ret = {}
		while self.token == 'detail':
			detail = self.value.replace(':', '')
			self.accept('detail')
			while self.token == 'space':
				self.accept('space')
			ret[ detail ] = self.value.replace('"', '')
			self.accept('string')
			while self.token == 'space':
				self.accept('space')
		return ret

	def instruments(self):
		if self.debug:
			sys.stderr.write('In instruments()\n')
		ret = {}
		while self.token == 'instrument':
			a = self.instrument()

			if len(a) == 0:
				break
			else:
				ret.update(a)
		return ret
	
	def instrument(self):
		if self.debug:
			sys.stderr.write('In instrument()\n')
		ret = {}
		
		instrument = self.value.replace(':', '')

		self.accept('instrument')
		while self.token == 'space':
			self.accept('space')
		a = {}
		if instrument == 'snare':
			a = self.snareMusic()
		if instrument == 'tenor':
			a = self.tenorMusic()
		if instrument == 'bass':
			a = self.bassMusic()
		if instrument == 'cymbal':
			a = self.cymbalMusic()
		if a != self.NotFound:
			ret[ instrument ] = a
		return ret

	# music()	
	def snareMusic(self):
		if self.debug:
			sys.stderr.write('In snareMusic()\n')
		# returns an array of measures
		ret = []

		while 1:
			#a = self.timeSignature()

			a = self.snareMeasure()

			if a != self.NotFound:
				ret.append(a)
			else:
				break
			while self.token == 'space':
				self.accept('space')
			if self.token != 'pipe':
				break
			else:
				if not self.accept('pipe'):
					break
			while self.token == 'space':
				self.accept('space')
		if len(ret) == 0:
			return self.NotFound
		return ret

	def snareMeasure(self):
		if self.debug:
			sys.stderr.write('In measure()\n')

		# returns a measure structure
		ret = {
			'timeSignature': '4/4',
			'beats': []
		}
		while 1: # wish we had a do..while
			a = self.snareBeat()
			if len(a) == 0:
				break
			ret['beats'].append(a)
			while self.token == 'space':
				self.accept('space')

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def snareBeat(self):
		if self.debug:
			sys.stderr.write('In snareBeat()\n')
		# returns an array of notes
		ret = []
		while ['articulation','dynamic','rest','snareSurface','sticking'].count(self.token):
			# digest notes
			a = self.snareNote()
			if a == self.NotFound:
				if self.debug:
					sys.stderr.write('NotFound from snareNote()\n')
				break
			else:
				ret.append(a)


		# are we at the sticking separator?
		if self.token == 'startSticking':
			self.accept('startSticking')
			stickings = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			for sticking in stickings:
				note = ret[ i ]
				if sticking != '.':
					note['sticking'] = stickings[i]
				i += 1
			
		return ret

	def snareNote(self):
		if self.debug:
			sys.stderr.write('In snareNote()\n')
		# returns a note structure
		# this is just a sample of the structure, elements will not be present unless they have a value
		ret = {
			#'accent': False,
			#'diddle': False,
			#'dynamic': False,
			#'dynamicChange': '>' or '<'
			#'dynamicChangeEnd': False,
			#'flam': False,
			#'flamRest': False,
			#'fours': False,
			#'highAccent': False,
			#'notes': [],
			#'rest': False,
			#'sticking': False,
			#'surface': False
		}
		
		a = self.snareModifiers()
		ret.update(a)
		a = self.snareSurface()

		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def snareModifiers(self):
		if self.debug:
			sys.stderr.write('In snareModifiers()\n')
		ret = {}
		
		while 1:
			a = self.snareModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def snareModifier(self):
		if self.debug:
			sys.stderr.write('In snareModifier()\n')
		ret = {}
		if self.token == 'articulation':
			if self.value == ',':
				ret['flam'] = 'h'
			if self.value == '-':
				ret['diddle'] = True
			if self.value == '=':
				ret['fours'] = True
			self.accept('articulation')
			return ret

		elif self.token == 'dynamic':
			return self.dynamicModifier()

		else:
			if self.debug:
				sys.stderr.write('No modifier or no more\n')
			return self.NotFound

	def snareSurface(self):
		if self.debug:
			sys.stderr.write('In snareSurface()\n')
		ret = {}

		# snare
		# rR lL xX yY sS
		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif re.search(self.value, "HXRBSG"):
			# why would value='.' be matched here?
			ret['accent'] = True
			if self.value == 'X':
				ret['shot'] = True
				ret['surface'] = self.value.lower()
			else:
				ret['surface'] = self.value.lower()
			self.accept('snareSurface')
			return ret

		elif re.search(self.value, "hxrbsg"):
			if self.value == 'x':
				ret['shot'] = True
				ret['surface'] = self.value
			else:
				ret['surface'] = self.value
			self.accept('snareSurface')
			return ret
			
		else: # should only get here if there's an error
			return self.NotFound



# bass methods

	def bassMusic(self):
		if self.debug:
			sys.stderr.write('In bassMusic()\n')
		# returns an array of measures
		ret = []

		while 1:
			a = self.bassMeasure()

			if a != self.NotFound:
				ret.append(a)
			else:
				break

			while self.token == 'space':
				self.accept('space')
			if self.token != 'pipe':
				break
			else:
				if not self.accept('pipe'):
					break
			while self.token == 'space':
				self.accept('space')
		if len(ret) == 0:
			return self.NotFound
		return ret

	def bassMeasure(self):
		if self.debug:
			sys.stderr.write('In measure()\n')

		# returns a measure structure
		ret = {
			'timeSignature': '4/4',
			'beats': []
		}
		while 1:
			a = self.bassBeat()
			if len(a) == 0:
				break
			ret['beats'].append(a)
			while self.token == 'space':
				self.accept('space')

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def bassBeat(self):
		if self.debug:
			sys.stderr.write('In bassBeat()\n')
		# returns an array of notes
		ret = []
		# need to add simultaneous and other tokens
		while ['articulation','dynamic','rest','sticking','bassTenorSurface','simultaneous'].count(self.token):
			a = self.bassNote()
			if a == self.NotFound:
				if self.debug:
					sys.stderr.write('NotFound from bassNote()\n')
				break
			else:
				ret.append(a)

		# are we at the sticking separator?
		if self.token == 'startSticking':
			self.accept('startSticking')
			stickings = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			for sticking in stickings:
				note = ret[ i ]
				if sticking != '.':
					note['sticking'] = stickings[i]
				i += 1

		return ret

	def bassNote(self):
		if self.debug:
			sys.stderr.write('In bassNote()\n')
		# returns a note structure
		# this is just a sample of the structure, elements will not be present unless they have a value
		ret = {
			#'accent': False,
			#'diddle': False,
			#'dynamic': False,
			#'dynamicChange': '>' or '<'
			#'dynamicChangeEnd': False,
			#'flam': False,
			#'flamRest': False,
			#'fours': False,
			#'highAccent': False,
			#'notes': [],
			#'rest': False,
			#'sticking': False,
			#'surface': False
		}
		
		a = self.bassModifiers()
		ret.update(a)
		a = self.bassSurface()

		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def bassModifiers(self):
		if self.debug:
			sys.stderr.write('In bassModifiers()\n')
		ret = {}
		
		while 1:
			a = self.bassModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def bassModifier(self):
		if self.debug:
			sys.stderr.write('In bassModifier()\n')
		ret = {}
		if self.token == 'articulation':
			if self.value == ',':
				ret['flam'] = True
			if self.value == '-':
				ret['diddle'] = True
			if self.value == '=':
				ret['fours'] = True
			self.accept('articulation')
			return ret

		elif self.token == 'dynamic':
			return self.dynamicModifier()

		else:
			if self.debug:
				sys.stderr.write('No modifier or no more\n')
			return self.NotFound

	def bassSurface(self):
		if self.debug:
			sys.stderr.write('In bassSurface()\n')
		ret = {}

		if self.token == 'simultaneous':
			surface = ''
			self.accept('simultaneous')
			while self.token == 'bassTenorSurface':
				if re.search(self.value, "ABCDEFU"):
					ret['accent'] = True # if any are accented, all will be
					surface = surface + self.value.lower()
		
				elif re.search(self.value, "abcdefu"):
					surface = surface + self.value

				self.accept('bassTenorSurface')
			self.accept('simultaneous')
			ret['surface'] = surface
			return ret


		else:
			# bass tenor
			if self.token == 'rest': #rest
				ret['rest'] = True
				self.accept('rest')
				return ret
	
			elif re.search(self.value, "ABCDEFU"):
				ret['accent'] = True
				ret['surface'] = self.value.lower()
				self.accept('bassTenorSurface')
				return ret
	
			elif re.search(self.value, "abcdefu"):
				ret['surface'] = self.value
				self.accept('bassTenorSurface')
				return ret
				
			else: # should only get here if there's an error
				return self.NotFound

# tenor methods

	def tenorMusic(self):
		if self.debug:
			sys.stderr.write('In tenorMusic()\n')
		# returns an array of measures
		ret = []

		while 1:
			a = self.tenorMeasure()

			if a != self.NotFound:
				ret.append(a)
			else:
				break

			while self.token == 'space':
				self.accept('space')
			if self.token != 'pipe':
				break
			else:
				if not self.accept('pipe'):
					break
			while self.token == 'space':
				self.accept('space')
		if len(ret) == 0:
			return self.NotFound
		return ret

	def tenorMeasure(self):
		if self.debug:
			sys.stderr.write('In measure()\n')

		# returns a measure structure
		ret = {
			'timeSignature': '4/4',
			'beats': []
		}
		while 1:
			a = self.tenorBeat()
			if len(a) == 0:
				break
			ret['beats'].append(a)
			while self.token == 'space':
				self.accept('space')

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def tenorBeat(self):
		if self.debug:
			sys.stderr.write('In tenorBeat()\n')
		# returns an array of notes
		ret = []
		# need to add simultaneous and other tokens
		while ['articulation','dynamic','rest','sticking', 'bassTenorSurface', 'tenorModifier'].count(self.token):
			a = self.tenorNote()
			if a == self.NotFound:
				if self.debug:
					sys.stderr.write('NotFound from tenorNote()\n')
				break
			else:
				ret.append(a)

		# are we at the sticking separator?
		if self.token == 'startSticking':
			self.accept('startSticking')
			stickings = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			for sticking in stickings:
				note = ret[ i ]
				if sticking != '.':
					note['sticking'] = stickings[i]
				i += 1

		return ret

	def tenorNote(self):
		if self.debug:
			sys.stderr.write('In tenorNote()\n')
		# returns a note structure
		# this is just a sample of the structure, elements will not be present unless they have a value
		ret = {
			#'accent': False,
			#'diddle': False,
			#'dynamic': False,
			#'dynamicChange': '>' or '<'
			#'dynamicChangeEnd': False,
			#'flam': False,
			#'flamRest': False,
			#'fours': False,
			#'highAccent': False,
			#'notes': [],
			#'rest': False,
			#'sticking': False,
			#'surface': False
		}
		
		a = self.tenorModifiers()
		ret.update(a)
		a = self.tenorSurface()

		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def tenorModifiers(self):
		if self.debug:
			sys.stderr.write('In tenorModifiers()\n')
		ret = {}
		
		while 1:
			a = self.tenorModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def tenorModifier(self):
		if self.debug:
			sys.stderr.write('In tenorModifier()\n')
		ret = {}
		if self.token == 'articulation':
			if self.value == ',':
				ret['flam'] = True
			if self.value == '-':
				ret['diddle'] = True
			if self.value == '=':
				ret['fours'] = True
			self.accept('articulation')
			return ret

		elif self.token == 'tenorModifier':
			if self.value == '*': # shot
				ret['shot'] = True
			self.accept('tenorModifier')
			return ret

		elif self.token == 'dynamic':
			return self.dynamicModifier()

		else:
			if self.debug:
				sys.stderr.write('No modifier or no more\n')
			return self.NotFound

	def tenorSurface(self):
		if self.debug:
			sys.stderr.write('In tenorSurface()\n')
		ret = {}

		# bass tenor
		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif re.search(self.value, "ABCDEFU"):
			ret['accent'] = True
			ret['surface'] = self.value.lower()
			self.accept('bassTenorSurface')
			return ret

		elif re.search(self.value, "abcdefu"):
			ret['surface'] = self.value
			self.accept('bassTenorSurface')
			return ret
			
		else: # should only get here if there's an error
			return self.NotFound


	def sticking(self):
		ret = []
		while self.token == 'sticking' or self.token == 'rest':
			a = self.token
			if a == 'rest':
				ret.append(self.value)
				self.accept('rest')
			if a == 'sticking':
				ret.append(self.value)
				self.accept('sticking')
		return ret
				
	def dynamicModifier(self):
		ret = {}
		if self.token == 'dynamic':
			if self.value == 'P':
				ret['dynamic'] = 'P'
			if self.value == 'M':
				ret['dynamic'] = 'M'
			if self.value == 'F':
				ret['dynamic'] = 'F'
			if self.value == '<':
				ret['dynamicChange'] = '<'
			if self.value == '>':
				ret['dynamicChange'] = '>'
			self.accept('dynamic')
			return ret

	def condense(self, score, settings={}):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# for tenors, merge flam notes together

		# expand unison surface into simultaneous based on number of basses?

		# if timeSignature per measure is not specified, deduce into x/4

		# obey basses setting
		basses = 'abcdef'
		if 'basses' in score:
			bassUnison = basses[0: int(score['basses']) ]
		else: # default to 5 basses for unisons
			bassUnison = basses[0:5]

		# annotate with durations
		for (instrument,music) in score['instruments'].items():
			dynamic = False 
			dynamicChange = False
			tupletCount = 1
			for measure in music:
				#if not 'timeSignature' in measure:
				#	measure['timeSignature'] = score['timeSignature']
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
								note['surface'] = bassUnison
							if 'flam' in note:
								note['flam'] = note['surface']
					# end bass-specific

					# this is really geared toward midi output
					# annotate with durations
					duration = len(beat)
					for note in beat:
						# duration is the denominator of the fraction,
						# how much of the beat the note owns
						# 4 would be 1/4 of a beat, thus a 16th note
						note['duration'] = duration
						if not (duration == 1 or duration == 2 or duration % 4 == 0):
							if tupletCount == 1:
								note['tupletStart'] = duration

							if tupletCount == duration:
								note['tupletStop'] = True
								tupletCount = 1
							else:
								tupletCount += 1
							note['tuplet'] = True
						else:
							tupletCount = 1

					# set dynamicChangeEnd
					for note in beat:
						if dynamicChange and 'dynamic' in note:
							note['dynamicChangeEnd'] = True
							dynamicChange = False
						if 'dynamicChange' in note:
							dynamicChange = True
						
					# condense rests
                                        # need to skip tuplets
                                        i = 0
                                        z = len(beat)
                                        while i < z:
                                                j = i + 1
                                                if not j < z:
                                                        i += 2
                                                        continue
                                                a = beat[i]
                                                b = beat[j]
                                                if 'rest' in b and not 'tuplet' in b: # don't condense rests within tuplets
                                                        a['duration'] /= 2
                                                        del beat[j]
                                                        i -= 1
                                                        z -= 1

                                                i += 2
                                        # end condense rests

		return score

 
rules = [
	# details
	("detail", r"(author|basses|subtitle|tempo|timesignature|title):"),
	# instruments
	("instrument", r"(snare|bass|tenor|cymbal):"),

	#modifiers
	("startSticking", ":"),
	("dynamic", r"[<>PMF]{1}"),
	("sticking", r"[rl]"),
	("articulation", r"[,=-]"),

	("snareSurface", r"[hHxX]"),
	("bassTenorSurface", r"[aAbBcCdDeEuU]"),
	("tenorModifier", r"[*]"),
	("rest", r"[.]"),

	("pipe", r"\|"),

	("simultaneous", r"\(|\)"),
	
	("space", r"[\t\r\n ]"),
	("string", r"\"[a-zA-Z0-9 /_-]+\"") # string

	#("timesignature", r"[1-9]/[1-9]")
	#("tempo", r"[1-9]+")
]
 
lex = Lexer(rules, case_sensitive=True, omit_whitespace=False)

settings = {}

# debug
# debug2

for arg in sys.argv:
	if arg.startswith('--'): # flag
		# does it have an equal sign?
		parts = arg[2:].split('=')
		if len(parts) > 1:
			settings[ parts[0] ] = parts[1]
		else:
			settings[ arg[2:] ] = True
			

tokens = lex.scan( sys.stdin.read() )

# hmmm, which methods do i need to pass settings to?

parser = Parser(tokens, settings)
a = parser.score()
# finalizes and annotates the intermediate data structure
a = parser.condense(a)

if 'midi' in settings:
	out = MidiConvertor()
	b = out.convert(a, settings)
	sys.stdout.write(b)

elif 'lilypond' in settings:
	out = LilypondConvertor()
	b = out.convert(a, settings)
	sys.stdout.write(b)

else:
	sys.stdout.write( repr(a) )
