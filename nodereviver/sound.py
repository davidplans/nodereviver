'''
    This file is part of nodereviver

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    @author: Vincent Petry <PVince81@yahoo.fr>
'''

import pygame
from pylibpd import *
import numpy

BUFFERSIZE = 4096
SAMPLERATE = 44100
BLOCKSIZE = 64

class _SoundManager:
    MOVE = 0
    DEAD = 1
    DRAW = 2

    FILES = [
        "move.wav",
        "dead.wav",
        "draw.wav"
    ]

    # TODO davide I think we need a level event that we can use
    # to change patch and understand level finish and new level

    def __init__(self):
        self.sounds = []
        self._initialized = False
        self.enabled = True
        self._pdManager = None
        self._ch = None
        self._inbuf = None
        self._sounds = None
        self._samples = None
        self._patch = None
        self._BUFFERSIZE = 1024
        self._BLOCKSIZE = 64
        self._SAMPLERATE = 44100
        self._selector = 0

    def init(self, config):
        if self._initialized:
            return
        self._initialized = True
        self._config = config
        pygame.mixer.pre_init(44100, -16, 2, 256)
        pygame.init()
        self._pdManager = PdManager(1,2,self._SAMPLERATE, 1)
        libpd_add_to_search_path('engine/')
        self._patch = libpd_open_patch('engine/futureuser_EVA.pd', '.')
        print "$0: ", self._patch

        # this is basically a dummy since we are not actually going to read from the mic
        self._inbuf = array.array('h', range(self._BLOCKSIZE))

        # the pygame channel that we will use to queue up buffers coming from pd
        self._ch = pygame.mixer.Channel(0)
        # python writeable sound buffers
        self._sounds = [pygame.mixer.Sound(numpy.zeros((self._BUFFERSIZE, 2), numpy.int16)) for s in range(2)]
        self._samples = [pygame.sndarray.samples(s) for s in self._sounds]

        
    #def loadSounds(self):
    #    if self._config.sound:
    #        #pygame.mixer.init()
    #        for fileName in self.FILES:
    #            self.sounds.append(pygame.mixer.Sound(self._config.dataPath + fileName))


    def release(self):
        libpd_release()
        if self._initialized and self._config.sound:
            pygame.mixer.quit()

    def play(self, soundIndex):
        libpd_float('sound', soundIndex)
        #if not self.enabled or not self._initialized or not self._config.sound:
        #    return
        #self.sounds[soundIndex].play()

    #def enable(self, enabled = True):
    #    self.enabled = enabled
        
    def processAudio(self):
        if not self._ch.get_queue():
            # make sure we fill the whole buffer
            for x in range(self._BUFFERSIZE):
                # let's grab a new block from Pd each time we're out of BLOCKSIZE data
                if x % self._BLOCKSIZE == 0:
                    outbuf = self._pdManager.process(self._inbuf)
                # de-interlace the data coming from libpd
                self._samples[self._selector][x][0] = outbuf[(x % self._BLOCKSIZE) * 2]
                self._samples[self._selector][x][1] = outbuf[(x % self._BLOCKSIZE) * 2 + 1]
            # queue up the buffer we just filled to be played by pygame
            self._ch.queue(self._sounds[self._selector])
            # next time we'll do the other buffer
            self._selector = int(not self._selector)

    def sendFrustration(self, frustration):
        libpd_float('frustration', frustration)

    def sendPlanning(self, planning):
        libpd_float('planning', planning)

    def sendFear(self, fear):
        libpd_float('fear', fear)

    def sendDeath(self):
        libpd_bang('death')

    def sendVictory(self):
        libpd_bang('victory')

    def sendMove(self):
        libpd_bang('move')

    def sendNodeLuminance(self, nodeLum):
        libpd_message('move', nodeLum)


soundManager = _SoundManager()
