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

	settings = {}

	def __init__(self, tokens, settings={}):
		self.tokens = tokens
		self.token, self.value = self.tokens.next()
		self.debug = ('debug' in settings)
		self.debug2 = ('debug2' in settings)
		self.settings = settings

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

		except UnknownTokenError as e:
			self.token = self.value = False
			self.die( str(e) )
			return False

		if self.debug:
			sys.stderr.write('At ' + self.token + ':' + self.value + "\n")
		if self.token == 'comment':
			return self.next()
		return True


	def score(self):
		ret = {}
		ret['instruments'] = ['snare','tenor','bass','cymbal']

		if 'instruments' in self.settings:
			for instrument in ret['instruments']:
				if not instrument in self.settings['instruments']:
					ret['instruments'].remove( instrument )

		a = self.details()
		if len(a):
			ret.update(a)
		a = self.instruments()
		if len(a):
			ret.update(a)
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
				# is the current instrument name in self.settings['instruments']
				# if 'instruments' in self.settings and instrument in self.settings['instruments']
				# skip
				# else
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
			# maybe we should only set timeSignature if it has changed
			#'timesignature': '4/4',
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
					note['hand'] = stickings[i]
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
			#'timesignature': '4/4',
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
		while ['articulation','dynamic','rest','sticking','bassTenorSurface','simultaneousA'].count(self.token):
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
					note['hand'] = stickings[i]
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
			sys.stderr.write('In tenorSurface()\n')
		ret = {}

		# bass tenor
		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif self.token == 'simultaneousA':
			self.accept('simultaneousA')
			ret = self.bassSurfaces()
			self.accept('simultaneousB')
			return ret

		else:
			return self.bassSurface2()

	def bassSurface2(self):
		if self.debug:
			sys.stderr.write('In bassSurface2()\n')
		ret = {}
		if re.search(self.value, "ABCDEFU"):
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

	def bassSurfaces(self):
		if self.debug:
			sys.stderr.write('In bassSurfaces()\n')
		ret = {}
		while self.token == 'bassTenorSurface':
			a = self.bassSurface2()
			if 'surface' in ret:
				surface = ret['surface']
			else:
				surface = ''
			if 'surface' in a:
				surface = surface + a['surface']
			ret.update(a)
			ret['surface'] = surface
		return ret


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
			sys.stderr.write('In tenorMeasure()\n')

		# returns a measure structure
		ret = {
			#'timesignature': '4/4',
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
		while ['articulation','dynamic','rest','sticking', 'simultaneousA', 'bassTenorSurface', 'tenorModifier'].count(self.token):
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
					note['hand'] = stickings[i]
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
		
		while ['articulation','dynamic','tenorModifier'].count(self.token):
			if self.token == 'articulation':
				if self.value == ',':
					ret['flam'] = True
				if self.value == '-':
					ret['diddle'] = True
				if self.value == '=':
					ret['fours'] = True
				self.accept('articulation')

			elif self.token == 'tenorModifier':
				if self.value == '*': # shot
					ret['shot'] = True
				self.accept('tenorModifier')

			elif self.token == 'dynamic':
				a = self.dynamicModifier()
				ret.update(a)

		return ret

	def tenorSurface(self):
		if self.debug:
			sys.stderr.write('In tenorSurface()\n')
		ret = {}

		# bass tenor
		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif self.token == 'simultaneousA':
			self.accept('simultaneousA')
			ret = self.tenorSurfaces()
			self.accept('simultaneousB')
			return ret

		else:
			return self.tenorSurface2()

	def tenorSurface2(self):
		if self.debug:
			sys.stderr.write('In tenorSurface2()\n')
		ret = {}
		if re.search(self.value, "ABCDEFU"):
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

	def tenorSurfaces(self):
		if self.debug:
			sys.stderr.write('In tenorSurfaces()\n')
		ret = {}
		while self.token == 'bassTenorSurface':
			a = self.tenorSurface2()
			if 'surface' in ret:
				surface = ret['surface']
			else:
				surface = ''
			if 'surface' in a:
				surface = surface + a['surface']
			ret.update(a)
			ret['surface'] = surface
		return ret


# cymbal methods

	def cymbalMusic(self):
		if self.debug:
			sys.stderr.write('In cymbalMusic()\n')
		# returns an array of measures
		ret = []

		while 1:
			a = self.cymbalMeasure()

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

	def cymbalMeasure(self):
		if self.debug:
			sys.stderr.write('In measure()\n')

		# returns a measure structure
		ret = {
			#'timesignature': '4/4',
			'beats': []
		}
		while 1:
			a = self.cymbalBeat()
			if len(a) == 0:
				break
			ret['beats'].append(a)
			while self.token == 'space':
				self.accept('space')

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def cymbalBeat(self):
		if self.debug:
			sys.stderr.write('In cymbalBeat()\n')
		# returns an array of notes
		ret = []
		# need to add simultaneous and other tokens
		while ['articulation','dynamic','rest','bassTenorSurface','simultaneousA', 'tenorModifier','cymbalModifier'].count(self.token):
			a = self.cymbalNote()
			if a == self.NotFound:
				if self.debug:
					sys.stderr.write('NotFound from cymbalNote()\n')
				break
			else:
				ret.append(a)

		return ret

	def cymbalNote(self):
		if self.debug:
			sys.stderr.write('In cymbalNote()\n')
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
		
		a = self.cymbalModifiers()
		ret.update(a)
		a = self.cymbalSurface()

		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def cymbalModifiers(self):
		if self.debug:
			sys.stderr.write('In cymbalModifiers()\n')
		ret = {}
		
		while 1:
			a = self.cymbalModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def cymbalModifier(self):
		if self.debug:
			sys.stderr.write('In cymbalModifier()\n')
		ret = {}
		if self.token == 'tenorModifier' or self.token == 'cymbalModifier':
			if self.value == '^': # taps
				ret['tap'] = True
				self.accept('cymbalModifier')
			if self.value == '!': # choke
				ret['choke'] = True
				self.accept('cymbalModifier')
			if self.value == '~': # slide
				ret['slide'] = True
				self.accept('cymbalModifier')
			if self.value == '*': # hihat
				ret['hihat'] = True
				self.accept('tenorModifier')
			return ret

		elif self.token == 'dynamic':
			return self.dynamicModifier()

		else:
			if self.debug:
				sys.stderr.write('No modifier or no more\n')
			return self.NotFound

	def cymbalSurface(self):
		if self.debug:
			sys.stderr.write('In cymbalSurface()\n')
		ret = {}

		# bass tenor
		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif self.token == 'simultaneousA':
			self.accept('simultaneousA')
			ret = self.cymbalSurfaces()
			self.accept('simultaneousB')
			return ret

		else:
			return self.cymbalSurface2()

	def cymbalSurface2(self):
		if self.debug:
			sys.stderr.write('In cymbalSurface2()\n')
		ret = {}
		if re.search(self.value, "ABCDEFU"):
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

	def cymbalSurfaces(self):
		if self.debug:
			sys.stderr.write('In cymbalSurfaces()\n')
		ret = {}
		while self.token == 'bassTenorSurface':
			a = self.cymbalSurface2()
			if 'surface' in ret:
				surface = ret['surface']
			else:
				surface = ''
			if 'surface' in a:
				surface = surface + a['surface']
			ret.update(a)
			ret['surface'] = surface
		return ret


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
			if self.value == 'O':
				ret['dynamic'] = 'O'
			if self.value == 'P':
				ret['dynamic'] = 'P'
			if self.value == 'M':
				ret['dynamic'] = 'M'
			if self.value == 'F':
				ret['dynamic'] = 'F'
			if self.value == 'G':
				ret['dynamic'] = 'G'
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

		# annotate with durations and many other things
		for instrument in score['instruments']:
			if not instrument in score:
				continue
			music = score[ instrument ]
			dynamic = False 
			dynamicChange = False
			tupletCount = 1

			# set time signature on first measure if not specified and score has one
			firstMeasure = music[0]
			if not 'timesignature' in firstMeasure and 'timesignature' in score:
				firstMeasure['timesignature'] = score['timesignature']

			for measure in music:
				#if not 'timesignature' in measure:
				#	measure['timesignature'] = score['timesignature']
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
	("comment", r"#.*"),
	# details
	("detail", r"(author|basses|subtitle|tempo|timesignature|title):"),
	# instruments
	("instrument", r"(snare|bass|tenor|cymbal):"),

	#modifiers
	("startSticking", ":"),
	("dynamic", r"[<>OPMFG]{1}"),
	("sticking", r"[rl]"),
	("articulation", r"[,=-]"),

	("snareSurface", r"[hHxXsS]"),
	("bassTenorSurface", r"[aAbBcCdDeEfFuU]"),
	("tenorModifier", r"[*]"),
	("cymbalModifier", r"[~^!]"),
	("rest", r"[.]"),

	("pipe", r"\|"),

	("simultaneousA", r"\("),
	("simultaneousB", r"\)"),
	
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

if 'instruments' in settings:
	settings['instruments'] = map(str.strip, settings['instruments'].split(',')) # might need to strip spaces or quotes

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

elif 'vdlmidi' in settings:
	out = VDLMidiConvertor()
	b = out.convert(a, settings)
	sys.stdout.write(b)

elif 'midi2' in settings:
	out = MidiConvertor2()
	b = out.convert(a, settings)
	sys.stdout.write(b)

elif 'lilypond' in settings:
	out = LilypondConvertor()
	b = out.convert(a, settings)
	sys.stdout.write(b)

elif 'musicxml' in settings:
	out = MusicXMLConvertor()
	b = out.convert(a, settings)
	sys.stdout.write(b)

else:
	sys.stdout.write( repr(a) )
