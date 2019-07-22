###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import os
import subprocess
import sys
import re
import requests
import time
import six

from collections import namedtuple
from PyQt5.QtCore import QThread
from .resources import resourcePath
from six.moves import queue

import logging
from vi.singleton import Singleton

global gPygletAvailable

try:
    import pyglet
    from pyglet import media

    gPygletAvailable = True
except ImportError:
    gPygletAvailable = False


class SoundManager(six.with_metaclass(Singleton)):
    SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
              "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
              "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"}

    soundVolume = 25  # Must be an integer between 0 and 100
    soundActive = False
    soundAvailable = False
    useDarwinSound = False
    useSpokenNotifications = True
    _soundThread = None

    def __init__(self):
        self._soundThread = self.SoundThread()
        self.soundAvailable = self.platformSupportsAudio()
        if not self.platformSupportsSpeech():
            self.useSpokenNotifications = False
        if self.soundAvailable:
            self._soundThread.start()

    def platformSupportsAudio(self):
        return self.platformSupportsSpeech() or gPygletAvailable

    def platformSupportsSpeech(self):
        if self._soundThread.isDarwin:
            return True
        return False

    def setUseSpokenNotifications(self, newValue):
        if newValue is not None:
            self.useSpokenNotifications = newValue

    def setSoundVolume(self, newValue):
        """ Accepts and stores a number between 0 and 100.
        """
        self.soundVolume = max(0, min(100, newValue))
        self._soundThread.setVolume(self.soundVolume)

    def playSound(self, name="alarm", message="", abbreviatedMessage=""):
        """ Schedules the work, which is picked up by SoundThread.run()
        """
        if self.soundAvailable and self.soundActive:
            if self.useSpokenNotifications:
                audioFile = None
            else:
                audioFile = resourcePath("vi/ui/res/{0}".format(self.SOUNDS[name]))
            self._soundThread.queue.put((audioFile, message, abbreviatedMessage))

    def quit(self):
        if self.soundAvailable:
            self._soundThread.quit()

    #
    #  Inner class handle audio playback without blocking the UI
    #

    class SoundThread(QThread):
        queue = None
        useGoogleTTS = False
        useVoiceRss = False
        VOICE_RSS_API_KEY = '896a7f61ec5e478cba856a78babab79c'
        GOOGLE_TTS_API_KEY = ''
        isDarwin = sys.platform.startswith("darwin")
        volume = 25


        def __init__(self):
            QThread.__init__(self)
            self.queue = queue.Queue()
            if gPygletAvailable:
                self.player = media.Player()
            else:
                self.player = None
            self.active = True


        def setVolume(self, volume):
            self.volume = volume


        def run(self):
            while True:
                audioFile, message, abbreviatedMessage = self.queue.get()
                if not self.active:
                    return
                if SoundManager().useSpokenNotifications and (message != "" or abbreviatedMessage != ""):
                    if abbreviatedMessage != "":
                        message = abbreviatedMessage
                    if not self.speak(message):
                        self.playAudioFile(audioFile, False)
                        logging.error("SoundThread: sorry, speech not yet implemented on this platform")
                elif audioFile is not None:
                    self.playAudioFile(audioFile, False)

        def quit(self):
            self.active = False
            self.queue.put((None, None, None))
            if self.player:
                self.player.pause()
                self.player.delete()
            QThread.quit(self)


        def speak(self, message):
            if self.useGoogleTTS:
                self.audioExtractToMp3(inputText=message)  # experimental
            elif self.useVoiceRss:
                self.playTTS(message)  # experimental
            elif self.isDarwin:
                self.darwinSpeak(message)
            else:
                return False
            return True


        def handleIdleTasks(self):
            self.speakRandomChuckNorrisJoke()


        # Audio subsytem access

        def playAudioFile(self, filename, stream=False):
            try:
                volume = float(self.volume) / 100.0
                if self.player:
                    src = media.load(filename, streaming=stream)
                    self.player.queue(src)
                    self.player.volume = volume
                    self.player.play()
                elif self.isDarwin:
                    subprocess.call(["afplay -v {0} {1}".format(volume, filename)], shell=True)
            except Exception as e:
                logging.error("SoundThread.playAudioFile exception: %s", e)

        def darwinSpeak(self, message):
            try:
                os.system("say [[volm {0}]] '{1}'".format(float(self.volume) / 100.0, message))
            except Exception as e:
                logging.error("SoundThread.darwinSpeak exception: %s", e)

        #
        #  Experimental text-to-speech stuff below
        #

        # VoiceRss

        def playTTS(self, inputText=''):
            try:
                mp3url = 'http://api.voicerss.org/?c=WAV&key={self.VOICE_RSS_API_KEY}&src={inputText}&hl=en-us'.format(
                    **locals())
                self.playAudioFile(requests.get(mp3url, stream=True).raw)
                time.sleep(.5)
            except requests.exceptions.RequestException as e:
                logging.error('playTTS error: %s', str(e))

        # google_tts

        def audioExtractToMp3(self, inputText='', args=None):
            # This accepts :
            #   a dict,
            #   an audio_args named tuple
            #   or arg parse object
            audioArgs = namedtuple('audio_args', ['language', 'output'])
            if args is None:
                args = audioArgs(language='en', output=open('output.mp3', 'w'))
            if type(args) is dict:
                args = audioArgs(language=args.get('language', 'en'), output=open(args.get('output', 'output.mp3'), 'w'))
            # Process inputText into chunks
            # Google TTS only accepts up to (and including) 100 characters long texts.
            # Split the text in segments of maximum 100 characters long.
            combinedText = self.splitText(inputText)

            # Download chunks and write them to the output file
            for idx, val in enumerate(combinedText):
                mp3url = "http://translate.google.com/translate_tts?tl=%s&q=%s&total=%s&idx=%s&ie=UTF-8&client=t&key=%s" % (
                args.language, requests.utils.quote(val), len(combinedText), idx, self.GOOGLE_TTS_API_KEY)
                headers = {"Host": "translate.google.com", "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1)"}
                sys.stdout.write('.')
                sys.stdout.flush()
                if len(val) > 0:
                    try:
                        args.timeout.write(requests.get(mp3url, headers=headers).content)
                        time.sleep(.5)
                    except requests.exceptions.RequestException as e:
                        logging.error('audioExtractToMp3 error: %s', e)
            args.output.close()
            return args.output.name

        def splitText(self, inputText, maxLength=100):
            """
            Try to split between sentences to avoid interruptions mid-sentence.
            Failing that, split between words.
            See splitText_rec
            """

            def splitTextRecursive(inputText, regexps, maxLength=maxLength):
                """
                Split a string into substrings which are at most maxLength.
                Tries to make each substring as big as possible without exceeding
                maxLength.
                Will use the first regexp in regexps to split the input into
                substrings.
                If it it impossible to make all the segments less or equal than
                maxLength with a regexp then the next regexp in regexps will be used
                to split those into subsegments.
                If there are still substrings who are too big after all regexps have
                been used then the substrings, those will be split at maxLength.

                Args:
                    inputText: The text to split.
                    regexps: A list of regexps.
                        If you want the separator to be included in the substrings you
                        can add parenthesis around the regular expression to create a
                        group. Eg.: '[ab]' -> '([ab])'

                Returns:
                    a list of strings of maximum maxLength length.
                """
                if (len(inputText) <= maxLength):
                    return [inputText]

                # Mistakenly passed a string instead of a list
                if isinstance(regexps, basestring):
                    regexps = [regexps]
                regexp = regexps.pop(0) if regexps else '(.{%d})' % maxLength

                textList = re.split(regexp, inputText)
                combinedText = []
                # First segment could be >max_length
                combinedText.extend(splitTextRecursive(textList.pop(0), regexps, maxLength))
                for val in textList:
                    current = combinedText.pop()
                    concat = current + val
                    if (len(concat) <= maxLength):
                        combinedText.append(concat)
                    else:
                        combinedText.append(current)
                        # val could be > maxLength
                        combinedText.extend(splitTextRecursive(val, regexps, maxLength))
                return combinedText

            return splitTextRecursive(inputText.replace('\n', ''), ['([\,|\.|;]+)', '( )'])
