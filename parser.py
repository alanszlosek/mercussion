import sys
import yaml
from lexer import *
from convertor import *

# what i'd like is for each method to return a data structure
# or empty if there were no matches
# what do i do when input is exhausted?

class Parser:
	# defines
	NotFound = -1

	token = ''
	value = ''

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

	def whitespace(self):
		while self.token == 'space':
			self.accept('space')

	# music()	
	def music(self):
		if self.debug:
			sys.stderr.write('In music()\n')
		# returns an array of measures
		ret = []

		while 1:
			#a = self.timeSignature()

			a = self.measure()

			if a != self.NotFound:
				ret.append(a)
			else:
				break

			self.whitespace()

			if self.token != 'pipe':
				break
			else:
				if not self.accept('pipe'):
					break

			self.whitespace()

		if len(ret) == 0:
			return self.NotFound
		return ret

	def measure(self):
		if self.debug:
			sys.stderr.write('In measure()\n')

		# returns a measure structure
		ret = {
			# maybe we should only set timeSignature if it has changed
			#'timesignature': '4/4',
			'beats': []
		}
		while 1: # wish we had a do..while
			a = self.beat()
			if len(a) == 0:
				break
			ret['beats'].append(a)

			self.whitespace()

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def beat(self):
		if self.debug:
			sys.stderr.write('In beat()\n')
		# returns an array of notes
		ret = []
		simultaneous = False
		while ['articulation','dynamic','rest','simultaneous','sticking','surface'].count(self.token):
			# digest notes
			a = self.note()
			if a == self.NotFound:
				if self.debug:
					sys.stderr.write('NotFound from note()\n')
				break

			if simultaneous:
				# tack surface onto last parsed note
				ret[ len(ret)-1 ]['surface'] += a['surface']
			else:
				ret.append(a)

			if self.token == 'simultaneous':
				simultaneous = True
				self.accept('simultaneous')
			else:
				simultaneous = False


		# are we at the sticking separator?
		if self.token == 'colon':
			self.accept('colon')
			stickings = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			for note in ret:
				if not i < len(stickings):
					break
				sticking = stickings[ i ]
				if 'rest' in note:
					continue
				note['hand'] = sticking
				i += 1
			
		return ret

	def note(self):
		if self.debug:
			sys.stderr.write('In note()\n')
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
		
		a = self.modifiers()
		ret.update(a)
		a = self.surface()

		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def modifiers(self):
		if self.debug:
			sys.stderr.write('In modifiers()\n')
		ret = {}
		
		while 1:
			a = self.modifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def modifier(self):
		if self.debug:
			sys.stderr.write('In modifier()\n')
		ret = {}
		if self.token == 'articulation':
			if self.value == ',':
				ret['flam'] = 'h'
			if self.value == '-':
				ret['diddle'] = True
			if self.value == '=':
				ret['fours'] = True

			# cymbal modifiers
			if self.value == '~' or self.value == '!':
				ret['cymbal'] = 'slide'
			if self.value == '`':
				ret['cymbal'] = 'hihat'
			if self.value == '^':
				ret['cymbal'] = 'tap'
			if self.value == '@':
				ret['cymbal'] = 'crashchoke'
			if self.value == '!':
				ret['stop'] = True
			self.accept('articulation')
			return ret

		elif self.token == 'dynamic':
			return self.dynamicModifier()

		else:
			if self.debug:
				sys.stderr.write('No modifier or no more\n')
			return self.NotFound

	def surface(self):
		if self.debug:
			sys.stderr.write('In surface()\n')
		ret = {}

		if self.token == 'rest': #rest
			ret['rest'] = True
			self.accept('rest')
			return ret

		elif self.token == 'surface':
			# why would value='.' be matched here?
			if self.value.isupper():
				ret['accent'] = True
			if self.value.lower() == 'x':
				ret['shot'] = True

			ret['surface'] = self.value.lower()
			self.accept('surface')
			return ret

		else: # should only get here if there's an error
			return self.NotFound

	def sticking(self):
		ret = []
		while self.token == 'sticking' or self.token == 'rest':
			a = self.token
			if a == 'rest':
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

	def condense(self, instrument, music, settings={}):
		# should we also annotate notes with durations in this step, or another step prior to self.toLilypond()?

		# within a beat, if the last note of a pair is a rest, the note prior to a rest should have half the duration
		# 32 32 32 32rest 32 32 32 32
		# should become
		# 32 32 16 32 32 32 32

		# for tenors, merge flam notes together

		# if timeSignature per measure is not specified, deduce into x/4

		# annotate with durations and many other things
		dynamic = False 
		dynamicChange = False
		tupletCount = 1

		# set time signature on first measure if not specified and score has one
		# FIX ME
		#firstMeasure = music[0]
		#if not 'timesignature' in firstMeasure and 'timesignature' in score:
		#	firstMeasure['timesignature'] = score['timesignature']

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
						if 'flam' in note:
							note['flam'] = note['surface']
							note['surface'] = beat[ i+1 ]['surface']
							#print('del' + str(i+1))
							del beat[i+1]
							z -= 1
						i += 1
				# end tenor-specific

				# fix bass flams
				if instrument == 'bass':
					for note in beat:
						if 'flam' in note:
							note['flam'] = note['surface']
				# end bass-specific

				# cymbal-specific
				if instrument == 'cymbal':
					for note in beat:
						if not 'surface' in note:
							continue
						if note['surface'] == 'b': # slide-choke
							pass
						if note['surface'] == 'c': # crash-choke
							pass
						if 'cymbal' in note and note['cymbal'] == 'hihat': # hihat
							note['staccato'] = True
					
				# end cymbal-specific
					

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

		return music 

 
