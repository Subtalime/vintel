class Character:
    monitor = False
    charname = None
    location = None

    def __init__(self, charname, status=True, location=None):
        self.charname = charname
        self.monitor = bool(eval(str(status)))
        self.location = None if location == 'None' else location

    def update(self, monitor=None, location=None):
        if monitor:
            self.setMonitoring(monitor)
        if location:
            self.setLocation(location)
        return self

    def setMonitoring(self, enable):
        self.monitor = enable

    def setLocation(self, location):
        self.location = location

    def getLocations(self):
        return self.location

    def disable(self):
        self.setMonitoring(False)

    def enable(self):
        self.setMonitoring(True)

    def getName(self):
        return self.charname

    def getStatus(self):
        return self.monitor

    def getMonitoring(self):
        return self.getStatus()

    def __repr__(self):
        return "{}.{}.{}".format(self.charname, self.monitor, self.location)

