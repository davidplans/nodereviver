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

    def __init__(self):
        self.sounds = []
        self._initialized = False
        self.enabled = True

    def init(self, config):
        if self._initialized:
            return
        self._initialized = True
        self._config = config
        if self._config.sound:
            pygame.mixer.pre_init(44100, -16, 2, 256)

    def loadSounds(self):
        if self._config.sound:
            #pygame.mixer.init()
            for fileName in self.FILES:
                self.sounds.append(pygame.mixer.Sound(self._config.dataPath + fileName))

    def startEngine(self):
        # this is basically a dummy since we are not actually going to read from the mic
        inbuf = array.array('h', range(BLOCKSIZE))
        #pygame.mixer.init(frequency=SAMPLERATE)
        m = PdManager(1, 2, SAMPLERATE, 1)
        libpd_add_to_search_path('engine/')
        patch = libpd_open_patch('engine/futureuser_EVA.pd', '.')
        print "$0: ", patch
        # the pygame channel that we will use to queue up buffers coming from pd
        ch = pygame.mixer.Channel(0)
        # python writeable sound buffers
        sounds = [pygame.mixer.Sound(numpy.zeros((BUFFERSIZE, 2), numpy.int16)) for s in range(2)]
        samples = [pygame.sndarray.samples(s) for s in sounds]
        # we go into an infinite loop selecting alternate buffers and queueing them up
        # to be played each time we run short of a buffer
        selector = 0
        while(1):
            # we have run out of things to play, so queue up another buffer of data from Pd
            if not ch.get_queue():
                # make sure we fill the whole buffer
                for x in range(BUFFERSIZE):
                    # let's grab a new block from Pd each time we're out of BLOCKSIZE data
                    if x % BLOCKSIZE == 0:
                        outbuf = m.process(inbuf)
                    # de-interlace the data coming from libpd
                    samples[selector][x][0] = outbuf[(x % BLOCKSIZE) * 2]
                    samples[selector][x][1] = outbuf[(x % BLOCKSIZE) * 2 + 1]
                # queue up the buffer we just filled to be played by pygame
                ch.queue(sounds[selector])
                # next time we'll do the other buffer
                selector = int(not selector)

        libpd_release()

    def release(self):
        if self._initialized and self._config.sound:
            pygame.mixer.quit()

    def play(self, soundIndex):
        if not self.enabled or not self._initialized or not self._config.sound:
            return
        self.sounds[soundIndex].play()

    def enable(self, enabled = True):
        self.enabled = enabled


soundManager = _SoundManager()
