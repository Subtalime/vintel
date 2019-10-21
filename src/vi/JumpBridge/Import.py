import logging, re

class Bridges(list):
    def __init__(self):
        self = []

    def export(self):
        bridgeList = []
        for bridge in self:
            routes = []
            routes.append(bridge.start)
            routes.append(bridge.direction)
            routes.append(bridge.end)
            bridgeList.append(routes)
        return bridgeList

class Bridge(object):
    def __init__(self, region: str, start: str, end: str, status: str="Online", distance: float=0., direction: str="<>"):
        self.region = region
        self.start = start
        self.end = end
        self.status = status
        self.distance = float(distance)
        self.direction = direction

class Import:
    def __init__(self):
        self.bridges = Bridges()

    def convertGarpaData(self, fileContent: list):
        self.bridges.clear()
        for line in fileContent:
            line = re.sub("[ \t]+", " ", line)
            if line.find("@") == -1:
                continue
            columns = line.split(" ")
            if len(columns) < 13:
                continue
            if columns[2] != "@" or columns[5] != "@":
                continue

            self.bridges.append(Bridge(columns[0], columns[1], columns[4], columns[7], columns[10]))
        if len(self.bridges) == 0:
            # maybe it's already in Export-Format?
            for line in fileContent:
                line = re.sub("[ \t]+", " ", line)
                columns = line.split(" ")
                if len(columns) != 3:
                    break
                self.bridges.append(Bridge(None, columns[0], columns[2], direction=columns[1]))

        return self.bridges.export()

    def readGarpaFile(self, fileName: str=None, clipboard: str=None):
        try:
            if not clipboard:
                with open(fileName, "r") as f:
                    content = f.read().splitlines(keepends=False)
            else:
                content = clipboard.splitlines(keepends=False)
            if content:
                return self.convertGarpaData(content)
        except Exception as e:
            logging.error("Error in importing Garpa Jumpbridges", e)
        return []


if __name__ == "__main__":
    importFile = "D:\\Develop\\vintel\\src\\vi\\ui\\res\\mapdata\\Goons-jump.txt"

    data = Import().readGarpaFile(importFile)
    print(data)

