from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from vi.resources import resourcePath
from .SoundSetting import SoundSetting

class SoundSetting(QDialog):

    def __init__(self, parent):
        if not self.platformSupportsSpeech():
            self.useSpokenNotifications = False
        if not self.soundAvailable:
            return
        self.soundDialog = QDialog(parent)
        loadUi(resourcePath("vi/ui/SoundSetup.ui"), self.soundDialog)
        self.soundDialog.volumeSlider.setValue(self.soundVolume)
        self.soundDialog.volumeSlider.valueChanged.connect(self.setSoundVolume)
        self.soundDialog.testSoundButton.clicked.connect(self.playAlarmSound)
        self.soundDialog.stopSoundButton.clicked.connect(self.stopAlarmSound)
        self.soundDialog.closeButton.clicked.connect(self.closeSound)
        self.soundDialog.stopSoundButton.setEnabled(False)
        self.soundDialog.show()

    def closeSound(self):
        if not self.soundDialog.isHidden():
            self.stopAlarmSound()
            self.soundDialog.accept()


    def setSoundVolume(self, newValue):
        """ Accepts and stores a number between 0 and 100.
        """
        self.soundVolume = max(0, min(100, newValue))

    def playAlarmSound(self):
        self.soundDialog.testSoundButton.setEnabled(False)
        self.soundDialog.stopSoundButton.setEnabled(True)
        self.playSound()

    def stopAlarmSound(self):
        self.soundDialog.testSoundButton.setEnabled(True)
        self.soundDialog.stopSoundButton.setEnabled(False)
        self._soundThread.queue.put(("", "", ""))
        # self.playSound()

    def quit(self):
        if self.soundAvailable:
            self._soundThread.quit()

