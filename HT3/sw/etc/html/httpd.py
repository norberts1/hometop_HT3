#!/usr/bin/python3
#
#################################################################
## Copyright (c) 2013 Norbert S. <junky-zs@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#################################################################
# Ver:0.1.5  / Datum 25.05.2014
# Ver:0.2    / 2021-02-17  port-number changed to 48086
#################################################################
#
#----------------------------------------------------
# Dateiname:  httpd.py
# Kleiner HTTP-Server, der auf den Port: 48086 verbindet.
# Die Daten muessen in dem Verzeichnis des Servers sein.
#----------------------------------------------------
#
from http.server import HTTPServer, CGIHTTPRequestHandler
serveradresse =("", 48086)
server=HTTPServer(serveradresse, CGIHTTPRequestHandler)
server.serve_forever()
