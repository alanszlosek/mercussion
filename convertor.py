from decimal import *

class Convertor:
	def convert(self,score,settings):
		pass

class MidiConvertor(Convertor):
	# does noteOff affect the output at all? test again, because i might need it for cymbals

	volumeMap = {
		"O": .20,
		"P": .40, # pianissimo
		"M": .60, # mezzo-forte
		"F": .80, # forte
		"G": 1.00 # ff
	}

	# will need to hard-code volume levels for crescendos and decrescendos

	def dynamicRanges(self, score):
		# annotate with crescendo/decrescndo rise/fall data
		# keep track of beats and notes between change start and stopping point

		# annotate each note with its beat/note index
		# helps us with calculating volume rise and fall per note


		# along the way, annotate notes with volume percentage that aren't within a dynamic change
		# keep track of the previous dynamic change
		for (instrument,music) in score['instruments'].items():
			start = {}
			startDynamic = 'M'
			dynamic = 'M'
			beatCount = 0
			for measure in music:
				for beat in measure['beats']:
					noteCount = 0
					for note in beat:
						note['beatIndex'] = beatCount
						note['noteIndex'] = noteCount

						if 'dynamic' in note:
							dynamic = note['dynamic']

						if 'dynamicChangeEnd' in note:
							# log what we're changing to
							# this note should have an absolute dynamic

							beats = note['beatIndex'] - start['beatIndex']
							diff = self.volumeMap[ dynamic ] - self.volumeMap[ startDynamic ]

							perBeat = diff / beats
							start['perBeat'] = perBeat # yikes, floating point sucks

							start = {}

						if len(start) == 0:
							note['volumePercentage'] = self.volumeMap[ dynamic ]

						if 'dynamicChange' in note:
							start = note
							startDynamic = dynamic

						noteCount += 1
					beatCount += 1
		return score

	def cymbals(self, score):
		# convert cymbal notes with special annotations to different surfaces
		for (instrument,music) in score['instruments'].items():
			if not instrument == 'cymbal':
				continue
			for measure in music:
				for beat in measure['beats']:
					for note in beat:
						if 'tap' in note:
							note['surface'] = '^'
						elif 'hihat' in note:
							note['surface'] = '*'
						elif 'surface' in note:
							if note['surface'] == 'c' or note['surface'] == 'd':
								note['surface'] = '@'
							else:
								note['surface'] = '!'
		return score


	def convert(self, score, settings):
		score = self.dynamicRanges(score)
		score = self.cymbals(score)
		#print( repr(score) )
		#return ''

		instrumentProgramMap = {
			"bass": "0",
			"cymbal": "3",
			"snare": "2",
			"tenor": "1"
		}
		instrumentVolumeMap = {
			"bass": 127,
			"cymbal": 80,
			"snare": 100,
			"tenor": 100
		}
		instrumentPanMap = {
			"bass": "64", # 30
			"cymbal": "64",
			"snare": "64",
			"tenor": "64" # 98
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
			"e": "d5",

			# cymbal
			"!": "e6",
			"@": "c6",
			"^": "e6",
			"*": "a5"
			
		}

		if 'tempo' in score:
			scoreTempo = int(score['tempo'])
			tempo = 60000000 / scoreTempo
		else:
			scoreTempo = 120
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
		flamPosition = -20 # calculate based on tempo
		accentIncrease = int(127/4)
		perBeat = 384
		startingCounter = 30 #(scoreTempo / 60) * 30 # calculate how much time would yield a second

		for (instrument,music) in score['instruments'].items():
			instrumentVolume = instrumentVolumeMap[ instrument ]
			volume = self.volumeMap['F'] # start at forte
			volumePerBeat = 0
			volumePerNote = 0
			counter = startingCounter
			nextBeat = counter + perBeat

			channelString = str(channel)
	
			out += "MTrk\n"
			# map instrument to a channel
			out += "0 PrCh ch=" + channelString + " prog=" + instrumentProgramMap[instrument] + "\n"
			# set main track volume
			out += "0 Par ch=" + channelString + " con=7 val=" + str(instrumentVolume) + "\n"
			out += "0 Par ch=" + channelString + " con=10 val=" + instrumentPanMap[instrument] + "\n"

                        for measure in music:
                                for beat in measure['beats']:
					c1 = counter
					volume += volumePerBeat
					notes = len(beat) # need to only count actual notes, not rests

					for note in beat:
						c2 = str(c1)
						if 'rest' in note:
							pass
						else:
							if 'flam' in note:
								# if surface is shot, flams should be on the drum head
								# annotate notes with proper flam surface
								#go back a bit, from current counter value
								tempVolume = int(instrumentVolume * self.volumeMap['P'])
								out += str(c1 - 13) + " On ch=" + channelString + " n=" + noteMap[ note['flam'] ] + " v=" + str(tempVolume) + "\n"
								#out += str(c1 - 5) + " Off ch=" + channelString + " n=" + noteMap[ note['surface'] ] + " v=0\n"
							
							# prepare volume
							if 'volumePercentage' in note:
								volume = note['volumePercentage']
								tempVolume = volume

							if volumePerNote <> 0:
								tempVolume += volumePerNote

							if 'perBeat' in note:
								volumePerBeat = note['perBeat']
								volumePerNote = volumePerBeat / notes

							if 'accent' in note:
								actualVolume = int(instrumentVolume * tempVolume) + accentIncrease
							else:
								actualVolume = int(instrumentVolume * tempVolume)

							if actualVolume > 127:
								actualVolume = 127

							for surface in note['surface']:
								out += c2 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(actualVolume) + "\n"
								# expand diddle/tremolo
								# add the second note
								if 'diddle' in note:
									# don't think diddle should be same volume!
									c3 = str(c1 + (perBeat / (note['duration'] * 2)))
									out += c3 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(actualVolume) + "\n"
								if 'fours' in note:
									c3 = perBeat / (note['duration'] * 4)
									c4 = str(c1 + (c3))
									out += c4 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(actualVolume) + "\n"
									c4 = str(c1 + c3 + c3)
									out += c4 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(actualVolume) + "\n"
									c4 = str(c1 + c3 + c3 + c3)
									out += c4 + " On ch=" + channelString + " n=" + noteMap[ surface ] + " v=" + str(actualVolume) + "\n"
							# when do we turn off
							# divide
							c3 = str(c1 + (perBeat / note['duration']))
							for surface in note['surface']:
								# why do i sometimes see the note off volume at 64?
								#out += c3 + " Off ch=" + channelString + " n=" + noteMap[ surface ] + " v=0\n"
								pass

							# i bet some cymbal notes we'll have to avoid turning off until we get an explicit choke note

						c1 += (perBeat / note['duration']) # how long does this note last?
					nextBeat += perBeat
					counter += perBeat
					# end note loop
				# end beat loop
			# end measure loop
			out += "TrkEnd\n"

			channel += 1
		# end instrument loop
		return out

