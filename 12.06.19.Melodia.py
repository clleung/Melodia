###############################################################################
# Final - Melodia
#
#Name: Cho-Lin (Lisa) Leung
#Andrew ID: clleung
#Date: December 6, 2019
#
###############################################################################
###############################################################################
#Imports:
import math, copy
import random
from cmu_112_graphics import *
from tkinter import *
from PIL import Image 
import sys
import aubio
#
###############################################################################
###############################################################################
'''
General Citations:
    Framework taken from:
    http://www.cs.cmu.edu/~112/notes/notes-animations-part2.html#subclassingModalApp

Transcription Mode:
    from 15-112 Aubdio demo shared folder: 
    aubio_demo.py by Evan Zeng
    merged with modified version of:
    https://github.com/aubio/aubio/blob/master/python/demos/demo_tempo.py
    and
    https://github.com/aubio/aubio/blob/master/python/demos/demo_onset.py

    returns the time for a quarter note (b/c melodia only works in 4/4 meter)
    and returns all of the onsets for notes
'''
###############################################################################
###############################################################################

class SplashScreenMode(Mode):

    def keyPressed(mode, event):
        mode.app.setActiveMode(mode.app.startOptionsMode)
    def redrawAll(mode, canvas):
        font = 'Verdana 20 bold'
        font2 = "Verdana 12"
        x = mode.width/2
        y = 150
        dy = 100
        canvas.create_text(x, y, text="Welcome to Melodia! Let's make music!", 
            font=font)
        y += dy
        canvas.create_text(x, y, text = ("Image Processing will let you look at samples with arrow keys " 
                                + "and let you input your own piece!"), font=font2)
        y += dy
        canvas.create_text(x, y, text = ("Transcribe Audio will let you choose"
                                + " a file and convert it into sheet music!"), font=font2)
        y += dy
        canvas.create_text(x, y, text = ("View Pieces will let you open the previous images you've saved!"),
                                font = font2)
        y += dy
        canvas.create_text(x, y, text='Press any key to start!'
            , font=font)

class Measure():
    #starts at one b/c of musical convention; first measure always starts at 1
    mNum = 1
    def __init__(self, mode, notes):
        self.mode = mode
        self.mNum  = Measure.mNum
        #note: needed to separate self.mNum from Measure.mNum bc incrementing
        #Measure.mNum within the constructor without assigning a value to it 
        #makes ALL instances of the measure object equal to the total number of measures
        #significant when differentiating the individual measures
        #important for future editing/features (exp: providing measure numbers each line or copy/pasting)
        Measure.mNum += 1
        self.notes = notes
    #CHECK - probably unnecessary 
    def __repr__(self):
        return (f"Measure({self.notes})")

    def measureLen(self):
        pass

    def posInfo(self):
        newNotes = []
        for note in (self.notes):
            info = Note.noteInfo(note)
            newNotes.append(info)
        return newNotes
        
    def drawMeasure(self, canvas, x, y):
        '''
        assume that x,y is the top left corner of the measure including buffer space
        '''
        #b/c bt 1 is ALWAYS at the same position
        beat1Center = 50
        beatDiff = 75
        measureHeight = 50
        indivBarHeight = measureHeight // 6
        #
        #print("drawM", beat1Center, beatDiff, measureHeight, indivBarHeight)
        noteCenter = beat1Center

        for note in self.notes:
            isSharp = False
            #assigned bc it will change
            #horizontal movement
            
            noteSpacing = note.getNoteSpace()

            #vertical movement
            notePitch = note.getPitchPos()
            #checks to see if sharps need to be drawn
            if(notePitch % 1 != 0): isSharp = True
            #turn notePitch into an int b/c A4 and A#4 have the same position, just
            #an attachment with it
            if(notePitch > 0): 
                pitchPos = 12 - int(notePitch)
            else:
                pitchPos = 12 + int(notePitch)

            pitchPlacement = pitchPos * indivBarHeight 
            #print("isS,nP", isSharp, notePitch)
            #print("nC, pp", noteCenter, pitchPlacement)
            if(note.noteType == "wh"):
                y += 20
            note.drawNote(canvas, x + noteCenter, y + pitchPlacement)
            noteCenter += noteSpacing*beatDiff

