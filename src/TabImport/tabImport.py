'''
Created on Aug 3, 2013

@author: mike_000
'''

from Data.NotePosition import NotePosition
from Data.Score import ScoreFactory
from Data.Drum import Drum, HeadData
from Data.DrumKit import DrumKit
from Data import MeasureCount

import itertools

class TabImportError(RuntimeError):
    pass

class DrumStaffGuess(object):
    def __init__(self):
        self._lines = []
        self._barPositions = []

    def num_lines(self):
        return len(self._lines)

    def __iter__(self):
        return iter(self._lines)

    def get_line_by_prefix(self):
        pass

    def add_line(self, line):
        if self._lines:
            thisLineIndexes = [index for index, char in enumerate(line.line)
                               if char == line.BARLINE]
            if thisLineIndexes != self._barPositions:
                return False
        else:
            self._barPositions = [index for index, char in enumerate(line.line)
                                  if char == line.BARLINE]
        self._lines.append(line)
        return True

    def iterMeasures(self):
        barIterator = itertools.izip(self._barPositions[:-1],
                                     self._barPositions[1:])
        for start, end in barIterator:
            yield [DrumLineGuess(line.prefix, line.line[start + 1:end])
                   for line in self]

class DrumLineGuess(object):
    BARLINE = "|"
    EMPTY_NOTE = "-"
    FORBIDDEN = set(" ")
    def __init__(self, prefix, line):
        self.prefix = prefix
        self.line = line
        
    @classmethod
    def recognize(cls, line):
        barCount = line.count(cls.BARLINE)
        if barCount < 2:
            return None
        start = line.index(cls.BARLINE)
        startEmpty = line.find(cls.EMPTY_NOTE)
        if startEmpty != -1 and startEmpty < start:
            start = startEmpty
        end = line.rindex(cls.BARLINE)
        endEmpty = line.rfind(cls.BARLINE)
        if endEmpty > end:
            end = endEmpty
        lineData = line[start:end + 1]
        lineData = lineData.replace(" ", "")
        for char in lineData:
            if char in cls.FORBIDDEN:
                return None
        prefix = line[:start].strip()
        if not prefix:
            return None
        prefix = prefix.rstrip(":").strip()
        return cls(prefix, lineData)

class DrumKitGuess(object):
    def __init__(self, staffGuesses):
        self._heads = {}
        self._order = []
        self._abbr = {}
        self._readGuesses(staffGuesses)
        self._fixOrder(staffGuesses)
        self._checkDrums()

    def _readGuesses(self, staffGuesses):
        for staff in staffGuesses:
            for line in staff:
                if line.prefix not in self._heads:
                    self._addDrum(line.prefix)
                for char in line.line:
                    if char not in (line.BARLINE, line.EMPTY_NOTE):
                        self._addNoteHead(line.prefix, char)

    def _fixOrder(self, staffGuesses):
        order = self._order
        for staff in staffGuesses:
            for first, line1 in enumerate(staff):
                for second, line2 in enumerate(staff):
                    if second <= first:
                        continue
                    left = order.index(line1.prefix)
                    right = order.index(line2.prefix)
                    if left > right:
                        order[left], order[right] = order[right], order[left]
        self._order = list(reversed(order))

    def _checkDrums(self):
        abbrs = set()
        for prefix in self:
            if not self._heads[prefix]:
                self._addNoteHead(prefix, "x")
            if len(prefix) <= 2:
                abbr = prefix
            else:
                if prefix[-1] in '0123456789':
                    abbr = prefix[0] + prefix[-1]
                else:
                    abbr = prefix[:2]
            if abbr not in abbrs:
                self._abbr[prefix] = abbr
                abbrs.add(abbr)
            else:
                count = 0
                looped = False
                while abbr in abbrs:
                    abbr = prefix[:1]
                    if count == 9:
                        if abbr == 'z' or ord(abbr[0]) == 0x7e:
                            abbr = 'A'
                            if looped:
                                raise TabImportError("Could not assign abbreviation for drum %s" % abbr)
                            looped = True
                        elif abbr == 'Z':
                            abbr = 'a'
                        else:
                            abbr = chr(ord(prefix) + 1)
                    count += 1
                    abbr += str(count)
                self._abbr[prefix] = abbr
                abbrs.add(abbr)

    def abbr(self, prefix):
        return self._abbr[prefix]



    def __iter__(self):
        return iter(self._order)

    def note_heads(self, prefix):
        return list(self._heads[prefix])

    def _addDrum(self, prefix):
        if prefix in self._order:
            return
        self._order.append(prefix)
        self._heads[prefix] = []

    def _addNoteHead(self, prefix, noteHead):
        if noteHead not in self._heads[prefix]:
            self._heads[prefix].append(noteHead)

    def drumIndex(self, prefix):
        return self._order.index(prefix)

