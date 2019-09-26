import six
from vi.singleton import Singleton
global gPygletAvailable

try:
    import pyglet
    from pyglet import media

    gPygletAvailable = True
except ImportError:
    gPygletAvailable = False


from .SoundSetting import SoundSetting

class SoundThread(six.with_metaclass(Singleton), SoundSetting):
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

    def resourcePath(relativePath):
        import sys, os
        """ Get absolute path to resource, works for dev and for PyInstaller
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            basePath = sys._MEIPASS
        else:
            basePath = os.path.abspath(".")
        returnpath = os.path.join(basePath, relativePath)
        return returnpath

    def playSound(self, name="alarm", message="", abbreviatedMessage=""):
        """ Schedules the work, which is picked up by SoundThread.run()
        """
        if self.soundAvailable and self.soundActive:
            if self.useSpokenNotifications:
                audioFile = None
            else:
                snd = self.SOUNDS[name]
                audioFile = self.resourcePath("vi/ui/res/{0}".format(snd))
            self._soundThread.queue.put((audioFile, message, abbreviatedMessage))
            # self._soundThread.queue.put(("", "", ""))

