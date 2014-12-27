#! /usr/bin/python3
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
#  script sets GPIO11 (rapsi-header Pin23) to output
#
#   please install at first the python setuptools with command:
#        sudo apt-get install python-setuptools
#
#  you must be user: root to execute this script
#
#################################################################
#
import RPi.GPIO as GPIO

def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # setup Header Pin23 for output
    GPIO.setup (11, GPIO.OUT)

setup_gpio()
