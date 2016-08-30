#! /usr/bin/python3
#
#################################################################
## Copyright (c) 2016 Norbert S. <junky-zs@gmx.de>
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
# Ver:0.1    / Datum 20.07.2016 first release
# Ver:0.2    / Datum 29.08.2016
#################################################################


# Bus-Type definitions mainly used for GUI-support cause on bluddy
#  hell of telegramms running on different bus-systems
BUS_TYPE_EMS = 1
BUS_TYPE_HT2 = 2    # not supported
BUS_TYPE_HT3 = 3
BUS_TYPE_CAN = 4    # not supported


#### Heatronic -typed constants ####
##### ID357 - ID360 #############################################
 # msg ID357 to ID360 offsets for heating-circuits
 #  (Bauart, temperatur_niveaus)
HT_OFFSET_357_360_HC_TYPE            = 0
HT_OFFSET_357_360_RC_TYPE            = 1
HT_OFFSET_357_360_ACTIVE_PROGRAMM   = 13
HT_OFFSET_357_360_OP_MODE_HC        = 14
HT_OFFSET_357_360_TEMPNIVEAU_FROST  = 15
HT_OFFSET_357_360_TEMPNIVEAU_SPAREN = 16
HT_OFFSET_357_360_TEMPNIVEAU_NORMAL = 17
HT_OFFSET_357_360_HEATUP_SPEED      = 18
HT_OFFSET_357_360_HOLIDAY_OP_MODE   = 19

HT_OFFSET_377_380_OP_MODE_HC         = 4


HT_TEMPNIVEAU_FROST = "frost"
HT_TEMPNIVEAU_SPAREN = "sparen"
HT_TEMPNIVEAU_NORMAL = "heizen"
HT_TEMPNIVEAU_HEIZEN = HT_TEMPNIVEAU_NORMAL
HT_TEMPNIVEAU_DUMMY = ""

HT_HC_MODE_AUTO = "auto"
HT_HC_MODE_MANUAL = "manual"

HT_OPERATING_STATUS_HC_NONE   = 0
HT_OPERATING_STATUS_HC_FROST  = 1
HT_OPERATING_STATUS_HC_SPAR   = 2
HT_OPERATING_STATUS_HC_NORMAL = 3
HT_OPERATING_STATUS_HC_AUTO   = 4

#### EMS -typed constants ####
##### ID677 - ID684 #############################################
 # msg ID677 to ID684 offsets (SP := SetPoint,RTSP := Room temp SP)
EMS_OFFSET_CURRENT_ROOM_TEMP    = 0
EMS_OFFSET_STATUS_FLAG          = 2
EMS_OFFSET_CURRENT_ROOM_TEMP_SP = 6
EMS_OFFSET_NEXT_ROOM_TEMP_SP    = 7
EMS_OFFSET_TIME_2_NEXT_TEMP_SP  = 8
EMS_OFFSET_RTSD_STATUS         = 10
EMS_OFFSET_RTSP_HEATING_LEVEL  = 11
EMS_OFFSET_OPERATING_STATUS_HC = 21
 # values
EMS_STATUS_FLAG_HEAT_POSSIBLE     = 0x01
EMS_STATUS_FLAG_FROST_DANGER_OUTD = 0x02
EMS_STATUS_FLAG_FROST_DANGER_IND  = 0x04
EMS_STATUS_FLAG_OPEN_WINDOW       = 0x08
EMS_STATUS_FLAG_HC_SUMMER_MODE    = 0x10

EMS_RTSD_STATUS_SET_AUTOMATIC     = 0x01
EMS_RTSD_STATUS_COMFORT_ACTIVE    = 0x02
EMS_RTSD_STATUS_TEMP_INC_COMF_ACT = 0x04
EMS_RTSD_STATUS_PREV_ECO_ACTIVE   = 0x08

EMS_RTSP_HEATING_LEVEL_ECO      = 1
EMS_RTSP_HEATING_LEVEL_COMFORT1 = 2
EMS_RTSP_HEATING_LEVEL_COMFORT2 = 3
EMS_RTSP_HEATING_LEVEL_COMFORT3 = 4

EMS_OPERATING_STATUS_HC_OFF     = 0
EMS_OPERATING_STATUS_HC_SUMMER  = 1
EMS_OPERATING_STATUS_HC_MANUAL  = 2
EMS_OPERATING_STATUS_HC_COMFORT = 3
EMS_OPERATING_STATUS_HC_ECO     = 4