# for trying out another soundfont with a different instrument layout
class MidiConvertor2(Convertor):
	# does noteOff affect the output at all? test again, because i might need it for cymbals

	volumeMap = {
		"O": .20,
		"P": .40, # pianissimo
		"M": .60, # mezzo-forte
		"F": .80, # forte
		"G": 1.00 # ff
	}

	# will need to hard-code volume levels for crescendos and decrescendos

	def dynamicRanges(self, score):
		# annotate with crescendo/decrescndo rise/fall data
		# keep track of beats and notes between change start and stopping point

		# annotate each note with its beat/note index
		# helps us with calculating volume rise and fall per note


		# along the way, annotate notes with volume percentage that aren't within a dynamic change
		# keep track of the previous dynamic change
		for (instrument,music) in score['instruments'].items():
			start = {}
			startDynamic = 'M'
			dynamic = 'M'
			beatCount = 0
			for measure in music:
				for beat in measure['beats']:
					noteCount = 0
					for note in beat:
						note['beatIndex'] = beatCount
						note['noteIndex'] = noteCount

						if 'dynamic' in note:
							dynamic = note['dynamic']

						if 'dynamicChangeEnd' in note:
							# log what we're changing to
							# this note should have an absolute dynamic

							beats = note['beatIndex'] - start['beatIndex']
							diff = self.volumeMap[ dynamic ] - self.volumeMap[ startDynamic ]

							perBeat = diff / beats
							start['perBeat'] = perBeat # yikes, floating point sucks

							start = {}

						if len(start) == 0:
							note['volumePercentage'] = self.volumeMap[ dynamic ]

						if 'dynamicChange' in note:
							start = note
							startDynamic = dynamic

						noteCount += 1
					beatCount += 1
		return score


	def convert(self, score, settings):
		score = self.dynamicRanges(score)
		#print( repr(score) )
		#return ''

		instrumentProgramMap = {
			"bass": "0",
			"cymbal": "0",
			"snare": "0",
			"tenor": "0"
		}
		instrumentVolumeMap = {
			"bass": 127,
			"cymbal": 127,
			"snare": 100,
			"tenor": 110
		}
		instrumentPanMap = {
			"bass": "30",
			"cymbal": "64",
			"snare": "64",
			"tenor": "98"
		}
		noteMap = {
			'snare': {
				"h": "77",
				"x": "79",
				"s": "81" # rim/ping
			},

			'bass': {
				"a": "69",
				"b": "66",
				"c": "62",
				"d": "57",
				"e": "53" # should be 50
			},

			'tenor': {
				"a": "83", # 83
				"b": "82", # 82
				"c": "80", # 80
				"d": "78", # 78
				"e": "85" # 85
			},

			"cymbal": {
				"a": "111",
				"b": "113",
				"c": "111",
				"d": "113",
				"^": "111", # taps
				"=": "113", # slam-choke
				"h": "121", # hihat
			}
		}

		if 'tempo' in score:
			scoreTempo = int(score['tempo'])
			tempo = 60000000 / scoreTempo
		else:
			scoreTempo = 120
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
		flamPosition = -20 # calculate based on tempo
		accentIncrease = int(127/4)
		perBeat = 384
		startingCounter = 30 #(scoreTempo / 60) * 30 # calculate how much time would yield a second

		for (instrument,music) in score['instruments'].items():
			instrumentVolume = instrumentVolumeMap[ instrument ]
			volume = self.volumeMap['F'] # start at forte
			volumePerBeat = 0
			volumePerNote = 0
			counter = startingCounter
			nextBeat = counter + perBeat

			channelString = str(channel)
	
			out += "MTrk\n"
			# map instrument to a channel
			out += "0 PrCh ch=" + channelString + " prog=" + instrumentProgramMap[instrument] + "\n"
			# set main track volume
			out += "0 Par ch=" + channelString + " con=7 val=" + str(instrumentVolume) + "\n"
			out += "0 Par ch=" + channelString + " con=10 val=" + instrumentPanMap[instrument] + "\n"

                        for measure in music:
                                for beat in measure['beats']:
					c1 = counter
					volume += volumePerBeat
					notes = len(beat) # need to only count actual notes, not rests

					for note in beat:
						c2 = str(c1)
						if 'rest' in note:
							pass
						else:
							if 'flam' in note:
								# if surface is shot, flams should be on the drum head
								# annotate notes with proper flam surface
								#go back a bit, from current counter value
								tempVolume = int(instrumentVolume * self.volumeMap['P'])
								out += str(c1 - 13) + " On ch=" + channelString + " n=" + noteMap[instrument][ note['flam'] ] + " v=" + str(tempVolume) + "\n"
								#out += str(c1 - 5) + " Off ch=" + channelString + " n=" + noteMap[instrument][ note['surface'] ] + " v=0\n"
							
							# prepare volume
							if 'volumePercentage' in note:
								volume = note['volumePercentage']
								tempVolume = volume

							if volumePerNote <> 0:
								tempVolume += volumePerNote

							if 'perBeat' in note:
								volumePerBeat = note['perBeat']
								volumePerNote = volumePerBeat / notes

							if 'accent' in note:
								actualVolume = int(instrumentVolume * tempVolume) + accentIncrease
								if actualVolume > 127:
									actualVolume = 127
							else:
								actualVolume = int(instrumentVolume * tempVolume)

							for surface in note['surface']:
								# SHIT looks like i might need to make simultaneous notes for cymbals be separate notes! because "a" might need to choke while "b" taps
								# if 'choke' in note:
								# elif 'slide' in note:
								# elif 'tap' in note:
								out += c2 + " On ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=" + str(actualVolume) + "\n"
								# expand diddle/tremolo
								# add the second note
								if 'diddle' in note:
									c3 = str(c1 + (perBeat / (note['duration'] * 2)))
									out += c3 + " On ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=" + str(actualVolume) + "\n"
								if 'fours' in note:
									c3 = perBeat / (note['duration'] * 4)
									c4 = str(c1 + (c3))
									out += c4 + " On ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=" + str(actualVolume) + "\n"
									c4 = str(c1 + c3 + c3)
									out += c4 + " On ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=" + str(actualVolume) + "\n"
									c4 = str(c1 + c3 + c3 + c3)
									out += c4 + " On ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=" + str(actualVolume) + "\n"
							# when do we turn off
							# divide
							c3 = str(c1 + (perBeat / note['duration']))
							for surface in note['surface']:
								# why do i sometimes see the note off volume at 64?
								#out += c3 + " Off ch=" + channelString + " n=" + noteMap[instrument][ surface ] + " v=0\n"
								pass

							# i bet some cymbal notes we'll have to avoid turning off until we get an explicit choke note

						c1 += (perBeat / note['duration']) # how long does this note last?
					nextBeat += perBeat
					counter += perBeat
					# end note loop
				# end beat loop
			# end measure loop
			out += "TrkEnd\n"

			channel += 1
		# end instrument loop
		return out