def guessStaffs(lines):
    staffs = []
    currentStaff = None
    for line in itertools.imap(str.strip, lines):
        line = DrumLineGuess.recognize(line)
        if line is None:
            if currentStaff is not None:
                staffs.append(currentStaff)
                currentStaff = None
        else:
            lastStaff = currentStaff
            if currentStaff is None:
                currentStaff = DrumStaffGuess()
            if not currentStaff.add_line(line):
                currentStaff = lastStaff
    if currentStaff is not None:
        staffs.append(currentStaff)
    return staffs


def guessScore(staffs, drums):
    kit = DrumKit()
    for prefix in drums:
        heads = drums.note_heads(prefix)
        defaultHead = heads[0]
        drum = Drum(prefix, drums.abbr(prefix), defaultHead, False)
        headData = HeadData()
        drum.addNoteHead(defaultHead, headData)
        for head in heads[1:]:
            drum.addNoteHead(head)
        kit.addDrum(drum)
    score = ScoreFactory.makeEmptyScore(0, None, kit)
    for staffGuess in staffs:
        for measureLines in staffGuess.iterMeasures():
            if not measureLines:
                continue
            width = len(measureLines[0].line)
            measure = score.insertMeasureByIndex(width)
            for line in measureLines:
                drumIndex = drums.drumIndex(line.prefix)
                for noteTime, head in enumerate(line.line):
                    if head in (line.BARLINE, line.EMPTY_NOTE):
                        continue
                    measure.addNote(NotePosition(noteTime=noteTime, drumIndex=drumIndex),
                                    head)
    return score

def guessCounts(score):
    for measure in score.iterMeasures():
        width = len(measure)
        if width == 4:
            beatLength = 1
        elif width == 8:
            beatLength = 2
        elif width == 16:
            beatLength = 4
        elif width == 6:
            beatLength = 3
        elif width == 12:
            beatLength = 3
        elif width == 24:
            beatLength = 6
        elif width % 4 == 0:
            beatLength = 4
        elif width % 2 == 0:
            beatLength = 2
        else:
            beatLength = 1
        counter = MeasureCount.counterMaker(beatLength, width)
        measure.counter = counter

def importTab(handle):
    lines = handle.readlines()
    staffGuesses = guessStaffs(lines)
    drums = DrumKitGuess(staffGuesses)
    score = guessScore(staffGuesses, drums)
    guessCounts(score)
    if score.numMeasures() == 0:
        raise TabImportError("No measures found!")
    return score

def main():
    import sys
    if len(sys.argv) == 2:
        infile = sys.argv[1]
    else:
        print "Usage: tabimport infilename"
        return
    outfile = unicode(infile)
    if outfile.endswith(u".txt"):
        outfile = outfile[:-4]
    outfile += ".brp"
    with open(infile) as handle:
        score = importTab(handle)
    score.write(sys.stdout)
    score.write(open(outfile, 'wb'))

if __name__ == '__main__':
    main()