##### ID697 - ID704 #############################################
 # msg ID697 to ID704 offsets (SP := SetPoint)
EMS_OFFSET_RTSP_OPERATION_MODE = 0
EMS_OFFSET_COMFORT3_SP    = 1
EMS_OFFSET_COMFORT2_SP    = 2
EMS_OFFSET_COMFORT1_SP    = 3
EMS_OFFSET_ECO_SP         = 4
EMS_OFFSET_ECO_MODE       = 5
EMS_OFFSET_TEMPORARY_SP   = 8
EMS_OFFSET_OUTD_THRESHOLD = 9
EMS_OFFSET_MANUAL_SP     = 10
 # Operation Mode values #
EMS_OMODE_AUTO          = 0xff
EMS_OMODE_MANUAL        = 0
 # ECO Mode values #
EMS_ECO_MODE_OFF        = 0
EMS_ECO_MODE_HOLD_OUTD  = 1
EMS_ECO_MODE_HOLD_ROOM  = 2
EMS_ECO_MODE_REDUCED    = 3

EMS_TEMP_MODE_COMFORT1  = "comfort1"
EMS_TEMP_MODE_COMFORT2  = "comfort2"
EMS_TEMP_MODE_COMFORT3  = "comfort3"
EMS_TEMP_MODE_ECO       = "eco"
EMS_TEMP_MODE_TEMPORARY = "temporary"
EMS_TEMP_MODE_MANUAL    = "manual"


##### ID797 - ID798 #############################################
 # msg ID797 to ID798 offsets HotWater-circuits 1/2
EMS_OFFSET_DHW_EXTRA_ACTIVE    = 0
EMS_OFFSET_HOLIDAY_MODE_ACTIVE = 1
EMS_OFFSET_STATUS_CURRENT_SP   = 2
EMS_OFFSET_STATUS_CIRC_PUMP_SP = 3
# values
EMS_FALSE               = 0
EMS_TRUE                = 1
EMS_HOLIDAY_MODE_NONE     = 0
EMS_HOLIDAY_MODE_AUTO     = 1
EMS_HOLIDAY_MODE_OFF      = 2
EMS_HOLIDAY_MODE_OFF_TD   = 3
EMS_STATUS_CURRENT_FPD         = 1
EMS_STATUS_CURRENT_EXTRA       = 2
EMS_STATUS_CURRENT_MANUEL_OFF  = 3
EMS_STATUS_CURRENT_MANUEL_LOW  = 4
EMS_STATUS_CURRENT_MANUEL_HIGH = 5
EMS_STATUS_CURRENT_HOLIDAY_OFF = 6
EMS_STATUS_CURRENT_HOLIDAY_LOW = 7
EMS_STATUS_CURRENT_CLOCK_OFF   = 8
EMS_STATUS_CURRENT_CLOCK_LOW   = 9
EMS_STATUS_CURRENT_CLOCK_HIGH = 10
EMS_STATUS_CIRC_PUMP_FPD         = 1
EMS_STATUS_CIRC_PUMP_EXTRA       = 2
EMS_STATUS_CIRC_PUMP_MANUEL_OFF  = 3
EMS_STATUS_CIRC_PUMP_MANUEL_ON   = 4
EMS_STATUS_CIRC_PUMP_HOLIDAY_OFF = 5
EMS_STATUS_CIRC_PUMP_CLOCK_OFF   = 6
EMS_STATUS_CIRC_PUMP_CLOCK_ON    = 7

##### Message ID's ##############################################
 # msg_id's
  # (Heatronic)
ID357_TEMP_NIVEAU_HC1 = 357
ID358_TEMP_NIVEAU_HC2 = 358
ID359_TEMP_NIVEAU_HC3 = 359
ID360_TEMP_NIVEAU_HC4 = 360

ID377_CIRCUIT_TYPE_HC1 = 377
ID378_CIRCUIT_TYPE_HC2 = 378
ID379_CIRCUIT_TYPE_HC3 = 379
ID380_CIRCUIT_TYPE_HC4 = 380

  #  (EMS)
ID677_RTSD_HC1 = 677
ID678_RTSD_HC2 = 678
ID679_RTSD_HC3 = 679
ID680_RTSD_HC4 = 680
ID697_RTSD_HC1 = 697
ID698_RTSD_HC2 = 698
ID699_RTSD_HC3 = 699
ID700_RTSD_HC4 = 700
ID797_DHW1 = 797    # HotWater-circuit 1
ID798_DHW2 = 798    # HotWater-circuit 2

if __name__ == "__main__":
    pass
