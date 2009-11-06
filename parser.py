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
		self.debug = False #True

	def die(self, message):
		print(message)
		sys.exit()

	def accept(self, a):
		if self.token == a:
			if self.debug:
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
		if self.token == 'detail':
			a = self.details()
			ret.update(a)
		a = self.instruments()
		ret['instruments'] = a
		if self.debug:
			print( repr(ret) )
		return ret

	def details(self):
		ret = {}
		while self.token == 'detail':
			detail = self.value
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
		while 1:
			if self.token == False: # end of input
				break
			a = self.instrument()
			if a == self.NotFound:
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
		a = self.music()
		if a != self.NotFound:
			ret[ instrument ] = a
		return ret

	def music(self):
		if self.debug:
			print('In music()')
		# returns an array of measures
		ret = []

		while 1:
			a = self.measure()
			#print('here:' + repr(a))
			#sys.exit()

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
				

	def measure(self):
		if self.debug:
			print('In measure()')

		# returns a measure structure
		ret = {
			'timeSignature': '4/4',
			'beats': []
		}
		while 1:
			a = self.beat()
			if len(a) == 0:
				break
			ret['beats'].append(a)
			while self.token == 'space':
				self.accept('space')

		if len( ret['beats'] ) == 0:
			return self.NotFound
		return ret

	def beat(self):
		if self.debug:
			print('In beat()')
		# returns an array of notes
		ret = []
		while 1:
			if self.token == 'simultaneousA': # simultaneous
				self.accept('simultaneousA')
				a = self.simultaneousNotes()
				if a == self.NotFound:
					self.die('Should not be here')
					break
				else:
					ret.append(a)
				self.expect('simultaneousB')

			else:
				a = self.note()
				if a == self.NotFound:
					if self.debug:
						print('NotFound from note()')
					break
				else:
					ret.append(a)
				# notes or modifiers
				if ['articulation','dynamic','noteSurface','sticking'].count(self.token) == 0:
					if self.debug:
						print('Break from beat()')
					break
		return ret

	# just like beat(), but without the parenthesis grouping
	def simultaneousNotes(self):
		if self.debug:
			print('In simultaneousNotes()')
		# returns an array of notes
		ret = []
		while 1:
			a = self.note()
			if a == self.NotFound:
				break
			else:
				ret.append(a)
			# notes or modifiers
			if ['articulation','dynamic','noteSurface','sticking'].count(self.token) == 0:
				if self.debug:
					print('Break from simultaneousNotes()')
				break
		return ret
		

	def note(self):
		if self.debug:
			print('In note()')
		# returns a note structure
		# this is just a sample of the structure, elements will not be present unless they have a value
		ret = {
			#'accent': False,
			#'crescendo': False,
			#'decrescendo': False,
			#'diddle': False,
			#'dynamic': False,
			#'flam': False,
			#'flamRest': False,
			#'fours': False,
			#'highAccent': False,
			#'notes': [],
			#'rest': False,
			#'sticking': False,
			'surface': False
		}
		
		a = self.modifiers()
		ret.update(a)
		a = self.noteSurface()
		if a == self.NotFound: # if no surface, probably an error
			return self.NotFound
			#self.die('Should have caught this error in surfaceNote()')
		else:
			ret.update(a)
		return ret

	def modifiers(self):
		if self.debug:
			print('In modifiers()')
		ret = {}
		
		while 1:
			a = self.modifier()
			if a == self.NotFound: # no modifiers, or no more modifiers
				break
			ret.update(a)
		return ret

	def modifier(self):
		if self.debug:
			print('In modifier()')
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
			if self.value == 'P':
				ret['dynamic'] = 'P'
			if self.value == 'M':
				ret['dynamic'] = 'M'
			if self.value == 'F':
				ret['dynamic'] = 'F'
			if self.value == '<':
				ret['crescendo'] = True
			if self.value == '>':
				ret['decrescendo'] = True
			self.accept('dynamic')
			return ret

		elif self.token == 'sticking':
			if self.value == 'l':
				ret['sticking'] = 'l'
			if self.value == 'r':
				ret['sticking'] = 'r'
			self.accept('sticking')
			return ret
		else:
			if self.debug:
				print('No modifier or no more')
			return self.NotFound

	def noteSurface(self):
		if self.debug:
			print('In noteSurface()')
		ret = {}
		if self.token == False: # end of input
			return self.NotFound
			self.die('EOI')

		# snare
		if self.value == '.': #rest
			ret['rest'] = True
		elif re.search(self.value, "ABCDEFX"):
			# why would value='.' be matched here?
			ret['accent'] = True
			ret['surface'] = self.value.lower()
		else:
			ret['surface'] = self.value
			
		if self.accept('noteSurface'):
			return ret
		else: # should only get here if there's an error
			return self.NotFound
			#self.die('Expected a note surface')

 
rules = [
	# details
	("detail", r"(author|tempo|timesignature|title):"),
	# instruments
	("instrument", r"(snare|bass|tenor|cymbal):"),

	#modifiers
	("dynamic", r"[<>PMF]{1}"),
	("sticking", r"[rl]"),
	("articulation", r"[,=-]"),

	("noteSurface", r"[hHxXaAbBcCdDeEuU.]"),

	("pipe", r"\|"),

	#("drum", r"[1-6]{1}"),
	("simultaneousA", r"\("),
	("simultaneousB", r"\)"),
	
	("space", r"[\t\n ]"),
	#("line", r"\r|\n"), 
	("string", r"\"[a-zA-Z0-9 _-]+\"") # string

	#("timesignature", r"[1-9]/[1-9]")
	#("tempo", r"[1-9]+")
]
 
lex = Lexer(rules, case_sensitive=True, omit_whitespace=False)

#tokens = lex.scan("title:\"Listen here Fucker\" author: \"Alan Szlosek\" snare:\n\tPH-hhh x.hh ,hh,hh | lhlh =h=h\nbass:\n\tPaa bb cc|aabb")
#tokens = lex.scan("snare:(ab).cd aab bbc | . . . | a b c")
#tokens = lex.scan("snare:P,H.hh -hHhh Mhhh.hh")
#tokens = lex.scan("b.cd")
#tokens = lex.scan("snare: hhhh hhh. tenor: ,bCba,aD abC.")


if sys.argv[1] == '--midi':
	tweakForMidi = True
	f = open(sys.argv[2], 'r')
else:
	f = open(sys.argv[1], 'r')

text = f.read()
tokens = lex.scan(text)

parser = Parser(tokens)
a = parser.score()
#print( repr(a) )

convertor = Convertor()
settings = {
	'expantTremolos': False,
	'tapOff': False
}
b = convertor.toLilypond(a, settings)

print( b )
