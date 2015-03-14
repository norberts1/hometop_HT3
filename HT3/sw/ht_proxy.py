#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2015 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1.7  / Datum 25.02.2015 first release
#################################################################

import sys, time
sys.path.append('lib')
import ht_proxy_if
import logging

__author__  = "Norbert S <junky-zs@gmx.de>"
__status__  = "draft"
__version__ = "0.1.7"
__date__    = "25 February 2015"

configfile="./etc/config/ht_proxy_cfg.xml"
#zs# activate only for debugging purposes #
# ht_proxy=ht_proxy_if.cht_proxy_daemon(configfile, loglevel=logging.DEBUG)
ht_proxy=ht_proxy_if.cht_proxy_daemon(configfile)
ht_proxy.start()
while True:
    time.sleep(2)
