from PyQt5.QtWidgets import QDialog
from vi.ui.SoundSetup import Ui_Dialog
from vi.sound.soundmanager import SoundManager

class SoundSettingDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
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
            self.quit()

    def setSoundVolume(self, newValue):
        """ Accepts and stores a number between 0 and 100.
        """
        self.soundVolume = max(0, min(100, newValue))
        SoundManager().setSoundVolume(self.soundVolume)

    def playAlarmSound(self):
        if SoundManager().soundAvailable:
            import time
            self.testSoundButton.setEnabled(False)
            self.stopSoundButton.setEnabled(True)
            SoundManager().playSound()
            while SoundManager.player.playing:
                time.sleep(0.1)
            self.testSoundButton.setEnabled(True)
            self.stopSoundButton.setEnabled(False)


    def stopAlarmSound(self):
        if SoundManager().soundAvailable:
            self.testSoundButton.setEnabled(True)
            self.stopSoundButton.setEnabled(False)
            SoundManager().playSound("stop")

    def quit(self):
        self.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    sd = SoundSettingDialog()
    sd.show()
