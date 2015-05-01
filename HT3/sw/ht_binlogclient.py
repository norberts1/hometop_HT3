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
# Ver:0.1.8  / Datum 01.05.2015 first release
#################################################################

import sys, os
sys.path.append('lib')
import ht_proxy_if


configfile="./etc/config/ht_proxy_cfg.xml"

binfile="./var/log/ht_binlog.log"

if len(sys.argv) > 1:
    if '/' in str(sys.argv[1]):
        binfile=str(sys.argv[1])
    else:
        binfile=os.path.join("./var/log", str(sys.argv[1]))
    
try:
    print("   -- start binaer data logging to file: {0} --".format(binfile))
    fobj=open(binfile,"wb")
except:
    print("couldn't open file:{0}".format(binfile))
    raise

try:
    client=ht_proxy_if.cht_socket_client(configfile, devicetype=ht_proxy_if.DT_MODEM)
except:
    print("couldn't open proxy-client;check config-file:{0}".format(configfile))
    raise

loop=True
while loop:
    try:
        fobj.write(client.read())
    except (KeyboardInterrupt):
        loop=False
    except IOError:
        loop=False
        print("couldn't write to file:{0}".format(binfile))
        raise

    fobj.flush()


fobj.flush()
fobj.close()
