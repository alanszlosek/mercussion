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

	def __init__(self, tokens):
		self.tokens = tokens
		self.token, self.value = self.tokens.next()
		self.debug = False
		self.debug2 = False

	def die(self, message):
		print(message)
		sys.exit()

	def accept(self, a):
		if self.token == a:
			if self.debug2:
				print('Accept ' + self.token + ':' + self.value)
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
				print('No more')
			return False

		except UnknownTokenError:
			self.token = self.value = False
			self.die('Unknown token')
			return False
		if self.debug:
			print('At ' + self.token + ':' + self.value)
		return True


	def score(self):
		ret = {}
		a = self.details()
		if len(a):
			ret.update(a)
		a = self.instruments()
		ret['instruments'] = a
		if self.debug:
			print( repr(ret) )

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
			print('In instruments()')
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
			print('In instrument()')
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
			print('In snareMusic()')
		# returns an array of measures
		ret = []

		while 1:
			#a = self.timeSignature()

			a = self.snareMeasure()

			if a != self.NotFound:
				ret.append(a)
			else:
				break
			#print(self.token)
			#sys.exit()
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
			print('In measure()')

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
			print('In snareBeat()')
		# returns an array of notes
		ret = []
		while ['articulation','dynamic','rest','snareSurface','sticking'].count(self.token):
			# digest notes
			a = self.snareNote()
			if a == self.NotFound:
				if self.debug:
					print('NotFound from snareNote()')
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
					#print(note['surface'])
				i += 1
			
		return ret

	def snareNote(self):
		if self.debug:
			print('In snareNote()')
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
			print('In snareModifiers()')
		ret = {}
		
		while 1:
			a = self.snareModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def snareModifier(self):
		if self.debug:
			print('In snareModifier()')
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
				print('No modifier or no more')
			return self.NotFound

	def snareSurface(self):
		if self.debug:
			print('In snareSurface()')
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
			ret['surface'] = self.value.lower()
			self.accept('snareSurface')
			return ret

		elif re.search(self.value, "hxrbsg"):
			ret['surface'] = self.value
			self.accept('snareSurface')
			return ret
			
		else: # should only get here if there's an error
			return self.NotFound



# bass methods

	def bassMusic(self):
		if self.debug:
			print('In bassMusic()')
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
			print('In measure()')

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
			print('In bassBeat()')
		# returns an array of notes
		ret = []
		# need to add simultaneous and other tokens
		while ['articulation','dynamic','rest','sticking','bassTenorSurface','bassSimultaneous'].count(self.token):
			a = self.bassNote()
			if a == self.NotFound:
				if self.debug:
					print('NotFound from bassNote()')
				break
			else:
				ret.append(a)

		# are we at the sticking separator?
		if self.token == 'startSticking':
			self.accept('startSticking')
			b = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			# should loop over sticking array instead
			for note in ret:
				if type(note) == list:
					# copy to each note in simultaneous list
					pass
				elif type(note) == dict:
					if not 'rest' in note:
						#note['sticking'] = b[i]
						#print(note['surface'])
						i += 1

		return ret

	def bassNote(self):
		if self.debug:
			print('In bassNote()')
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
			print('In bassModifiers()')
		ret = {}
		
		while 1:
			a = self.bassModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def bassModifier(self):
		if self.debug:
			print('In bassModifier()')
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
				print('No modifier or no more')
			return self.NotFound

	def bassSurface(self):
		if self.debug:
			print('In bassSurface()')
		ret = {}

		if self.token == 'bassSimultaneous':
			surface = ''
			self.accept('bassSimultaneous')
			while self.token == 'bassTenorSurface':
				if re.search(self.value, "ABCDEFU"):
					ret['accent'] = True # if any are accented, all will be
					surface = surface + self.value.lower()
		
				elif re.search(self.value, "abcdefu"):
					surface = surface + self.value

				self.accept('bassTenorSurface')
			self.accept('bassSimultaneous')
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
			print('In tenorMusic()')
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
			print('In measure()')

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
			print('In tenorBeat()')
		# returns an array of notes
		ret = []
		# need to add simultaneous and other tokens
		while ['articulation','dynamic','rest','sticking', 'bassTenorSurface'].count(self.token):
			a = self.tenorNote()
			if a == self.NotFound:
				if self.debug:
					print('NotFound from tenorNote()')
				break
			else:
				ret.append(a)

		# are we at the sticking separator?
		if self.token == 'startSticking':
			self.accept('startSticking')
			b = self.sticking()
			# now annotate notes in ret with stickings we just got?
			i = 0
			# should loop over sticking array instead
			for note in ret:
				if type(note) == list:
					# copy to each note in simultaneous list
					pass
				elif type(note) == dict:
					if not 'rest' in note:
						#note['sticking'] = b[i]
						#print(note['surface'])
						i += 1

		return ret

	def tenorNote(self):
		if self.debug:
			print('In tenorNote()')
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
			print('In tenorModifiers()')
		ret = {}
		
		while 1:
			a = self.tenorModifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def tenorModifier(self):
		if self.debug:
			print('In tenorModifier()')
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
				print('No modifier or no more')
			return self.NotFound

	def tenorSurface(self):
		if self.debug:
			print('In tenorSurface()')
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

 
rules = [
	# details
	("detail", r"(author|tempo|timesignature|title|subtitle):"),
	# instruments
	("instrument", r"(snare|bass|tenor|cymbal):"),

	#modifiers
	("startSticking", ":"),
	("dynamic", r"[<>PMF]{1}"),
	("sticking", r"[rl]"),
	("articulation", r"[,=-]"),

	("snareSurface", r"[hHxX]"),
	("bassTenorSurface", r"[aAbBcCdDeEuU]"),
	("bassSimultaneous", r"\[|\]"),
	("rest", r"[.]"),

	("pipe", r"\|"),

	("simultaneousA", r"\("),
	("simultaneousB", r"\)"),
	
	("space", r"[\t\n ]"),
	("string", r"\"[a-zA-Z0-9 /_-]+\"") # string

	#("timesignature", r"[1-9]/[1-9]")
	#("tempo", r"[1-9]+")
]
 
lex = Lexer(rules, case_sensitive=True, omit_whitespace=False)

#tokens = lex.scan("title:\"Listen here Fucker\" author: \"Alan Szlosek\" snare:\n\tPH-hhh x.hh ,hh,hh | lhlh =h=h\nbass:\n\tPaa bb cc|aabb")
#tokens = lex.scan("snare:(ab).cd aab bbc | . . . | a b c")
#tokens = lex.scan("snare:P,H.hh -hHhh Mhhh.hh")
#tokens = lex.scan("b.cd")
#tokens = lex.scan("snare: hhhh hhh. tenor: ,bCba,aD abC.")

settings = {
	'basses': 5,
	'tapOff': False
}

# would rather read from stdin
f = open(sys.argv[1], 'r')

which = ''
for arg in sys.argv:
	if arg.startswith('--'): # flag
		which = arg[2:]	
		pass

text = f.read()
tokens = lex.scan(text)

parser = Parser(tokens)
a = parser.score()

# finalizes and annotates the intermediate data structure
conv = Convertor()
a = conv.condense(a)

if which == 'midi':
	midi = MidiConvertor()
	b = midi.convert(a)
	print(b)

else:
	print( repr(a) )

#convertor = LilypondConvertor()
#b = convertor.convert(a, settings)
#print( b )