rules = [
	("comment", r"#.*"),

	#modifiers
	("dynamic", r"[<>OPMFG]{1}"),
	("sticking", r"[rl]"),
	("articulation", r"[,=~!`@^-]"),
# really do need cymbal-only articulations

	("surface", r"[aAbBcCdDeEuUsStThHxX]"),
	("rest", r"[.]"),

	("pipe", r"\|"),

	("simultaneous", r"\+"),
	
	("space", r"[\t\r\n ]"),

	("integer", r"[0-9]"),
	("colon", ":")
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

instruments = ['snare','tenor','bass','cymbal']

if 'instruments' in settings:
	settings['instruments'] = map(str.strip, settings['instruments'].split(',')) # might need to strip spaces or quotes
else:
	settings['instruments'] = instruments

doc = yaml.load( sys.stdin.read() )

# clear out instrument we want to ignore
for instrument in instruments:
	if instrument in doc and not instrument in settings['instruments']:
		del doc[ instrument ]


# foreach instrument, lex
for instrument in settings['instruments']:
	if not instrument in doc:
		continue
	tokens = lex.scan( doc[ instrument ] )

# hmmm, which methods do i need to pass settings to?

	parser = Parser(tokens, settings)
	a = parser.music()
	# finalizes and annotates the intermediate data structure
	a = parser.condense(instrument, a)
	# replace original string
	doc[ instrument ] = a

doc['instruments'] = settings['instruments']

if 'midi' in settings:
	out = MidiConvertor()
	b = out.convert(doc, settings)
	sys.stdout.write(b)

elif 'vdlmidi' in settings:
	out = VDLMidiConvertor()
	b = out.convert(doc, settings)
	sys.stdout.write(b)

elif 'midi2' in settings:
	out = MidiConvertor2()
	b = out.convert(doc, settings)
	sys.stdout.write(b)

elif 'lilypond' in settings:
	out = LilypondConvertor()
	b = out.convert(doc, settings)
	sys.stdout.write(b)

elif 'musicxml' in settings:
	out = MusicXMLConvertor()
	b = out.convert(doc, settings)
	sys.stdout.write(b)

else:
	sys.stdout.write( repr(doc) )
