from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from vi.resources import resourcePath
from vi.ui.SoundSetup import Ui_Dialog
from vi.sound.soundmanager import SoundManager

class SoundSettingDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        # if not self.platformSupportsSpeech():
        #     self.useSpokenNotifications = False
        # if not self.soundAvailable:
        #     return
        QDialog.__init__(self,parent=parent)
        self.setupUi(self)
        self.volumeSlider.setValue(SoundManager().soundVolume)
        self.volumeSlider.valueChanged.connect(self.setSoundVolume)
        self.testSoundButton.clicked.connect(self.playAlarmSound)
        self.stopSoundButton.clicked.connect(self.stopAlarmSound)
        self.closeButton.clicked.connect(self.closeSound)
        self.stopSoundButton.setEnabled(False)

    def closeSound(self):
        if not self.isHidden():
            self.stopAlarmSound()
            self.soundDialog.accept()


    def setSoundVolume(self, newValue):
        """ Accepts and stores a number between 0 and 100.
        """
        self.soundVolume = max(0, min(100, newValue))
        SoundManager().setSoundVolume(self.soundVolume)

    def playAlarmSound(self):
        if SoundManager().soundAvailable:
            self.testSoundButton.setEnabled(False)
            self.stopSoundButton.setEnabled(True)
            SoundManager().playSound()

    def stopAlarmSound(self):
        if SoundManager().soundAvailable:
            self.testSoundButton.setEnabled(True)
            self.stopSoundButton.setEnabled(False)
            SoundManager().soundThread.queue.put(("", "", ""))
            SoundManager().playSound()

    def quit(self):
        self.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    sd = SoundSettingDialog()
    sd.show()
