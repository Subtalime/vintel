#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

from vi.resources import get_resource_path
from vi.cache.cache import Cache
from PyQt5.QtGui import QImage, QPixmap


class Avatar(QPixmap):
    def __init__(self, character=None):
        data = None
        if character:
            data = Cache().get_avatar(character)
        if not data:
            with open(get_resource_path("qmark.png"), "rb") as f:
                data = f.read()
        image = QImage.fromData(data)
        super(Avatar, self).__init__(image)
        self.scaledToHeight(32)