class Note():
    def __init__(self, mode, beat, duration, pitch):
        self.mode = mode
        #will refine beat and duration here to fit with the image processing
        self.beat = beat
        self.duration = duration
        self.pitch = pitch
        #print("NEW", self.beat, self.duration, self.pitch, self.mode.qtr)
        #note: can call methods of the class within the constructor, just don'f
        #forget to call it by self.methodName(parameters not inc. self)
        self.qtr = AnalyzeFile.qtrTime
        self.noteType = str(self.getNoteType())
        self.noteSpace = self.getNoteSpace()
        self.noteImage = self.mode.allNoteImagesDict[self.noteType]

    def __repr__ (self):
        return (f"(Note({self.beat}, {self.duration}, {self.pitch}))")
        
    def roundDur(self, qtr):
        
        dur = self.duration
        noteVals = [qtr/4, qtr/2, qtr, 2*qtr, 4*qtr]
        setNoteVals = set(noteVals)
        '''
        noteVals = [qtr/4, qtr/2, qtr/2 + qtr/4, qtr, qtr, qtr + qtr/2, 2*qtr, 
                    2*qtr + qtr, 4*qtr]
        '''
        roundedDur = qtr/4
        if (dur not in setNoteVals):
            prevVal = dur
            #if(dur < qtr/8): return 0
            for i in noteVals:
                #qtr = 1, notedur = 1
                if(dur == i):
                    roundedDur = i
                    break
                elif(dur > i):
                    prevVal = i
                elif(dur < i and dur > prevVal):
                    if(abs(i - dur) > abs(dur - prevVal)):
                        roundedDur = prevVal
                        break
                    else:
                        roundedDur = i
                        break
    
        return roundedDur

    #'translate' the three parameters(beat, duration, pitch) for drawing
    @staticmethod
    def dictNoteTypes(qtr):
        noteType = {
                    qtr/4: "sx", 
                    qtr/2: "ei", 
                    #qtr/2 + qtr/4: "dei", 
                    qtr: "qt", 
                    #qtr + qtr/2: "dqt", 
                    2*qtr: "hf", 
                    #2*qtr + qtr: "dhf", 
                    4*qtr:"wh"
        }
        return noteType
        
    def getNoteType(self):
        qtr = self.qtr
        if(qtr == 0):
            pass
        dur = self.roundDur(qtr)
        #print("HERE", dur, self.duration)
        self.duration = dur
        #print(qtr, dur)
        noteType = Note.dictNoteTypes(qtr)
        #print(noteType, noteType[dur])
        return noteType[dur]

    def getNoteSpace(self):
        #gets the duration in time
        qtr = self.qtr
        noteType = Note.dictNoteTypes(qtr)
        for key in noteType:
            if noteType[key] == self.noteType:
                return key
        return None

    @staticmethod
    def allPitchPos():
        #sharps will be at the same positon as the note after (exp:  A#, A), but
        #keeping .5 for drawing the sign "#"
        #for identification, mod values by 1 to see if they're floats
        #or use isinstance cuz it would do the exact same thing
        pitchPos = {
                    "G3":  -3,
                    "A#3": -2.5,
                    "A3":  -2,
                    "B#3": -1.5,
                    "B3":  -1,
                    "C4":   0,
                    "C#4":  0.5,
                    "D4":   1,
                    "D#4":  1.5,
                    "E4":   2,
                    "F4":   3,
                    "F#4":  3.5,
                    "G4":   4,
                    "A#4":  4.5,
                    "A4":   5,
                    "B#4":  5.5,
                    "B4":   6,
                    "C5":   7,
                    "C#5":  7.5,
                    "D5":   8,
                    "D#5":  8.5,
                    "E5":   9,
                    "F5":   10,
                    "F#5":  10.5,
                    "G5":   11,
                    "A#5":  11.5,
                    "A5":   12,
                    "B#5":  12.5,
                    "B5":   13,
                    "C6":   14

        }
        return pitchPos

    def getPitchPos(self):
        pitchPos = Note.allPitchPos()
        return pitchPos[self.pitch]

    def getBeatPos(self):
        return self.beat

    def noteInfo(self):
        beat, dur, pitch = self.beat, self.duration, self.pitch

        beatPos = getBeatPos(self)
        pitchPos = getPitchPos(self)
        newDur = getNoteType(self)

        return (beatPos, pitchPos, newDur)

    def drawNote(self, canvas, x, y):
        #print(x, y)
        #rotate notes above (and inc??) A5
        #canvas.create_text(x, y + 30, text = (self.beat, self.duration, self.pitch, self.noteType))
        canvas.create_text(x, y + 30, text = (self.pitch))
        canvas.create_image(x, y, image = ImageTk.PhotoImage(self.noteImage))

class SampleNote(Note):
    @staticmethod
    def calculateQtr(bpm):
        #calculate bpm with aubio, pass in!!!
        #finding seconds per beat, or per qtr note
        secPerMin = 60
        #bc the 
        spb = secPerMin / bpm
        return spb
    def roundDur(self, qtr):
        roundedDur = None
        dur = self.duration
        noteVals = [qtr/4, qtr/2, qtr/2 + qtr/4, qtr, qtr, qtr + qtr/2, 2*qtr, 
                    2*qtr + qtr, 4*qtr]

        if (dur not in noteVals):
            #find the nearest noteVal
            #using qtr/8 to cut out possible harmonics/errors
            prevVal = dur
            if(dur < qtr/8): return 0
            for i in noteVals:
                if(dur > i):
                    prevVal = i
                elif(dur < i and dur > prevVal):
                    if((i - dur) > (dur - prevVal)):
                        roundedDur = preVal
                    else:
                        roundedDur = i
        else:
            roundedDur = dur
        return roundedDur
    def getNoteSpace(self):
        #gets the duration in time
        qtr = SampleNote.calculateQtr(60)
        noteType = Note.dictNoteTypes(qtr)
        for key in noteType:
            if noteType[key] == self.noteType:
                return key
        return None
    def getNoteType(self):
        qtr = SampleNote.calculateQtr(60)
        dur = self.roundDur(qtr)
        noteType = Note.dictNoteTypes(qtr)
        return noteType[dur]