class MusicXMLConvertor(Convertor):
	durationMap = {
		1: 'quarter',
		2: 'eighth',
		3: 'eighth',
		4: '16th',
		5: '16th',
		6: '16th',
		7: '16th',
		8: '32nd'
	}
	beamMap = {
		2: '1',
		3: '1',
		4: '2',
		5: '2',
		6: '2',
		7: '2',
		8: '3',
	}
	dynamicMap = {
		'O': 'pp',
		'P': 'p',
		'M': 'mf',
		'F': 'f',
		'G': 'ff'
	}
	noteHeads = {
		'x': 'x'
	}

	def convert(self, score, settings):
		nl = "\n"
		t = "\t"
		t2 = t + t
		t3 = t + t + t
		t4 = t + t + t + t

		instrumentOrder = ['snare','tenor','bass','cymbal']

		noteMap = {
			# snare
			"h": "C5",
			"x": "C5",

			# bass and tenor
			"a": "E5",
			"b": "C5",
			"c": "A4",
			"d": "F4",
			"e": "D4"
		}

		out = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>' + nl + '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 2.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">' + nl
		out += '<score-partwise version="2.0">' + nl
		if 'title' in score:
			out += '<work>' + nl
			out += t + '<work-title>' + score['title'] + '</work-title>' + nl
			out += '</work>' + nl
		if 'author' in score:
			out += '<identification>' + nl
			out += t + '<creator type="composer">' + score['author'] + '</creator>' + nl
			out += t + '<rights>Copyright 2010 ' + score['author'] + '</rights>' + nl
			out += '</identification>' + nl
		out += '<part-list>' + nl

		i = 1
		for instrument in instrumentOrder:
			if not instrument in score['instruments']:
				continue
			music = score['instruments'][ instrument ]
			out += t + '<score-part id="P' + str(i) + '">' + nl
			out += t2 + '<part-name>' + instrument + '</part-name>' + nl
			#out += t2 + '<midi-instrument id="P' + str(i) + 'i">' + nl
			#out += t3 + '<midi-channel></midi-channel>' + nl
			#out += t3 + '<midi-program></midi-program>' + nl
			#out += t3 + '<midi-unpitched></midi-unpitched>' + nl
			#out += t2 + '</midi-instrument>' + nl
			out += t + '</score-part>' + nl
			i += 1
		out += '</part-list>' + nl

		i = 1
		for instrument in instrumentOrder:
			if not instrument in score['instruments']:
				continue
			music = score['instruments'][ instrument ]
			out += '<part id="P' + str(i) + '">' + nl
			prevTimeSignature = ''
			iMeasure = 1
			for measure in music:
				ts = measure['timeSignature'].split('/')
				out += t + '<measure number="' + str(iMeasure) + '">' + nl
				out += t2 + '<attributes>' + nl
				# divisions per quarter note for 1 duration
				out += t3 + '<divisions>12</divisions>' + nl
				if iMeasure == 1:
					out += t3 + '<key><fifths>0</fifths><mode>major</mode></key>' + nl
				if prevTimeSignature <> measure['timeSignature']:
					out += t3 + '<time symbol="common"><beats>' + str(ts[0]) + '</beats><beat-type>' + str(ts[1]) + '</beat-type></time>' + nl
				if iMeasure == 1:
					out += t3 + '<clef><sign>percussion</sign></clef>' + nl
				out += t2 + '</attributes>' + nl
				for beat in measure['beats']:
					iNote = 1
					for note in beat:
						if 'rest' in note:
							duration = note['duration']
							out += t2 + '<note>' + nl
							out += t3 + '<rest />' + nl
							out += t3 + '<duration>' + str(12 / note['duration']) + '</duration>' + nl
							out += t3 + '<type>' + str(self.durationMap[ note['duration'] ]) + '</type>' + nl
							if duration == 3:
								out += t3 + '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>' + nl
							elif duration == 6:
								out += t3 + '<time-modification><actual-notes>6</actual-notes><normal-notes>4</normal-notes></time-modification>' + nl

							if note['duration'] > 1:
								out += t3 + '<beam>'
								if iNote == 1:
									out += 'begin'
								elif iNote == note['duration']:
									out += 'end'
								else:
									out += 'continue'
								out += '</beam>' + nl
							out += t2 + '</note>' + nl
						else:
							iSurface = 1
							for surface in note['surface']:

								if 'dynamicChange' in note or 'dynamicChangeEnd' in note:
									out += t2 + '<direction><direction-type><wedge type="'
									if 'dynamicChange' in note:
										if note['dynamicChange'] == '<':
											out += 'crescendo'
										else:
											out += 'diminuendo'
									else:
										out += 'stop'
									out += '">'
									out += '</wedge></direction-type></direction>' + nl

								duration = note['duration']
								out += t2 + '<note>' + nl

								if iSurface > 1: # simultaneous notes
									# this note is in a chord with the previous
									out += t3 + '<chord />' + nl

								noteMapped = noteMap[ surface ]
								out += t3 + '<unpitched><display-step>' + noteMapped[0] + '</display-step><display-octave>' + noteMapped[1] + '</display-octave></unpitched>' + nl

								out += t3 + '<duration>' + str(12 / note['duration']) + '</duration>' + nl
								#out += t3 + '<voice>' + str(iSurface) + '</voice>' + nl
								out += t3 + '<type>' + str(self.durationMap[ note['duration'] ]) + '</type>' + nl

								if duration == 3:
									out += t3 + '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>' + nl
								elif duration == 6:
									out += t3 + '<time-modification><actual-notes>6</actual-notes><normal-notes>4</normal-notes></time-modification>' + nl
									pass

								out += t3 + '<stem>up</stem>' + nl

								if 'shot' in note:
									out += t3 + '<notehead>x</notehead>' + nl
								elif surface in self.noteHeads:
									out += t3 + '<notehead>' + self.noteHeads[ surface ] + '</notehead>' + nl

								if note['duration'] > 1:
									out += t3 + '<beam>' # number="' + self.beamMap[ note['duration'] ] + '">'
									if iNote == 1:
										out += 'begin'
									elif iNote == note['duration']:
										out += 'end'
									else:
										out += 'continue'
									out += '</beam>' + nl

								if duration == 3 or duration == 6 or 'accent' in note or 'diddle' in note or 'dynamic' in note:
									out += t3 + '<notations>' + nl

								# for tuplet bracket, need to know whether first or last note in tuplet
								if duration == 3:
									#out += t4 + '<tuplet />' + nl
									pass
								if duration == 6:
									pass
								if 'diddle' in note:
									out += t4 + '<ornaments><tremolo type="single">1</tremolo></ornaments>' + nl
								if 'accent' in note :
									out += t4 + '<articulations><accent placement="above"></accent></articulations>' + nl
								if 'dynamic' in note:
									out += t4 + '<dynamics placement="below"><' + self.dynamicMap[ note['dynamic'] ] + ' /></dynamics>' + nl
								if duration == 3 or duration == 6 or 'accent' in note or 'diddle' in note or 'dynamic' in note:
									out += t3 + '</notations>' + nl

								if 'sticking' in note:	
									out += t3 + '<lyric placement="below"><text>' + note['sticking'] + '</text></lyric>' + nl

								out += t2 + '</note>' + nl

								iSurface += 1
						iNote += 1
					# end note loop
				# end beat loop
				iMeasure += 1
				prevTimeSignature = measure['timeSignature']

				out += t + '</measure>' + nl
			# end measure loop
			out += '</part>' + nl
			i += 1
		# end instrument loop
		out += '</score-partwise>'
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

	# or fixDurations
	def fixDurations(self, score):
		# fix durations and set tuplet flags
		# tuplet flags may already be set in some cases by left/right square brackets

		# 1=4, 2=8, 3=8tuplet, 4=16, 5=16tuplet, 6=16tuplet, 7=16tuplet, 8=32
		for (instrument,music) in score['instruments'].items():
			for measure in music:
				for beat in measure['beats']:
					for note in beat:
						# if tuplet and (last note in a beat, or no longer tuplet), close tuplet
						# is last beat?
						if note['duration'] == 3:
							duration = 8

						elif note['duration'] > 4 and note['duration'] < 8:
							duration = 16

						elif note['duration'] == 1 or note['duration'] == 2 or note['duration'] % 4 == 0:
							duration = note['duration'] * 4

						note['duration'] = duration

						# should i set shot flag here too?
		return score

	def convert(self, parsed, settings={}):
		#a = self.flams(parsed)
		a = self.fixDurations(parsed)

		ret = '\\version "2.8.7"\n'
		#ret += '#(set-default-paper-size "a4" \'landscape)'
		# this doesn't do enough. lilypond feels like a waste of effort.
		ret += '\t\\paper {\n'
		ret += '\t\tbetween-system-padding = #0.1\n'
		ret += '\t\tbetween-system-space = #0.1\n'
		ret += '\t\tragged-last-bottom = ##f\n'
		ret += '\t\tragged-bottom = ##f\n'
		ret += '\t}\n'

		ret += '\\header {\n'
		if 'title' in a:
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
			'O': '\\pp',
			'P': '\\p',
			'M': '\\mf',
			'F': '\\f',
			'G': '\\ff',
	
			'<': '\\<',
			'>': '\\>',
			':': '\\!'
		}

		# set this flag when we encounter one of them
		# unset it when we encounter the first dynamic that's not one
		crescendoDecrescendo = False
		dynamic = 'M'

		instruments = a['instruments']
		instruments2 = ['snare','tenor','bass','cymbal']

		for instrument in instruments2:
			if not instrument in instruments.keys():
				continue

			music = instruments[ instrument ]
			
			if instrument == 'snare':
				ret += '\t% Snare\n'
				ret += '\t\\new Staff {\n'
				#ret += '\t\t\\set Staff.midiInstrument = "electric grand"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Snare "\n'

				#self.beaming()
				if 'timesignature' in a:
					ret += '\t\t\\time ' + a['timesignature'] + '\n'

			elif instrument == 'tenor':
				ret += '\t% Tenor\n'
				ret += '\t\\new Staff {\n'
				#ret += '\t\t\\set Staff.midiInstrument = "bright acoustic"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Tenor "\n'
				if 'timesignature' in a:
					ret += '\t\t\\time ' + a['timesignature'] + '\n'

			elif instrument == 'bass':
				ret += '\t% Bass\n'
				ret += '\t\\new Staff {\n'
				#ret += '\t\t\\set Staff.midiInstrument = "acoustic grand"\n'
				ret += '\t\t\\set Staff.instrumentName = #"Bass "\n'
				if 'timesignature' in a:
					ret += '\t\t\\time ' + a['timesignature'] + '\n'

			elif instrument == 'cymbal':
				ret += '\t% Cymbals\n'
				ret += '\t\\new Staff {\n'
				#ret += '\t\t\\set Staff.midiInstrument = "honky-tonk"\n'
				ret +='\t\t\\set Staff.instrumentName = #"Cymbals "\n'
				if 'timesignature' in a:
					ret += '\t\t\\time ' + a['timesignature'] + '\n'

			ret += '\t\t\\stemUp\n'

			iMeasure = 1
			for measure in music:
				beats = len(measure['beats'])

				# if measure has a time signature, print it
				# but it's a bitch when doing it when a crescendo hasn't ended

				for beat in measure['beats']:
					for note in beat:
						if 'tupletStart' in note:
							if note['tupletStart'] == 3:
								ret += '\\times 2/3 { '
							else:
								ret += '\\times 4/6 { '


						if 'flam' in note:
							if instrument == 'snare':
								ret += '\\override Stem #\'length = #4 \\appoggiatura c\'\'8 \\revert Stem #\'length \stemUp '
							else: # tenor and bass flam element has surface
								ret += '\\override Stem #\'length = #4 \\appoggiatura ' + mapping[ note['flam'] ] + '8 \\revert Stem #\'length \stemUp '


						# note or rest?
						if 'rest' in note:
							ret += 'r' + str(note['duration'])
						else:
							if len(note['surface']) > 1:
								ret += ' <<'
							for surface in note['surface']:
								if 'shot' in note:
									ret += '\\override NoteHead #\'style = #\'cross '
									ret += mapping[ surface ] + str(note['duration'])

								# elif 'choke' in note:
								# elif 'slide' in note:
								# elif 'tap' in note:
								else:
									ret += mapping[ surface ] + str(note['duration'])

								# diddle?
								# check flag for whether to expand tremolos
								if 'diddle' in note:
									ret += ':' + str(note['duration'] * 2)

								# fours?
								if 'fours' in note:
									ret += ':' + str(note['duration'] * 4)

								if 'dynamicChangeEnd' in note:
									ret += '\! '

								if 'dynamic' in note:
									ret += mapping[ note['dynamic'] ] + ' '

								if 'dynamicChange' in note:
									ret += mapping[ note['dynamicChange'] ] + ' '

								# should note be accented?
								if 'accent' in note:
									#ret += ' \\accent'
									ret += ' ^>'

								if 'shot' in note:
									ret += ' \\revert NoteHead #\'style'

								ret += ' '

							if len(note['surface']) > 1:
								ret += ' >>'


						if 'tupletStop' in note: # last note in a tuplet
							ret += '} '

						ret += ' '
					# end note loop

				# end beat loop

				if len(measure['beats']) > 1:
					ret += ' | '

				ret += ' \n '
				if iMeasure == 4:
					if len(measure['beats']) > 1:
						ret += ' \\break \n '
					iMeasure = 1
				else:
					iMeasure += 1
			# end measure loop

			ret += '}\n'
		# end instrument loop

		ret += '>>\n'
		ret += '\t\\layout {\n'
		#print('\t\tindent = 0')
		ret += '\t}\n'
		ret += '}\n'
		return ret
