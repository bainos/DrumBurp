'''
Created on 12 Dec 2010

@author: Mike Thomas

'''

from Drum import Drum
from DBErrors import DuplicateDrumError, NoSuchDrumError

class DrumKit(object):
    '''
    classdocs
    '''

    DEFAULT_KIT = [("Foot pedal", "Fo", "x"),
                   ("Kick", "Bd", "o"),
                   ("Low Tom", "LT", "o"),
                   ("Snare", "Sn", "x"),
                   ("Mid Tom", "MT", "o"),
                   ("High Tom", "HT", "o"),
                   ("Ride", "Ri", "x"),
                   ("HiHat", "Hh", "x"),
                   ("Crash", "Cr", "x")]


    def __init__(self):
        self._drums = []

    def __len__(self):
        return len(self._drums)

    def __getitem__(self, index):
        return self._drums[index]

    def __iter__(self):
        return iter(self._drums)

    def loadDefaultKit(self):
        for drumData in self.DEFAULT_KIT:
            self.addDrum(Drum(*drumData))

    def addDrum(self, drum):
        if drum in self._drums:
            raise DuplicateDrumError(drum.name, drum.abbr)
        self._drums.append(drum)

    def deleteDrum(self, name = None, index = None):
        assert(not(index is None and name is None))
        assert(not(index is not None and name is not None))
        if name is not None:
            index = [i for i, dr in enumerate(self._drums)
                     if dr.name == name]
            if len(index) != 1:
                raise NoSuchDrumError(name)
            index = index[0]
        if not (0 <= index < len(self)):
            raise NoSuchDrumError(index)
        self._drums.pop(index)