class AnalyzeFile():
    qtrTime = 0
    def __init__(self, mode, filename):
        self.mode = mode

        self.filename = filename
        #self.qtr = None

        (self.qtr, self.onsets, self.beats) = self.getTempo()
        #need to/can make a class attr b/c only one audio file is analyzed at a time
        #(even if I analyzed more than one, i can't do multiple at once so it's fine)
        #need to send it to the Note class for the spacing of notes
        AnalyzeFile.qtrTime = self.qtr
        #stored in the constructor for easy access--particularly with regards to visualization later
        #also debugging 
        self.pitchLst = self.getPitch()
        self.noteLst = self.detect()
        #12.03 MERGE STUFF HERE
        self.revisedNotes = self.mergePitchAndNote()
        self.audioData = self.findTheBeat()
        #the only list that is sent to the mode
        #it provides the list of notes within each measure
        self.convertedData = self.analyzeFile()
        #the mode will receive self.filename (unedited), self.convertedData, and self.qtr

    @staticmethod
    def roundTime(n):
        num = round(n*100)
        return num/100
    #delete in final if no longer used
    def roundByQtr(self, qtr, note):
        roundedDur = 0
        noteVals = [qtr/4, qtr/2, qtr/2 + qtr/4, qtr, qtr, qtr + qtr/2, 2*qtr, 
                    2*qtr + qtr, 4*qtr, ]

        if (note not in noteVals):
            prevVal = note
            if(note < qtr/4): return 0
            for i in noteVals:
                if(note == i):
                    roundedDur = i
                elif(note > i):
                    prevVal = i
                    
            return roundedDur

    def getTempo(self):
        filename = self.filename

        samplerate = 44100 
        win_tempo = 512
        hop_tempo = win_tempo // 2
        #Note: clean this up before due date!
        sTempo = self.mode.app.aubio.source(filename, samplerate, hop_tempo)
        s = self.mode.app.aubio.source(filename, samplerate, hop_tempo)
        tempo_o = self.mode.app.aubio.tempo("default", win_tempo, hop_tempo, samplerate)
        onseto = self.mode.app.aubio.onset("default", win_tempo, hop_tempo, samplerate)
        
        delay = 4. * hop_tempo
        beats = []
        onsets = []

        #mememe
        numBeat = 0
        secPBeat = 0
        diffBeats = 0
        prevBeat = None
        #end

        # total number of frames read
        total_framesTempo = 0
        while True:
            samplesTempo, readTempo = sTempo()
            is_beat = tempo_o(samplesTempo)
            
            if(onseto(samplesTempo)):
                onsets.append(onseto.get_last_s())
            if is_beat:
                this_beat = int(total_framesTempo - delay + is_beat[0] * hop_tempo) 
                beat = (this_beat / float(samplerate))
                beats.append(beat)
                #mememe
                if(numBeat != 0):
                    secPBeat += beat - prevBeat
                    prevBeat = beat
                    diffBeats += 1
                else:
                    prevBeat = beat
                numBeat += 1

            total_framesTempo += readTempo
            if readTempo < hop_tempo: break

        avgspb = (secPBeat / diffBeats)
        avgsec = self.roundTime(avgspb)

        fileTime = beats[-1]

        return avgsec, onsets, beats

    #returns a tuple
    def getPitch(self):
        #mememememememe
        filename = self.filename
        samplerate = 44100 
        win_pitch = 4096
        hop_pitch = 512  
        print(filename)
        sPitch = self.mode.app.aubio.source(filename, samplerate, hop_pitch)

        tolerance = 0.8
        
        pitch_o = self.mode.app.aubio.pitch("yin", win_pitch, hop_pitch, samplerate)
        pitch_o.set_unit("freq") #not MIDI!!
        pitch_o.set_tolerance(tolerance)
        
        pitches = []
        confidences = []
        #mememe
        pitchLstDict = []
        pitchLstAubi = []
        allPitchesDict = set()
        allPitchesAubi = set()
        #end
        # total number of frames read
        total_framesPitch = 0
        
        delay = 4. * (hop_pitch//2)
        while True:
            samplesPitch, readPitch = sPitch()
            pitch = pitch_o(samplesPitch)[0]
            confidence = pitch_o.get_confidence()
            
            #memememe
            if(confidence > 0.85):
                if(pitch > 80 and pitch  < 1100):
                    note = self.mode.app.aubio.freq2note(pitch)
                    confidence = pitch_o.get_confidence()
                
                if((len(pitchLstAubi) < 1)):
                    total = int(total_framesPitch - delay)  
                    pitchTime = total / float(samplerate)
                    noteAndTime = (note, pitchTime)
                    pitchLstAubi.append(noteAndTime)

                (lastPitch, lastTime) = pitchLstAubi[-1]
                if((len(pitchLstAubi) >= 1 and (note != lastPitch))):
                    total = int(total_framesPitch - delay + lastTime * hop_pitch) 
                    pitchTime = total / float(samplerate)
                    noteAndTime = (note, pitchTime)
                    pitchLstAubi.append(noteAndTime)
                #end

            total_framesPitch += readPitch
            if readPitch < hop_pitch: break

        return pitchLstAubi

    #mememe
    def detect(self):
        filename = self.filename
        
        #makes sure to add the last pitch (or else it's None)
        (lastPitch, lastBeat) = self.pitchLst[-1]
        #(qtrTime, onsets, beats) = self.getTempo()
        print("HI", self.qtr)
        # self.qtr = qtrTime
        #self.changeQtr(qtrTime)
        #same thing but with tempo
        self.pitchLst.append( (lastPitch, self.beats[-1]) )
        #smallest note being accounted for
        sxNote = (self.qtr / 4)
        roundedSxNote = self.roundTime(sxNote)
        #must put the value back in bc duration is found by finding the difference; loses that first value
        notes = [self.onsets[0]]
        isFirst = True
        lastNote = None
        for currNote in self.onsets:
            if(isFirst == False):
                note = self.roundTime(currNote - prevNote)
                #excludes notes smaller than sixteenths
                if(note >= roundedSxNote):
                    notes.append(note)
            else:
                prevNote = currNote
                isFirst = False
        notes.append(self.roundTime(self.beats[-1]))
        return (notes)

    def findPitch(self, note):
        #connects pitch with the duration of the note
        isFirst = True
        prevTime = None
        prevPitch =  None
        notePitch = None
        #print(pitchLst)
        for i in range (len(self.pitchLst)):
            (pitch, currTime) = self.pitchLst[i]
            if(i != 0):
                if(note > prevTime and note < currTime):
                    notePitch = prevPitch
                    break
                elif(note > currTime and (i == len(self.pitchLst) - 1)):
                    notePitch = pitch

            prevTime = currTime
            prevPitch = pitch

        return notePitch

    def mergeLongNotes(self):
        #merges notes longer than a qtr note
        revised = []

        for i in range(len(noteInfo)):
            (note, pitch) = noteInfo[i]
            if (i != 0):
                if(prevPitch == pitch):
                    newNote = self.roundTime(prevNote + note)
                    noteInfo[i-1] = (newNote, pitch)
                else:
                    revised.append( (note, pitch) )
            else:
                revised.append( (note, pitch) )

            prevNote = note
            prevPitch = pitch
        return revised

    def mergePitchAndNote(self):
        noteInfo = []
        for note in self.noteLst:
            if(note != 0):
                pitch = self.findPitch(note)
                noteInfo.append( (note, pitch) )
        #no merging
        #revisedNotes = self.mergeLongNotes(noteInfo)
        revisedNotes = noteInfo
        return (revisedNotes)
    
    @staticmethod
    def dictAllBeats(qtr):
        beatVals = {
                    qtr/4: 0.25, 
                    qtr/2: 0.5, 
                    #qtr/2 + qtr/4: "dei", 
                    qtr: 1,
                    #qtr + qtr/2: "dqt", 
                    2*qtr: 2, 
                    #2*qtr + qtr: "dhf", 
                    4*qtr: 4
        }
        return beatVals
        
    def getTrueNoteType(self, dur):
        trueBeat = 0
        qtr = self.qtr
        noteVals = [qtr/4, qtr/2, qtr, 2*qtr, 4*qtr]
        setNoteVals = set(noteVals)
        
        '''
        noteVals = [qtr/4, qtr/2, qtr/2 + qtr/4, qtr, qtr, qtr + qtr/2, 2*qtr, 
                    2*qtr + qtr, 4*qtr]
        '''
        roundedDur = qtr/4
        if (dur not in setNoteVals):
            prevVal = dur
            #if(dur < qtr/8): return 0
            for i in noteVals:
                #qtr = 1, notedur = 1
                if(dur == i):
                    roundedDur = i
                    break
                elif(dur > i):
                    prevVal = i
                elif(dur < i and dur > prevVal):
                    if(abs(i - dur) > abs(dur - prevVal)):
                        roundedDur = prevVal
                        break
                    else:
                        roundedDur = i
                        break
                        
        trueBeat = (AnalyzeFile.dictAllBeats(qtr))[roundedDur]
        return trueBeat      

    def findTheBeat(self):
        isFirst = True
        finalLst =  []
        sumBeat = 1
        prevNoteVal = 0
         
         #fix the assignment of beats
        for n in range(len(self.revisedNotes) - 1):
         #account for last note please
         #for (note, pitch) in self.revisedNotes:
            #print(note, pitch)
            (note, pitch) = self.revisedNotes[n]
            newNoteVal = note - prevNoteVal
            #mod 4 because i'm using 4/4 meter
            typeBeat = self.getTrueNoteType(newNoteVal)
            if(isFirst == True):
                 info = (sumBeat, newNoteVal, pitch)
                 finalLst.append(info)
                 prevNoteVal = note
                 isFirst = False

            sumBeat += typeBeat
            if(sumBeat > 4): 
                sumBeat = 1
                isFirst = True
                

            info = (sumBeat, newNoteVal, pitch)
            
            finalLst.append(info)
            prevNoteVal = note
         
        return finalLst
        
    '''
    format:
    Measure(mode, [Note(mode, 1, 1, "B4"), Note(mode, 2, 1, "A4"), Note(mode, 3, 2, "G4")])
    '''
    def analyzeFile(self):
        convertedLst = []
        noteLst = []
        #beat1 = 0
        data = self.audioData
        print("data", data)
        for i in range(len(data) - 1):
            (beat, dur, pitch) =  data[i]
            (nextBeat, nextDur, nextPitch) = data[(i + 1)]
            print(i, data[i], data[(i + 1)])
            if(pitch == None): continue
            elif(i == 0):
                print("zero")
                #beat1 = beat
                newNote = Note(self.mode, beat, dur, pitch)
                noteLst.append(newNote)

            elif((beat + nextDur) >= 4):
                print("hiya", (beat + nextBeat))
                newNote = Note(self.mode, beat, dur, pitch)
                noteLst.append(newNote)

                if((len(noteLst)) > 0):
                    newMeasure = Measure(self.mode, noteLst)
                    convertedLst.append(newMeasure)
                    noteLst = []
            else:
                newNote = Note(self.mode, beat, dur, pitch)
                noteLst.append(newNote)

        return convertedLst

class TranscriptionMode(Mode):
    #CITATIONS
    #from 15-112 Aubdio demo shared folder: 
    #aubio_demo.py by Evan Zeng
    #merged with modified version of:
    #https://github.com/aubio/aubio/blob/master/python/demos/demo_tempo.py
    #and
    #https://github.com/aubio/aubio/blob/master/python/demos/demo_onset.py
    def appStarted(mode):  
        mode.toHome = Button(mode, "Home", 1225, 10, 100, 30, "blue")
        mode.newAudio = Button(mode, "New Piece", 1050, 10, 200, 30, "pink")
        mode.save = Button(mode, "Save", 30, 10, 30, 30, "deep sky blue")

        mode.allButtons = [mode.toHome, mode.newAudio, mode.save]
        mode.image = None
        mode.timerDelay = 50

        #loaded images in app b/c they're needed in transcription mode and
        #use samples mode
        #for some reason, I couldn't stick any other methods in app
        mode.allBufferDict = mode.app.loadBufferImages()
        mode.allNoteImagesDict = mode.app.loadNoteImages()

        mode.resetFile()
    
    def resetFile(mode):
        mode.filename = ""
        mode.convertedFile = None
        mode.qtr = None
    
    #modified from: https://pythonspot.com/tk-file-dialogs/
    def runFileDialog(mode):
        root = Tk()
        #just changed the filetypes to wav files
        root.filename = mode.app.filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("WAV files","*.wav"),("all files","*.*")))
        #mememememe the rest is what i wrote to crop out the name of just the file
        #instead of C:/Users/Lisa/Documents/112 Term Project/hot_cross_buns.wav
        #it returns hot_cross_buns.wav
        filename = ""
        for i in range(len(root.filename) - 1, 0, -1):
            if(".wav" not in root.filename): return ""
            if((root.filename)[i] == "/"):
                filename = (root.filename)[(i + 1):]
                return filename
        return ""

    #modified from: https://docs.python.org/3.9/library/tkinter.messagebox.html
    def leaveFileDialog(mode):
        #i added the variable so I know what answer the user chooses (yes/no)
        answer = messagebox.askyesno(title=None, message="Would you like to quit?")
        return answer

    def mousePressed(mode, event):
        for b in mode.allButtons:
            if(b.intersects(event.x, event.y) == True):
                b.click()
    
    def timerFired(mode): 
        if(mode.toHome.isClicked == True):
            mode.app.setActiveMode(mode.app.startOptionsMode)
            mode.toHome.unclick()
        elif(mode.newAudio.isClicked == True):
            mode.resetFile()
            mode.newAudio.unclick()

        if(mode.save.isClicked == True):
            #from:http://www.cs.cmu.edu/~112/notes/notes-animations-part2.html#getAndSaveSnapshot
            snapshotImage = mode.app.getSnapshot()
            mode.image = mode.app.scaleImage(snapshotImage, 0.4)
            mode.app.saveSnapshot()
            mode.save.unclick()

        if (mode.filename == ""):
            userFilename = ""
            validName = False
            exit = None
            while (validName == False):
                userFilename = mode.runFileDialog()
                if(userFilename == None):
                    validName= False
                else:
                    if(".wav" in userFilename):
                        validName = True
                        break
                exit = mode.leaveFileDialog()
                if(exit == True): 
                    validName = False
                    mode.filename = "" 
                    mode.app.setActiveMode(mode.app.startOptionsMode)
                    break

            if(userFilename != None and exit != True):
                    mode.file = AnalyzeFile(mode, userFilename)
                    mode.qtr = mode.file.qtr
                    mode.filename = mode.file.filename
                    mode.convertedFile = mode.file.convertedData
                    mode.qtr = mode.file.qtr

    #only the first bar has the time signature in music
    def drawM1BufferImages(mode, canvas, x, y):
        canvas.create_image(x, y, image =  
                    ImageTk.PhotoImage(mode.allBufferDict["blank"]))
        canvas.create_image(x - 630, y - 20, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["treble"]))
        canvas.create_image(x - 595, y - 20, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["meter"]))

    def drawAllMBufferImages(mode, canvas, x, y):
        numBlanks = (mode.height // 150)
        
        for i in range (numBlanks): 
            tX = x - 630
            tY = y - 20
            canvas.create_image(x, y, image =  
                    ImageTk.PhotoImage(mode.allBufferDict["blank"]))
            canvas.create_image(tX, tY, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["treble"]))
            y += 125 
    
    def modifyName(mode):
        newTitle = mode.filename[:-4]
        modified = ""

        for i in range (len(newTitle)):
            char = newTitle[i]
            if(i == 0 or modified[i - 1] == " "):
                char = char.upper()
            if(char == "_"):
                modified += " "
            else:
                modified += str(char)
        return modified

    def drawMusic(mode, canvas):
        startX = 70
        msrNum = 1
        startY = 20
        newY = startY
        numLine = 1
        barAdj = -2
        adj = 0

        for msr in mode.convertedFile:
            if(msrNum != 1 and msrNum % 4 == 1):
                startY += 115
                startX = 70
                if(barAdj - 2 == 0):
                    newY = startY + ((barAdj - 2) * 10)
                    adj = newY
                else:
                    newY = adj + (startY//2)
            msr.drawMeasure(canvas, startX, newY)
            barAdj += 1

            if(numLine % 4 != 1):
                adjX = 75
                adjY = 30
                x0 = startX - adjX
                y0 = startY + adjY
                y1 = y0 + 80
                canvas.create_line(x0, y0, x0, y1)
            else: numLine += 1

            startX += 300
            msrNum += 1
            

    def redrawAll(mode, canvas):
        #consider also assigning measure #s here
        #but on the other hand, doing it within the class ensures that it will
        #be able to be used for other things in the future
        # canvas.create_text(mode.width/2, 20, text = (
        #                 "press 'o' to pick a file to transcribe!'" ))
        
        mode.drawM1BufferImages(canvas, 680, 100)
        mode.drawAllMBufferImages(canvas, 680, 215)

        for b in mode.allButtons:
            b.drawButton(canvas)

        if(mode.filename == None or mode.convertedFile == None or mode.qtr == 0): return
        mode.drawMusic(canvas)
        scoreTitle = mode.modifyName()

        canvas.create_text(mode.width/2, 25, text = (scoreTitle), 
                            font = "Verdana 20 bold")
        
class ViewMode(Mode):
    def appStarted(mode):
        mode.toHome = Button(mode, "Home", 1250, 650, 100, 30, "indian red")
        mode.newImage = Button(mode, "New Image", 5, 650, 100, 30, "gold")

        mode.allButtons = [mode.toHome, mode.newImage]
        mode.resetFile()

    def resetFile(mode):
        mode.image = ""
    
    #https://pythonspot.com/tk-file-dialogs/
    def openFile(mode):
        root = Tk()
        #modified it to allow for jpg and png
        root.filename =  mode.app.filedialog.askopenfilename(initialdir = "/",
            title = "Select file",filetypes = (("PNG Files","*.png"), ("JPEG Files", "*.jpg"), ("All Files","*.*")))
        #cuts it to just the filename 
        #memememee
        filename = ""
        for i in range(len(root.filename) - 1, 0, -1):
            if(".png" not in root.filename and ".jpg" not in root.filename): return ""
            #elif(".jpg" not in root.filename): return ""
            if((root.filename)[i] == "/"):
                filename = (root.filename)[(i + 1):]
                return filename
        return ""

    def pickNewImage(mode):
        #modified from: https://pillow.readthedocs.io/en/3.1.x/reference/Image.html
        image = ""
        while(image == ""):
            filen = mode.openFile()
            im = mode.app.Image.open(filen)
            #modified from: https://www.geeksforgeeks.org/python-pil-image-resize-method/
            image = im.resize( (mode.width, mode.height) )
        return image

    #modified from: https://docs.python.org/3.9/library/tkinter.messagebox.html
    def leaveFileDialog(mode):
        #i added the variable so I know what answer the user chooses (yes/no)
        answer = messagebox.askyesno(title=None, message="Would you like to quit?")
        return answer

    def mousePressed(mode, event):
        for b in mode.allButtons:
            if(b.intersects(event.x, event.y) == True):
                b.click()
                
    def timerFired(mode):
        if(mode.toHome.isClicked == True):
            mode.app.setActiveMode(mode.app.startOptionsMode)
            mode.toHome.unclick()
        elif(mode.newImage.isClicked == True):
            mode.resetFile()
            mode.image = mode.pickNewImage()
            mode.newImage.unclick()
        elif(mode.image == ""):
            mode.image = mode.pickNewImage()

    def redrawAll(mode, canvas):
        if(mode.image != ""):
            canvas.create_image(mode.width/2, mode.height/2, image =  
                        ImageTk.PhotoImage(mode.image))
        for b in mode.allButtons:
            b.drawButton(canvas)

class Button():
    #rectangular buttons
    #would make a class attrib, but don't want buttons from different screen to interact with each other
    #allButtons = []
    def __init__(self, mode, name, x, y, width, height, fill):
        self.mode = mode
        self.isClicked = False
        
        self.name = name
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.fill = fill

        self.endX = self.x + self.w
        self.endY = self.y + self.h

    #modified from:
    #http://www.cs.cmu.edu/~112/notes/notes-animations-part2.html#sidescrollerExamples

    def intersects(self, ox, oy):

        if((ox >= self.x and ox <= self.endX) and (oy >= self.y and oy <= self.endY)):
            return True
        return False

    def click(self):
        self.isClicked = True
    
    def unclick(self):
        self.isClicked = False

    def drawButton(self, canvas):
        canvas.create_rectangle(self.x, self.y, self.endX, self.endY, fill = self.fill)
        cx= self.x + (self.w/2)
        cy = self.y + (self.h/2)
        canvas.create_text(cx, cy, text = self.name)

class ImageButton(Button):
    #image from the mode
    def __init__(self, mode, name, cx, cy, image):
        self.mode = mode
        self.name = name
        self.cx = cx
        self.cy = cy
        self.image = image

        self.block = False
        self.isClicked = False

        (self.x, self.y, self.endX, self.endY) = self.getImgBounds()
    
    def getImgBounds(self):
        (width, height) = self.image.size
        (hfW, hfH) = (width / 2, height / 2)
        x = self.cx - hfW
        endX = self.cx + hfW
        y = self.cy - hfH
        endY = self.cy + hfH
        return (x, y, endX, endY)

    def intersects(self, ox, oy):
        if((ox >= self.x and ox <= self.endX) and (oy >= self.y and oy <= self.endY)):
            return True
        return False

    def background(self, canvas):
        fill = "cyan3"
        marginX = 10
        marginY = 10
        if(self.name == "Wh"):
            marginX = -10
            marginY = 0
        canvas.create_rectangle(self.x - marginX, self.y - marginY, 
                                self.endX + marginX, self.endY + marginY, fill = fill)

    def drawButton(self, canvas):
        buttonImage = self.image
        self.background(canvas)
        canvas.create_image(self.cx, self.cy, image = ImageTk.PhotoImage(buttonImage))

#would've like to subclass ImageButton but python wouldnt allow it
class NoteImageButton(ImageButton):
    def __init__(self, mode, name, cx, cy, image, val):
        super().__init__(mode, name, cx, cy, image)
        self.val = val
        
class StartOptionsMode(Mode):
    def appStarted(mode):
        mode.toSamples = Button(mode, "Image Processing", 100, 500, 300, 100, "cyan")
        mode.toTranscribe = Button(mode, "Transcribe Audio", 500, 500, 300, 100, "medium orchid")
        mode.toView = Button(mode, "View Pieces", 900, 500, 300, 100, "coral")
        mode.allButtons = [mode.toSamples, mode.toTranscribe, mode.toView]

        mode.msg = None
        (mode.x, mode.y) = (0, 0)
    
    def setMsg(mode, button, x, y):
        msg = ""
        if(button == mode.toSamples):
            msg = "Look through samples with arrows and input your own music"
            mode.msg = msg
            mode.x = x
            mode.y = y
        elif(button == mode.toTranscribe):
            msg = "Pick a WAV file and transcribe to sheet music!"
            mode.msg = msg
            mode.x = x
            mode.y = y
        elif(button == mode.toView):
            msg = "Look at all the pieces you've saved!"
            mode.msg = msg
            mode.x = x
            mode.y = y
        else:
            mode.msg = None
            mode.x = ""
            mode.y = 0

    def mouseMoved(mode, event):
        for b in mode.allButtons:
            if(b.intersects(event.x, event.y) == True):
                mode.setMsg(b, event.x, event.y)

    def mousePressed(mode, event):
        for b in mode.allButtons:
            if(b.intersects(event.x, event.y) == True):
                b.click()

    #another way
    def keyPressed(mode, event):
        if(event.key == "a"):
            mode.app.setActiveMode(mode.app.samplesMode)
        elif(event.key == "s"):
            mode.app.setActiveMode(mode.app.transcriptionMode)
        elif(event.key == "d"):
            mode.app.setActiveMode(mode.app.viewImageMode)
    
    def timerFired(mode):
        if(mode.toSamples.isClicked == True):
            mode.app.setActiveMode(mode.app.samplesMode)
            mode.toSamples.unclick()
        elif(mode.toTranscribe.isClicked == True):
            mode.app.setActiveMode(mode.app.transcriptionMode)
            mode.toTranscribe.unclick()
        elif(mode.toView.isClicked == True):
            mode.app.setActiveMode(mode.app.viewImageMode)
            mode.toView.unclick()

    def drawSetMsg(mode, canvas):
        canvas.create_text(mode.x, mode.y, text = mode.msg, font = "Verdana 12")

    def redrawAll(mode, canvas):
        canvas.create_text(mode.width/2, mode.height/2, text = "Melodia", font = "Verdana 76 bold")
        for b in mode.allButtons:
            b.drawButton(canvas)
                
        mode.drawSetMsg(canvas)

#needed to make a mode for samples b/c the data analysis portion and the sample 
#data don't interact well -- it's much cleaner this way.
#it was also done before the analysis functions were made into a class 

class UseSamplesMode(Mode):
    def appStarted(mode):
        mode.toHome = Button(mode, "Home", 1250, 5, 100, 30, "SeaGreen1")
        mode.save = Button(mode, "Save", 5, 5, 30, 30, "deep sky blue")
        mode.create = Button(mode, "Create New", 1050, 5, 200, 30, "yellow")
        mode.finished = Button(mode, "Finished!", 900, 425, 125, 50, "SteelBlue1")

        mode.allBufferDict = mode.app.loadBufferImages()
        mode.allNoteImagesDict = mode.app.loadNoteImages()
        mode.sampleDict = mode.allSamplePieces()

        #need to make the list of buttons after the image dictionary if loaded
        #b/c of the image buttons for notes
        #ImageButton(mode, name, cx, cy, image)
        mode.sxNote = NoteImageButton(mode, "Sx", 100, 450, mode.allNoteImagesDict["sx"], 0.25)
        mode.eiNote = NoteImageButton(mode, "Ei", 200, 450, mode.allNoteImagesDict["ei"], 0.5)
        mode.qtrNote = NoteImageButton(mode, "Qtr", 300, 450, mode.allNoteImagesDict["qt"], 1)
        mode.hfNote = NoteImageButton(mode, "Hf", 400, 450, mode.allNoteImagesDict["hf"], 2)
        mode.whNote = NoteImageButton(mode, "Wh", 500, 450, mode.allNoteImagesDict["wh"], 4)

        mode.allButtons = [mode.toHome, mode.save, mode.create, mode.finished, mode.sxNote, mode.eiNote,
                            mode.qtrNote, mode.hfNote, mode.whNote]
        mode.noteButtons = [mode.sxNote, mode.eiNote, mode.qtrNote, mode.hfNote, mode.whNote]
        mode.image = None

        mode.sampleSetup()
        mode.totalPieces = 3

        mode.resetInputs()

    def sampleSetup(mode):
        #setup so you can look through all the different pieces in image processing
        mode.pieceNum = 1
        mode.filename = (mode.sampleDict[mode.pieceNum])[0]
        mode.convertedFile = (mode.sampleDict[mode.pieceNum])[1]
    def resetInputs(mode):
        mode.inputBeat = 1
        mode.firstInput = True
        mode.inputNoteLst = []
        mode.currMsr = 1
    #MAKE A DICTIONARY OF DIFF SAMPLES
    def allSamplePieces(mode):
        #Note: cannot make hCM2 & 4 eql to the 1st in the list for the melody;
        #had to copy and paste to make new instances of the class
        hCBM1 = Measure(mode, [SampleNote(mode, 1, 1, "B4"), SampleNote(mode, 2, 1, "A4"), SampleNote(mode, 3, 2, "G4")])
        hCBM2 = Measure(mode, [SampleNote(mode, 1, 1, "B4"), SampleNote(mode, 2, 1, "A4"), SampleNote(mode, 3, 2, "G4")])
        hCBM3 = Measure(mode, [SampleNote(mode, 1, 0.5, "G4"), SampleNote(mode, 1.5, 0.5, "G4"), SampleNote(mode, 2, 0.5, "G4"), 
                SampleNote(mode, 2.5, 0.5, "G4"), SampleNote(mode, 3, 0.5, "A4"), SampleNote(mode, 3.5, 0.5, "A4"), 
                SampleNote(mode, 4, 0.5, "A4"), SampleNote(mode, 4.5, 0.5, "A4")])
        hCBM4 = Measure(mode, [SampleNote(mode, 1, 1, "B4"), SampleNote(mode, 2, 1, "A4"), SampleNote(mode, 3, 2, "G4")])
        
        mode.hotCrossBuns = "Hot Cross Buns"
        mode.hotCrossBunsConverted = [hCBM1, hCBM2, hCBM3, hCBM4]
        
        mode.allNotes = "All Notes"
        mode.allNotesLst = []
        for i in range (5):
            mode.allNotesLst.append(Measure(mode, [SampleNote(mode, 1, 2, "D4"), SampleNote(mode, 3, 0.5, "C5"), 
                                SampleNote(mode, 3.5, 0.5, "D5"), SampleNote(mode, 4, 0.25, "A4"),
                                SampleNote(mode, 4.25, 0.25, "B4"), SampleNote(mode, 4.5, 0.25, "C4"),
                                SampleNote(mode, 4.75, 0.25, "D4")]))
            mode.allNotesLst.append(Measure(mode, [SampleNote(mode, 1, 4, "C5")]))
        mode.allNotesConverted = mode.allNotesLst

        mode.repMelody = "Repetitive Melody"
        mode.repMelodyLst = []
        for i in range (10):
            mode.repMelodyLst.append(Measure(mode, [SampleNote(mode, 1, 2, "D4"), SampleNote(mode, 3, 0.5, "C5"), 
                                SampleNote(mode, 3.5, 0.5, "D5"), SampleNote(mode, 4, 1, "A4")]))
        mode.repMelodyConverted = mode.repMelodyLst
        #use ints as keys, increment the ints to go between the different pieces!
        sampleDict = {
                        1 : [mode.hotCrossBuns, mode.hotCrossBunsConverted],
                        2 : [mode.allNotes, mode.allNotesConverted],
                        3: [mode.repMelody, mode.repMelodyConverted]
        }
        #mode.hotCrossBuns = [hi]
        return sampleDict

    def changeSample(mode):
        if(mode.pieceNum == 0): return
        mode.filename = (mode.sampleDict[mode.pieceNum])[0]
        mode.convertedFile = (mode.sampleDict[mode.pieceNum])[1]

    def mousePressed(mode, event):
        for b in mode.allButtons:
            if(b.intersects(event.x, event.y) == True):
                b.click()

    def keyPressed(mode, event):
        if(event.key == "Right"):
            mode.pieceNum += 1
            if(mode.pieceNum > len(mode.sampleDict)):
                mode.pieceNum = 1
        
        elif(event.key == "Left"):
            mode.pieceNum -= 1
            #b/c 1 is the first key in the dictionary
            if(mode.pieceNum < 1):
                mode.pieceNum = len(mode.sampleDict)
        
        mode.changeSample()
    
    def askPitch(mode):
        pitch = ""
        validName = False
        while (validName == False):
            pitch = mode.getUserInput("Put in the pitch in the format'[Note][Octave]'. Example: 'C4'  Type exit to leave")
            if(pitch == None):
                validName= False
            else:
                pitch = pitch.upper()
                if(pitch == "EXIT"):
                    validName = False
                    mode.filename = "" 
                    mode.app.setActiveMode(mode.app.startOptionsMode)
                    break
                else:
                    #statically allocated set
                    #from: http://www.cs.cmu.edu/~112/notes/notes-sets.html#creatingSets
                    allPitches = {"A", "B", "C", "D", "E", "F", "G"}
                    #input is a string
                    allOctaves = {"3", "4", "5", "6"}
                    if(len(pitch) != 2):  return False
                    if(not(pitch[0].isalpha() and pitch[1].isdigit())): return False
                    if(pitch[0] in allPitches and pitch[1] in allOctaves):
                        validName = True
                    else:
                        validName = False
        print(pitch)
        return pitch

    def timerFired(mode):
        if(mode.toHome.isClicked == True):
            mode.app.setActiveMode(mode.app.startOptionsMode)
            mode.toHome.unclick()
        if(mode.save.isClicked == True):
            #from:http://www.cs.cmu.edu/~112/notes/notes-animations-part2.html#getAndSaveSnapshot
            snapshotImage = mode.app.getSnapshot()
            mode.image = mode.app.scaleImage(snapshotImage, 0.4)
            mode.app.saveSnapshot()
            mode.save.unclick()
        if(mode.finished.isClicked == True):
            mode.totalPieces += 1
            mode.sampleDict[mode.totalPieces] = [mode.filename, mode.convertedFile]
            mode.sampleSetup()
            mode.resetInputs()
            mode.finished.unclick()
        if(mode.create.isClicked == True):
            userFilename = ""
            validName = False
            while (validName == False):
                userFilename = mode.getUserInput("Put in the name of your new score! Type exit to leave")
                if(userFilename == None):
                    validName= False
                else:
                    if(userFilename.upper() == "EXIT"):
                        validName = False
                        mode.filename = "" 
                        userFilename = ""
                        mode.app.setActiveMode(mode.app.startOptionsMode)
                        break
                    else:
                        validName = True
            if(userFilename != None):
                    mode.filename = userFilename
                    mode.convertedFile = []
                    mode.pieceNum = 0
                    mode.inputNoteLst = []
            mode.create.unclick()
        if(mode.pieceNum == 0):
            for noteButton in mode.noteButtons:
                if(noteButton.isClicked == True):
                    noteButton.unclick()
                    pitch = mode.askPitch()
                    beat = mode.inputBeat
                    dur = noteButton.val
                    #make a new measure after the first full measure
                    if(mode.inputBeat % 4 == 1 and mode.firstInput == True):
                        mode.inputNoteLst.append( SampleNote(mode, beat, dur, pitch) )
                        mode.firstInput = False
                    elif(mode.inputBeat % 4 == 1):
                        msr = Measure(mode, mode.inputNoteLst)
                        mode.convertedFile.append(msr)
                        mode.currMsr += 1
                        mode.inputNoteLst = []
                        mode.inputNoteLst.append( SampleNote(mode, beat % 4, dur, pitch) )
                    else:
                        mode.inputNoteLst.append( SampleNote(mode, beat % 4, dur, pitch) )

                    mode.inputBeat += noteButton.val
                

    def drawM1BufferImages(mode, canvas, x, y):
        canvas.create_image(x, y, image =  
                    ImageTk.PhotoImage(mode.allBufferDict["blank"]))
        canvas.create_image(x - 630, y - 20, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["treble"]))
        canvas.create_image(x - 595, y - 20, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["meter"]))

    def drawAllMBufferImages(mode, canvas, x, y):
        numBlanks = (mode.height // 150)
        
        for i in range (numBlanks - 2): 
            tX = x - 630
            tY = y - 20
            canvas.create_image(x, y, image =  
                    ImageTk.PhotoImage(mode.allBufferDict["blank"]))
            canvas.create_image(tX, tY, image = 
                    ImageTk.PhotoImage(mode.allBufferDict["treble"]))
            y += 125

    def drawMusic(mode, canvas):
        startX = 70
        msrNum = 1
        startY = 20
        numLine = 1

        for msr in mode.convertedFile:
            if(msrNum != 1 and msrNum % 4 == 1):
                startY += 125
                startX = 70
            msr.drawMeasure(canvas, startX, startY)
            barX = startX + 30

            if(numLine % 4 != 1):
                adjX = 35
                adjY = 30
                x0 = startX + adjX
                y0 = startY + adjY
                y1 = y0 + 80
                canvas.create_line(x0, y0, x0, y1)
            else: numLine += 1
            startX += 300
            msrNum += 1

    def drawBeatBox(mode, canvas):
        canvas.create_rectangle(575, 415, 675, 490, fill = "DarkOrchid3")
        canvas.create_text(625, 435, text = "Beat", font = "Verdana 12")
        canvas.create_text(625, 465, text = mode.inputBeat, font = "Verdana 12")

    def drawMsrBox(mode, canvas):
        canvas.create_rectangle(675, 415, 775, 490, fill = "OliveDrab1")
        canvas.create_text(725, 435, text = "Measure", font = "Verdana 12")
        canvas.create_text(725, 465, text = mode.currMsr, font = "Verdana 12")
    
    def drawNoteLst(mode, canvas):
        canvas.create_rectangle(65, 500, 675, 600, fill = "plum3")
        canvas.create_text(200, 520, text = "Current Measure Notes", font = "Verdana 12")
        currNoteLst = mode.inputNoteLst
        startX = 85
        startY = 560
        for note in mode.inputNoteLst:
            note.drawNote(canvas, startX, startY)
            startX += 30
        #canvas.create_text(100, 540, text = currNoteLst, font = "Verdana 12")

    def redrawAll(mode, canvas):
        #consider also assigning measure #s here
        #but on the other hand, doing it within the class ensures that it will
        #be able to be used for other things in the future
        mode.drawM1BufferImages(canvas, 680, 100)
        mode.drawAllMBufferImages(canvas, 680, 225)

        for b in mode.allButtons:
            b.drawButton(canvas)

        mode.drawBeatBox(canvas)
        mode.drawMsrBox(canvas)
        mode.drawNoteLst(canvas)

        if(mode.filename == None or mode.convertedFile == None): return
        mode.drawMusic(canvas)
        scoreTitle = mode.filename
        canvas.create_text(mode.width/2, 25, text = (scoreTitle), 
                            font = "Verdana 20 bold")
        # canvas.create_text(mode.width/2, 400, text = (mode.convertedFile))
        
class MyModalApp(ModalApp):
    import math, copy
    import random
    from PIL import Image 
    import sys
    import aubio
    from tkinter import filedialog
    from tkinter import messagebox
    #from tkinter import *
    def appStarted(app):
        app.splashScreenMode = SplashScreenMode()
        app.startOptionsMode = StartOptionsMode()
        app.viewImageMode = ViewMode()
        app.transcriptionMode = TranscriptionMode()
        app.samplesMode = UseSamplesMode()

        app.setActiveMode(app.splashScreenMode)
        app.timerDelay = 50
    
    def loadBufferImages(app):
        blankUrl = ("https://cdn3.virtualsheetmusic.com/images/first_pages"+
                    "/BIG/Virtu"
                + "alSheetMusic/blanksheetmusicFirst_BIG.gif")
        app.blank = app.loadImage(blankUrl)
        app.blankLines = app.blank.crop( (0, 200, 730, 250) )
        app.blankLine = app.scaleImage(app.blankLines, 2)

        (app.w, app.h) = app.blankLine.size
        
        trebleUrl = ("https://www.stickpng.com/assets/images/5a02cb3018e87004f"
                    + "1ca43e5.png")
        app.trebleClef = app.loadImage(trebleUrl)
        app.treble = app.scaleImage(app.trebleClef, 0.08)

        meterUrl = ("http://jonathankulp.org/images/4-4meter-original.png")
        app.meter44 = app.loadImage(meterUrl)
        app.meter = app.scaleImage(app.meter44, 0.09)

        allBufferDict = {
            "blank" : app.blankLine,
            "treble" : app.treble,
            "meter" : app.meter
        }
        return allBufferDict

    def loadNoteImages(app):
        #provides images of all the notes
        #Note: putting images into the dictionary in appStarted speeds up the runtime of the app significantly
        qtUrl = ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Qu"
            + "arter_note_with_upwards_stem.svg/360px-Quarter_note_with_upwards_stem.svg.png")
        app.qtNote = app.loadImage(qtUrl)
        app.qt = app.scaleImage(app.qtNote, 0.1)

        eiUrl = ("https://theonlinemetronome.com/photos/eighth-note-single.png")
        app.eiNote = app.loadImage(eiUrl)
        app.ei = app.scaleImage(app.eiNote, 0.04)

        sxUrl = ("https://theonlinemetronome.com/photos/sixteent-note-single.png")
        app.sxNote = app.loadImage(sxUrl)
        app.sx = app.scaleImage(app.sxNote, 0.1)

        hfUrl = ("https://theonlinemetronome.com/photos/half-note.png")
        app.hfNote = app.loadImage(hfUrl)
        app.hf = app.scaleImage(app.hfNote, 0.1)

        whUrl = ("https://theonlinemetronome.com/photos/whole-note.png")
        app.whNote = app.loadImage(whUrl)
        app.wh = app.scaleImage(app.whNote, 0.4)

        #the keys for the dictionary are self.getNoteType
        allNotesDict = {
                "qt": app.qt,
                "hf": app.hf,
                "wh": app.wh,
                "ei": app.ei,
                "sx": app.sx
        }
        return allNotesDict

app = MyModalApp(width=1366, height=705)