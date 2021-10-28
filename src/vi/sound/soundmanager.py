###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#
#
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

# TODO: consider "pyaudiotools"

import logging
import os
import re
import subprocess
import sys
import time
import wave
from collections import namedtuple
from threading import Thread
try:
    import pyglet
    gPygletAvailable = True
except ImportError:
    gPygletAvailable = False
import requests
import six
from six.moves import queue

from vi.resources import get_sound_resource_path

# import pyglet.clock
# import pyglet.resource
from vi.settings.settings import GeneralSettings
from vi.singleton import Singleton

LOGGER = logging.getLogger(__name__)


class SoundManager(six.with_metaclass(Singleton)):
    SOUNDS = {
        "alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
        "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
        "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav",
        "stop": "Empty.wav",
    }

    soundVolume = 25  # Must be an integer between 0 and 100
    _soundActive = False
    soundAvailable = False
    useDarwinSound = False
    useSpokenNotifications = True
    _soundThread = None

    def __init__(self):
        self.LOGGER = logging.getLogger(__name__)
        self.soundThread = self.SoundThread()
        self.soundAvailable = self.platformSupportsAudio()
        if not self.platformSupportsSpeech():
            self.useSpokenNotifications = False
        if self.soundAvailable and self.soundThread:
            try:
                self.soundThread.start()
            except UserWarning as e:
                self.LOGGER.warning(e)

    def platformSupportsAudio(self) -> bool:
        return self.platformSupportsSpeech() or gPygletAvailable

    def platformSupportsSpeech(self) -> bool:
        return self.soundThread.isDarwin

    def setUseSpokenNotifications(self, value: bool):
        if value is not None:
            self.useSpokenNotifications = value

    @property
    def enable_sound(self) -> bool:
        return GeneralSettings().sound_active

    @enable_sound.setter
    def enable_sound(self, value: bool):
        GeneralSettings().sound_active = value

    def playSoundFile(self, path, volume=25, message="", abbreviated_message=""):
        self.LOGGER.debug(f"put on Queue: '{path}' Volume:{volume}")
        if self.soundAvailable and self.enable_sound:
            if self.useSpokenNotifications:
                path = None
            if path and not os.path.exists(path):
                import glob

                hits = glob.glob(
                    os.path.join(get_sound_resource_path(), os.path.basename(path)), recursive=True
                )
                if hits:
                    path = hits[0]
                else:
                    path = None
            if self.soundThread:
                self.soundThread.queue.put((path, volume, message, abbreviated_message))

    def playSound(self, name="alarm", volume=25, message="", abbreviated_message=""):
        """ Schedules the work, which is picked up by SoundThread.run()
        """
        self.LOGGER.debug(f"playSound: {name}")
        if self.soundAvailable and self.enable_sound:
            if self.useSpokenNotifications:
                audio_file = None
            else:
                audio_file = get_sound_resource_path("{0}".format(self.SOUNDS[name]))
            if self.soundThread:
                self.soundThread.queue.put(
                    (audio_file, volume, message, abbreviated_message)
                )

    def quit(self):
        if self.soundAvailable:
            if self.soundThread:
                self.soundThread.quit()

    #
    #  Inner class handle audio playback without blocking the UI
    #
    class SoundThread(Thread):
        queue = None
        useGoogleTTS = False
        useVoiceRss = False
        VOICE_RSS_API_KEY = "896a7f61ec5e478cba856a78babab79c"
        GOOGLE_TTS_API_KEY = ""
        isDarwin = sys.platform.startswith("darwin")
        volume = 25

        def __init__(self):
            super(self.__class__, self).__init__(name="SoundThread")
            self.LOGGER = logging.getLogger(__name__)
            self.LOGGER.debug("initialize SoundThread")
            try:
                self.player = pyglet.media.Player()
                self.player.loop = False
            except UserWarning as e:
                self.LOGGER.warning(e)
            self.queue = queue.Queue()
            self.active = True
            self.currently_playing = False

        def setVolume(self, volume):
            self.volume = volume

        def run(self):
            while True:
                audio_file, volume, message, abbreviated_message = self.queue.get()
                self.LOGGER.debug(
                    "got from Queue: '%s', Active: %d", audio_file, self.active
                )
                if not self.active:
                    return
                if SoundManager().useSpokenNotifications and (
                    message != "" or abbreviated_message != ""
                ):
                    if abbreviated_message != "":
                        message = abbreviated_message
                    if not self.speak(message):
                        self.playAudioFile(audio_file, volume, False)
                        LOGGER.error(
                            "SoundThread: sorry, speech not yet implemented on this platform"
                        )
                # elif audioFile is not None:
                else:
                    self.playAudioFile(audio_file, volume, False)

        def quit(self):
            self.active = False
            self.queue.put((None, None, None, None))
            if self.player:
                self.player.pause()
                self.player.delete()

        def stop(self):
            if self.player:
                self.player.next_source()

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

        # Audio subsytem access
        def playAudioFile(self, filename, set_volume, stream=False):
            try:
                if not set_volume:
                    set_volume = 25
                volume = float(set_volume) / 100.0
                if self.player:
                    with wave.open(filename, "r") as f:
                        duration = (
                            f.getnframes()
                            / float(f.getnchannels() * f.getframerate())
                            / 2
                        )
                    self.LOGGER.debug(
                        "'%s' Vol:%f Duration:%f", filename, volume, duration
                    )
                    src = pyglet.media.load(filename, streaming=stream)
                    self.player.queue(src)
                    self.player.volume = volume
                    self.player.play()
                    time.sleep(duration)
                    self.player.next_source()
                elif self.isDarwin:
                    subprocess.call(
                        ["afplay -v {0} {1}".format(volume, filename)], shell=True
                    )
            except Exception as e:
                # wave.open throws weird errors, hence the logging like thi
                self.LOGGER.error(
                    "SoundThread.playAudioFile exception on %s: %r", filename, e
                )
                # self.player = media.Player()
                # self.player.loop = False

        #
        #  Experimental text-to-speech stuff below
        #
        def darwinSpeak(self, message):
            try:
                os.system(
                    "say [[volm {0}]] '{1}'".format(float(self.volume) / 100.0, message)
                )
            except Exception as e:
                self.LOGGER.error("SoundThread.darwinSpeak exception: %s" % message, e)

        # VoiceRss

        def playTTS(self, input_text=""):
            mp3url = f"http://api.voicerss.org/?c=WAV&key={self.VOICE_RSS_API_KEY}&src={input_text}&hl=en-us"
            try:
                self.playAudioFile(requests.get(mp3url, stream=True).raw)
                time.sleep(0.5)
            except requests.exceptions.RequestException as e:
                self.LOGGER.error("playTTS error: %s: %r", mp3url, e)

        # google_tts

        def audioExtractToMp3(self, inputText=None, args=None):
            # This accepts :
            #   a dict,
            #   an audio_args named tuple
            #   or arg parse object
            audioArgs = namedtuple("audio_args", ["language", "output"])
            if args is None:
                args = audioArgs(language="en", output=open("output.mp3", "w"))
            if type(args) is dict:
                args = audioArgs(
                    language=args.get("language", "en"),
                    output=open(args.get("output", "output.mp3"), "w"),
                )
            # Process inputText into chunks
            # Google TTS only accepts up to (and including) 100 characters long texts.
            # Split the text in segments of maximum 100 characters long.
            combined_text = self.splitText(inputText)

            # Download chunks and write them to the output file
            for idx, val in enumerate(combined_text):
                mp3url = (
                    "http://translate.google.com/translate_tts?tl=%s&q=%s&total=%s&idx=%s&ie=UTF-8&client=t&key=%s"
                    % (
                        args.language,
                        requests.utils.quote(val),
                        len(combined_text),
                        idx,
                        self.GOOGLE_TTS_API_KEY,
                    )
                )
                headers = {
                    "Host": "translate.google.com",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1)",
                }
                sys.stdout.write(".")
                sys.stdout.flush()
                if len(val) > 0:
                    try:
                        args.timeout.write(
                            requests.get(mp3url, headers=headers).content
                        )
                        time.sleep(0.5)
                    except requests.exceptions.RequestException as e:
                        self.LOGGER.error("audioExtractToMp3 error: %s" % mp3url, e)
            args.output.close()
            return args.output.name

        def splitText(self, input_text, max_length=100):
            """
            Try to split between sentences to avoid interruptions mid-sentence.
            Failing that, split between words.
            See splitText_rec
            """

            def splitTextRecursive(i_text, regexps, m_length):
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
                    i_text: The text to split.
                    regexps: A list of regexps.
                        If you want the separator to be included in the substrings you
                        can add parenthesis around the regular expression to create a
                        group. Eg.: '[ab]' -> '([ab])'
                    m_length: Maximum length
                Returns:
                    a list of strings of maximum m_length length.
                """
                if len(i_text) <= m_length:
                    return [i_text]

                # Mistakenly passed a string instead of a list
                if isinstance(regexps, str):
                    regexps = [regexps]
                regexp = regexps.pop(0) if regexps else "(.{%d})" % m_length

                textList = re.split(regexp, i_text)
                combinedText = []
                # First segment could be >max_length
                combinedText.extend(
                    splitTextRecursive(textList.pop(0), regexps, m_length)
                )
                for val in textList:
                    current = combinedText.pop()
                    concat = current + val
                    if len(concat) <= m_length:
                        combinedText.append(concat)
                    else:
                        combinedText.append(current)
                        # val could be > maxLength
                        combinedText.extend(splitTextRecursive(val, regexps, m_length))
                return combinedText

            return splitTextRecursive(
                input_text.replace("\n", ""), [r"([\,|\.|;]+)", "( )"], max_length
            )
