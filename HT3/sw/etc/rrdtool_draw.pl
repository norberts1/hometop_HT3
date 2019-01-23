#!/usr/bin/perl
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
# Ver:0.1.7  / Datum 04.03.2015 'heizungspumpenleistung' added
#              https://www.mikrocontroller.net/topic/324673#3970615
# Ver:0.1.8  / Datum 19.01.2016 'Betriebsart' added
#              right_axis_label added see:
#              https://www.mikrocontroller.net/topic/324673#3972919
#              'Last' - Values added in legend.
# Ver:0.2    / Datum 29.08.2016 'Betriebsart' changed to
#                'TemperaturNiveau'.
#               Display: All 'Minutes' changed to 'hours':=Stunden.
#               'BZeit' changed to:LAST (from AVERAGE).
#               FB10 remote-controller deactivated.
# Ver:0.3    / Datum 10.03.2018 integer-format draw corrected
# Ver:0.3.1  / Datum 19.01.2019 sub-function handling added
#               new parameter for controller-type and hc_mixed-flag
#               new parameter for Thydraulic Switch added.
#               new item 'T-Soll Hydraulische Weiche' added.
#               solar_draw_second_field() and handling added.
#               gain_day_draw and gain_sum_draw added.
#################################################################

#
use strict;
use warnings;
use RRDTool::OO;
use File::Spec;


my $mypath       =$ARGV[0];
my $mytargetpath =$ARGV[1];
my $myanzahlheizkreise=$ARGV[2];
my $controller_type = $ARGV[3];
my $hc1_mixed    =$ARGV[4];
my $hc2_mixed    =$ARGV[5];
my $hc3_mixed    =$ARGV[6];
my $hc4_mixed    =$ARGV[7];
my $hg_Thydraulsw=$ARGV[8];
my $solar_available =$ARGV[9];
my $second_collector=$ARGV[10];


################################################################
# subfunction-declarations                                     #
################################################################
sub heater_device_draw($$$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
## p4 = Hydraulic Switch flag;
################################################################

sub heater_cricuit_draw($$$$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
## p4 = hc_nr;
## p5 = hc_mixed_flag; 0:=unmixed, 1:=mixed
################################################################

sub domestic_hotwater_draw($$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
################################################################

sub solar_draw($$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
################################################################

sub solar_yield_draw($$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
################################################################

sub solar_draw_second_field($$$);
## p1 = sourcepath;
## p2 = targetpath;
## p3 = controller_type; 1:=Fxyz, 2:= Cxyz
################################################################


if (not defined $mytargetpath) {
  $mytargetpath=$mypath;
}
if (not defined $controller_type) {
    # set default to Fxyz-controller
    $controller_type = 1;
}
if (not defined $hc1_mixed) {
    # set default to unmixed
    $hc1_mixed = 0;
}
if (not defined $hc2_mixed) {
    # set default to unmixed
    $hc2_mixed = 0;
}
if (not defined $hc3_mixed) {
    # set default to unmixed
    $hc3_mixed = 0;
}
if (not defined $hc4_mixed) {
    # set default to unmixed
    $hc4_mixed = 0;
}
if (not defined $hg_Thydraulsw) {
    # set default flag for T hydraulic Switch to 0
    $hg_Thydraulsw = 0;
}
if (not defined $solar_available) {
    # set default flag for Solarpart available to 1
    $solar_available = 1;
}
if (not defined $second_collector) {
    # set default flag for second collector available to 0
    $second_collector= 0;
}

# Set Starttime
my $start_time     = time()-2880*60;
my $end_time       = time()-60;

if (defined $myanzahlheizkreise) {
	if ($myanzahlheizkreise<1 or $myanzahlheizkreise>4) {
		$myanzahlheizkreise=1;
	}
} else {
	$myanzahlheizkreise=1;
}

### generate timestring for title
my ($vonsek, $vonmin, $vonhour, $vonday, $vonmon, $vonyear)=localtime($start_time);
my ($bissek, $bismin, $bishour, $bisday, $bismon, $bisyear)=localtime($end_time);
my $timeendstring=sprintf(" - %02d:%02d:%02d %02d.%02d.%04d)",$bishour,$bismin,$bissek,$bisday,$bismon+1,$bisyear+1900);
my $timestring   =sprintf(" (%02d:%02d:%02d %02d.%02d.",$vonhour,$vonmin,$vonsek,$vonday,$vonmon+1).$timeendstring;

# Anzeige gross/klein
my $AnzeigeGross	= 1;
my $mywidth		= 350;
my $myheight		= 160;
if ($AnzeigeGross == 1) {
	$mywidth	= 740;
	$myheight	= 310;
}

# heater-device draw
heater_device_draw($mypath, $mytargetpath, $controller_type, $hg_Thydraulsw);

# hot water draw
domestic_hotwater_draw($mypath, $mytargetpath, $controller_type);

# hc1 draw
heater_cricuit_draw($mypath, $mytargetpath, $controller_type, 1, $hc1_mixed);

if ($myanzahlheizkreise>1) {
# hc2 draw
	heater_cricuit_draw($mypath, $mytargetpath, $controller_type, 2, $hc2_mixed);
}
if ($myanzahlheizkreise>2) {
# hc3 draw
	heater_cricuit_draw($mypath, $mytargetpath, $controller_type, 3, $hc3_mixed);
}
if ($myanzahlheizkreise>3) {
# hc4 draw
	heater_cricuit_draw($mypath, $mytargetpath, $controller_type, 4, $hc4_mixed);
}

if ($solar_available > 0) {
# solar draw
	solar_draw($mypath, $mytargetpath, $controller_type);

# solar ertrag draw
	solar_yield_draw($mypath, $mytargetpath, $controller_type);

	if ($second_collector > 0) {
		solar_draw_second_field($mypath, $mytargetpath, $controller_type);
	}
}

################################################################
################################################################
sub heater_device_draw($$$$)
{
	my($sourcepath, $targetpath, $controller_type, $Thydraulsw) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_heizgeraet.rrd";
	my $DB               = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $rrdh             = RRDTool::OO->new(file => $DB);
	my $Image            = File::Spec->catfile($targetpath, "/HT3/sw/etc/html/HT3_Heizgeraet.png");

	my $ThydraulicSwitch_str = "";
	my $hydraulicSwitch_legendstr = "T-Soll (Hydraulische Weiche)";

	if ($Thydraulsw > 0) {
		$ThydraulicSwitch_str = '              last\:';
	} else {
		$ThydraulicSwitch_str = '   nicht vorhanden\:';
	}

	$rrdh->option_add("graph", "right_axis");
	$rrdh->option_add("graph", "right_axis_label");
	$rrdh->graph(
		image			=> $Image,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		title			=> 'Heizgerät'.$timestring,
		color			=> {
			back => '#ffdd55',
			canvas => '#fff6d5',
		},
		# Background draw fuer betriebsmodus:='heizen'
		draw		=> {
			dsname	=> 'V_modus',
			color	=> '0cccc0',
			type	=> 'hidden',
			name	=> 'modusfkt',
		},
		draw		=> {
			color	=> 'e9ddaf',
			type	=> 'area',
			cdef	=> "modusfkt,45,*"
		},
		draw		=> {
			dsname	=> 'V_leistung',
			name	=> "Brennerleistung",
			legend	=> 'Brennerleistung (%)',
			color	=> 'cccccc',
			type	=> 'area'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "Brennerleistung_last",
			vdef	=> "Brennerleistung,LAST"
		},
		comment		=> '                       last\:',
		gprint		=> {
			format	=> '%2.0lf\l',
			draw	=> 'Brennerleistung_last',
		},
		draw		=> {
			dsname	=> 'T_vorlauf_soll',
			name	=> "TSoll",
			legend	=> 'T-Soll (Regelung)',
			color	=> 'ff0000'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_last",
			vdef	=> "TSoll,LAST"
		},
		comment		=> '                         last\:',
		gprint		=> {
			format	=> '%2.0lf\l',
			draw	=> 'TSoll_last',
		},
		draw		=> {
			dsname	=> 'T_vorlauf_ist',
			name	=> "TIst",
			legend	=> 'T-Ist  (Vorlauf)',
			thickness => 1,
			color	=> '0000ff'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_last",
			vdef	=> "TIst,LAST"
		},
		comment		=> '                          last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TIst_last',
		},
		draw		=> {
			dsname	=> 'T_ruecklauf',
			name	=> "TRueck",
			legend	=> 'Rücklauf',
			thickness => 1,
			color	=> '00ff00'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TRueck_last",
			vdef	=> "TRueck,LAST"
		},
		comment		=> '                                  last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TRueck_last',
		},
		draw           => {
			dsname => 'V_zirkula_pumpe',
			type	=> "hidden",
			name	=> 'zirkula_pumpe',
		},
		draw		=> {
			color	=> 'd45500',
			type	=> "area",
			legend	=> 'Zirkulations-Pumpe\l',
			cdef	=> "zirkula_pumpe,10,*"
		},
	#Rev.:0.1.7 ######### deactivated
	#	draw           => {
	#		dsname => 'V_heizungs_pumpe',
	#		type	=> "hidden",
	#		name	=> 'Heizungspumpe',
	#	},
	#Rev.:0.1.7 ######### new using of 'V_spare_1'.
		draw           => {
			dsname => 'V_spare_1',
			name	=> 'Heizungspumpenleistung',
			color	=> '008d00',
			legend => 'Heizungspumpenleistung (%)',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "HP_Leistung_last",
			vdef	=> "Heizungspumpenleistung,LAST"
		},
		comment		=> '                last\:',
		gprint		=> {
			format	=> '%2.0lf\l',
			draw	=> 'HP_Leistung_last',
		},
	#Rev.:0.1.7 ######### deaktiviert
	#	draw		=> {
	#		color	=> '008d00',
	#		type	=> "area",
	#		legend => 'Heizungspumpe\l',
	#		cdef	=> "Heizungspumpe,5,*"
	#	},
		draw		=> {
			dsname	=> 'T_aussen',
			name	=> 'Aussentemperatur',
			legend	=> 'Aussentemperatur min\:',
			thickness => 2,
			color	=> '000055'
		},
		# vdef for calculating Maximum, Minimum of 'Aussentemperatur'
		draw		=> {
			type	=> "hidden",
			name	=> "Aussentemperatur_min",
			vdef	=> "Aussentemperatur,MINIMUM",
		},
		gprint		=> {
			format	=> '%3.1lf',
			draw	=> 'Aussentemperatur_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "Aussentemperatur_max",
			vdef	=> "Aussentemperatur,MAXIMUM",
		},
		comment		=> 'max\:',
		gprint		=> {
			format	=> '%3.1lf',
			draw	=> 'Aussentemperatur_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "Aussentemperatur_last",
			vdef	=> "Aussentemperatur,LAST"
		},
		comment		=> '   last\:',
		gprint		=> {
			format	=> '%3.1lf\l',
			draw	=> 'Aussentemperatur_last',
		},
		draw		=> {
			dsname	=> 'C_betrieb_gesamt',
			name	=> 'BZeitg',
			type	=> "hidden",
			cfunc	=> 'LAST'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "BZeitg_average",
			vdef	=> "BZeitg,LAST",
		},
		gprint		=> {
			format	=> '  Betriebszeit gesamt \: %6.1lf Stunden\l',
			draw	=> 'BZeitg_average',
		},
		draw		=> {
			dsname	=> 'C_brenner_heizung',
			name	=> 'brennereinheiz',
			type	=> "hidden",
			cfunc	=> 'LAST'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "brennereinheiz_last",
			vdef	=> "brennereinheiz,LAST",
		},
		gprint		=> {
			format	=> '  Brenner ein         \: %6.0lf Zähler\l',
			draw	=> 'brennereinheiz_last',
		},
		draw		=> {
			dsname => 'V_spare_2',
			name	=> 'T_hydraulic_switch',
			color	=> 'ff8080',
			legend => $hydraulicSwitch_legendstr,
		},
		draw		=> {
			type	=> "hidden",
			name	=> "T_hydraulic_switch_last",
			vdef	=> "T_hydraulic_switch,LAST"
		},
		comment		=> $ThydraulicSwitch_str,
		gprint		=> {
			format	=> '%3.1lf\l',
			draw	=> 'T_hydraulic_switch_last',
		},
	);
} # heater_device_draw()
################################################################

sub domestic_hotwater_draw($$$)
{
	my($sourcepath, $targetpath, $controller_type) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_warmwasser.rrd";
	my $DB               = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $rrdh             = RRDTool::OO->new(file => $DB);
	my $Image            = File::Spec->catfile($targetpath, "/HT3/sw/etc/html/HT3_Warmwasser.png");

	$rrdh->option_add("graph", "right_axis");
	$rrdh->option_add("graph", "right_axis_label");
	$rrdh->graph(
		image			=> $Image,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		title			=> 'Warmwasser'.$timestring,
		color			=> {
			back => '#aaccff',
			canvas => '#d5e5ff',
		},
		draw		=> {
			dsname	=> 'T_soll',
			legend	=> 'T-Soll\l',
			color	=> 'ff0000'
		},
		draw		=> {
			dsname	=> 'T_ist',
			legend	=> 'T-Ist\l',
			color	=> '0000ff'
		},
		draw           => {
			dsname => 'V_WW_erzeugung',
			type	=> "hidden",
			name	=> 'WW_erzeugung',
		},
		draw		=> {
			type	=> "area",
			color	=> '008dff',
			legend  => 'Warmwasser Erzeugung\l',
			cdef	=> "WW_erzeugung,10,*"
		},
		draw           => {
			dsname => 'V_WW_temp_OK',
			type	=> "hidden",
			name	=> 'WW_temp_OK',
		},
		draw		=> {
			type	=> "area",
			color	=> '008d00',
			legend  => 'Speichertemperatur OK\l',
			cdef	=> "WW_temp_OK,5,*"
		},
		draw		=> {
			dsname	=> 'T_speicher',
			legend	=> 'T-Speicher min\:',
			name	=> 'Speicher',
			thickness => 2,
			color	=> '00ff00'
		},
		# vdef for calculating Maximum, Minimum of 'Speicher'
		draw		=> {
			type	=> "hidden",
			name	=> "Speicher_min",
			vdef	=> "Speicher,MINIMUM",
		},
		gprint		=> {
			format	=> '%3.1lf',
		draw	=> 'Speicher_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "Speicher_max",
			vdef	=> "Speicher,MAXIMUM",
		},
		gprint		=> {
			format	=> 'max\:%3.1lf',
			draw	=> 'Speicher_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "Speicher_last",
			vdef	=> "Speicher,LAST"
		},
		comment		=> ' last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'Speicher_last',
		},
		draw		=> {
			dsname	=> 'C_betriebs_zeit',
			name	=> 'BZeit',
			type	=> "hidden",
		},
		draw		=> {
			type	=> "hidden",
			name	=> "BZeit_last",
			vdef	=> "BZeit,LAST",
		},
		gprint		=> {
			format	=> '  Betriebszeit  \:%5.1lf Stunden',
			draw	=> 'BZeit_last',
		},
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
		comment		=> ' \s',
	);
} #domestic_hotwater_draw()
################################################################

sub solar_draw($$$)
{
	my($sourcepath, $targetpath, $controller_type) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_solar.rrd";
	my $DB               = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $rrdh             = RRDTool::OO->new(file => $DB);
	my $Image            = File::Spec->catfile($targetpath, "/HT3/sw/etc/html/HT3_Solar.png");

	$rrdh->option_add("graph", "right_axis");
	$rrdh->option_add("graph", "right_axis_label");
	$rrdh->graph(
		image			=> $Image,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		title	=> 'Solar'.$timestring,
		color			=> {
			back => '#c6e9af',
			canvas => '#e3f4d7',
		},
		##### Speicher unten #####
		draw		=> {
			dsname	=> 'T_speicher_unten',
			legend	=> 'T-Solarspeicher unten',
			thickness => 1,
			color	=> '00ff88',
			type	=> 'area',
			name	=> 'speiunten',
		},
		# vdef for calculating Maximum, Minimum of 'Speicher unten'
		draw		=> {
			type	=> "hidden",
			name	=> "speiunten_min",
			vdef	=> "speiunten,MINIMUM",
		},
		gprint		=> {
			format	=> 'min\:%03.1lf',
			draw	=> 'speiunten_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "speiunten_max",
			vdef	=> "speiunten,MAXIMUM",
		},
		gprint		=> {
			format	=> 'max\:%03.1lf',
			draw	=> 'speiunten_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "speiunten_last",
			vdef	=> "speiunten,LAST"
		},
		comment		=> ' last\:',
		gprint		=> {
			format	=> '%03.1lf\l',
			draw	=> 'speiunten_last',
		},
		comment	=>	'\j',
		##### Kollektor #####
		draw	=> {
			dsname	=> 'T_kollektor',
			color	=> 'cccc00',
			type	=> 'area',
			name	=> 'kollektor'  # name fuer den hidden draw
		},
		draw		=> {
			dsname	=> 'T_kollektor',
			legend	=> 'T-Kollektor          ',
			thickness => 1,
			color	=> 'ffcc00',
			cfunc	=> 'AVERAGE'
		},
		# vdef for calculating Maximum, Minimum of 'Kollektor'
		draw		=> {
			type	=> "hidden",
			name	=> "kollektor_min",
			vdef	=> "kollektor,MINIMUM",
		},
		gprint		=> {
			format	=> 'min\:%03.1lf',
			draw	=> 'kollektor_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "kollektor_max",
			vdef	=> "kollektor,MAXIMUM",
		},
		gprint		=> {
			format	=> 'max\:%03.1lf',
			draw	=> 'kollektor_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "kollektor_last",
			vdef	=> "kollektor,LAST"
		},
		comment		=> ' last\:',
		gprint		=> {
			format	=> '%03.1lf\l',
			draw	=> 'kollektor_last',
		},
		draw		=> {
			dsname	=> 'T_speicher_unten',
			thickness => 1,
			color	=> '00ffcc',
		},

		##### Solarpumpe #####
		draw		=> {
			dsname	=> 'V_solar_pumpe',
			type	=> "hidden",
			name	=> 'solpumpe'  # name fuer den hidden draw
		},
		draw		=> {
			color	=> 'ff6600',
			legend	=> 'Solarpumpe an\l',
			type	=> 'area',
			cdef	=> "solpumpe,5,*"
		},
		comment		=> ' \s',
		comment		=> ' \s',
	);
} # solar_draw()
################################################################

sub solar_yield_draw($$$)
{
	my($sourcepath, $targetpath, $controller_type) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_solar.rrd";
	my $DB               = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $rrdh             = RRDTool::OO->new(file => $DB);
	my $Image            = File::Spec->catfile($targetpath, "/HT3/sw/etc/html/HT3_Solarertrag.png");

	$rrdh->option_add("graph", "right_axis");
	$rrdh->option_add("graph", "right_axis_label");
	$rrdh->graph(
		image			=> $Image,
		vertical_label	=> '(k)Wh',
		right_axis	=> '1:0',
		right_axis_label	=> '(k)Wh',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		color			=>	{
			back => '#c6e9af',
			canvas => '#e3f4d7',
		},
		title		=> 'Solar Ertrag'.$timestring,

		##### Ertrag pro Stunde #####
		draw		=> {
			dsname	=> 'V_ertrag_stunde',
			legend	=> 'Ertrag/Stunde  max\:',
			color	=> 'aa88f0',
			type	=> 'area'
		},
		draw		=> {
			dsname	=> 'V_ertrag_stunde',
			color	=> 'aa8800',
			thickness => 2,
			name	=> 'ertrag_std',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "ertrag_draw",
			vdef	=> "ertrag_std,MAXIMUM",
		},
		gprint		=> {
			format	=> '%6.1lf %SWh',
			draw	=> 'ertrag_draw',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "ertrag_std_last",
			vdef	=> "ertrag_std,LAST"
		},
		comment		=> ' last\:',
		gprint		=> {
			format	=> '%6.1lf\l',
			draw	=> 'ertrag_std_last',
		},
		##### Ertrag / Tag #############
		draw		=> {
			dsname	=> 'V_ertrag_tag_calc',
			name	=> 'gain_day',
			type	=> "hidden",
		},
		draw		=> {
			type	=> "hidden",
			name	=> "gain_day_draw",
			vdef	=> "gain_day,LAST",
		},
		gprint		=> {
			format	=> '  Ertrag/Tag        \:   %5.1lf kWh\l',
			draw	=> 'gain_day_draw',
		},
		##### Ertrag / Summe ###########
		draw		=> {
			dsname	=> 'V_ertrag_sum_calc',
			name	=> 'gain_sum',
			type	=> "hidden",
		},
		draw		=> {
			type	=> "hidden",
			name	=> "gain_sum_draw",
			vdef	=> "gain_sum,LAST",
		},
		gprint		=> {
			format	=> '  Ertrag/Summe      \:   %5.1lf kWh\l',
			draw	=> 'gain_sum_draw',
		},
		##### Solarpumpen-Laufzeit #####
		draw		=> {
			dsname	=> 'C_laufzeit',
			name	=> 'pumpenlaufzeit',
			type	=> "hidden",
		},
		draw		=> {
			type	=> "hidden",
			name	=> "pumpenlauf_draw",
			vdef	=> "pumpenlaufzeit,LAST",
	#		cdef	=> "pumpenlaufzeit,0.017,*",
		},
		gprint		=> {
			format	=> '  Laufzeit Pumpe    \:   %5.1lf Stunden',
			draw	=> 'pumpenlauf_draw',
		},
		comment		=> ' \s',
		comment		=> ' \s'
	);
} # solar_yield_draw()
################################################################

sub heater_cricuit_draw($$$$$)
{
	my($sourcepath, $targetpath, $controller_type, $hc_nr, $hc_mixed) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_heizkreis".$hc_nr.".rrd";
	my $draw_filename    = "/HT3/sw/etc/html/HT3_Heizkreis".$hc_nr.".png";
	my $DB_heizkreis     = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $heizkreis_rrdh   = RRDTool::OO->new(file => $DB_heizkreis);
	my $ImageHK = File::Spec->catfile($targetpath, $draw_filename);

	my $draw_titel       = "Heizkreis:".$hc_nr." (ohne Mischer)";
    if ($hc_mixed > 0)
    {
        $draw_titel      = "Heizkreis:".$hc_nr." (mit Mischer)";
    }

    my $str_tempniveau = 'Temperatur Niveau (3=Heizen 2=Sparen 1=Frost)\l';
    if ($controller_type == 2)
    {
        $str_tempniveau = 'Temperatur Niveau (3=Comfort2 2=Comfort1 1=Eco)\l';
    }

	$heizkreis_rrdh->option_add("graph", "right_axis");
	$heizkreis_rrdh->option_add("graph", "right_axis_label");
	$heizkreis_rrdh->graph(
		image			=> $ImageHK,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		title			=> $draw_titel.$timestring,
		color			=> {
			back => '#ffeeaa',
			canvas => '#fff6d5',
		},
#Rev.:0.2   ######### 'Betriebsart' changed to 'TemperaturNiveau'
		draw		=> {
			dsname	=> 'V_tempera_niveau',
			name	=> 'TemperaturNiveau',
			type	=> 'hidden',
		},
		draw		=> {
			color	=> 'd0d0d0',
			type	=> 'area',
			cdef	=> "TemperaturNiveau,1,*",
			legend	=> $str_tempniveau,
			thickness => 2,
		},
########### neu anfang ######################
# T-Soll (Vorlauf)
		draw		=> {
			dsname	=> 'V_spare_1',
			name	=> 'TSollVorlauf_HK',
			legend	=> 'T-Soll (Vorlauf)   min\:',
			color	=> 'ffa000'
		},
			# vdef for calculating Maximum, Minimum of 'T-Soll (Vorlauf)'
			draw		=> {
				type	=> "hidden",
				name	=> "TSollVorlauf_HK_min",
				vdef	=> "TSollVorlauf_HK,MINIMUM",
			},
			gprint	=> {
				format	=> '%2.1lf',
				draw	=> 'TSollVorlauf_HK_min',
			},
			draw		=> {
				type	=> "hidden",
				name	=> "TSollVorlauf_HK_max",
				vdef	=> "TSollVorlauf_HK,MAXIMUM",
			},
			comment		=> 'max\:',
			gprint	=> {
				format	=> '%2.1lf',
				draw	=> 'TSollVorlauf_HK_max',
			},
		comment		=> 'last\:',
		draw		=> {
			type	=> "hidden",
			name	=> "TSollVorlauf_HK_last",
			vdef	=> "TSollVorlauf_HK,LAST"
		},
		gprint	=> {
			format	=> '%2.1lf\l',
			draw	=> 'TSollVorlauf_HK_last',
		},
########### neu ende #########################
		draw		=> {
			dsname	=> 'T_soll_HK',
			name	=> 'TSoll_HK',
			legend	=> 'T-Soll (gewünscht) min\:',
			color	=> 'ff0000'
		},
		# vdef for calculating Maximum, Minimum of 'T-Soll (gewünscht)'
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_min",
			vdef	=> "TSoll_HK,MINIMUM",
		},
		gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TSoll_HK_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_max",
			vdef	=> "TSoll_HK,MAXIMUM",
		},
		comment		=> 'max\:',
			gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TSoll_HK_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_last",
			vdef	=> "TSoll_HK,LAST"
		},
		comment		=> 'last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TSoll_HK_last',
		},
		draw		=> {
			dsname	=> 'T_ist_HK',
			name	=> 'TIst_HK',
			legend	=> 'T-Ist  (Raum)      min\:',
			color	=> '00ff00'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_last",
			vdef	=> "TIst_HK,LAST"
		},
		# vdef for calculating Maximum, Minimum of 'T-Ist  (Raum)'
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_HK_min",
			vdef	=> "TIst_HK,MINIMUM",
		},
		gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TIst_HK_HK_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_max",
			vdef	=> "TIst_HK,MAXIMUM",
		},
		comment		=> 'max\:',
		gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TIst_HK_max',
		},
		comment		=> 'last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TIst_HK_last',
		},

####### activate this if you are using a remote-controller #######################
#		draw		=> {
#			dsname	=> 'T_steuer_FB',
#			name	=> 'Raumtemperatur',
#			legend	=> 'T-Raum (FB10) min\:',
#			thickness => 2,
#			color	=> '8080ff'
#		},
#		# vdef for calculating Maximum, Minimum of 'Raumtemperatur'
#		draw		=> {
#			type	=> "hidden",
#			name	=> "Raumtemperatur_min",
#		vdef	=> "Raumtemperatur,MINIMUM",
#		},
#		gprint		=> {
#			format	=> '%3.1lf',
#			draw	=> 'Raumtemperatur_min',
#		},
#		draw		=> {
#			type	=> "hidden",
#			name	=> "Raumtemperatur_max",
#			vdef	=> "Raumtemperatur,MAXIMUM",
#		},
#		comment		=> 'max\:',
#		gprint		=> {
#			format	=> '%3.1lf',
#			draw	=> 'Raumtemperatur_max',
#		},
#		draw		=> {
#			type	=> "hidden",
#			name	=> "Raumtemperatur_HK_last",
#			vdef	=> "Raumtemperatur,LAST"
#		},
#		comment		=> '   last\:',
#		gprint		=> {
#			format	=> '%2.1lf\l',
#			draw	=> 'Raumtemperatur_HK_last',
#		},
##############################

###########################
# addon for IPM / MP - Moduls
		draw		=> {
			dsname	=> 'T_vorlauf_misch_HK',
			name	=> 'TMischer_HK',
			legend	=> 'T-Mischer          min\:',
			color	=> 'ffc000'
		},
		# vdef for calculating Maximum, Minimum of 'T-Mischer'
		draw		=> {
		type	=> "hidden",
		name	=> "TMischer_HK_min",
		vdef	=> "TMischer_HK,MINIMUM",
		},
		gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TMischer_HK_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TMischer_HK_max",
			vdef	=> "TMischer_HK,MAXIMUM",
		},
		comment		=> 'max\:',
		gprint		=> {
			format	=> '%2.1lf',
			draw	=> 'TMischer_HK_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TMischer_HK_last",
			vdef	=> "TMischer_HK,LAST"
		},
		comment		=> 'last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TMischer_HK_last',
		},
# Heizkreispumpe
		draw		=> {
			dsname	=> 'V_spare_2',
			name	=> 'HK_pumpe',
			legend	=> 'HK-Pumpe',
			color	=> 'fb00f0',
			type	=> 'area',
		},
	);
}
###########################

sub solar_draw_second_field($$$)
{
	my($sourcepath, $targetpath, $controller_type) = @_;
	my $rrdtool_filename = "/HT3/sw/var/databases/HT3_db_rrd_solar.rrd";
	my $DB               = File::Spec->catfile($sourcepath, $rrdtool_filename);
	my $rrdh             = RRDTool::OO->new(file => $DB);
	my $Image            = File::Spec->catfile($targetpath, "/HT3/sw/etc/html/HT3_Solar_second.png");

	$rrdh->option_add("graph", "right_axis");
	$rrdh->option_add("graph", "right_axis_label");
	$rrdh->graph(
		image			=> $Image,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height		=> $myheight,
		title	=> '2. Wärmequelle'.$timestring,
		color			=> {
			back => '#c6e9af',
			canvas => '#e3f4d7',
		},
		##### Second Kollektor #####
		draw	=> {
			dsname	=> 'V_spare_1',
			color	=> 'cccc00',
#			type	=> 'area',
			name	=> '2_kollektor'  # name fuer den hidden draw
		},
		draw		=> {
			dsname	=> 'V_spare_1',
			legend	=> '2. T-Kollektor          ',
			thickness => 2,
			color	=> 'ffcc00'
		},
		# vdef for calculating Maximum, Minimum of 'Kollektor'
		draw		=> {
			type	=> "hidden",
			name	=> "2_kollektor_min",
			vdef	=> "2_kollektor,MINIMUM",
		},
		gprint		=> {
			format	=> 'min\:%03.1lf',
			draw	=> '2_kollektor_min',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "2_kollektor_max",
			vdef	=> "2_kollektor,MAXIMUM",
		},
		gprint		=> {
			format	=> 'max\:%03.1lf',
			draw	=> '2_kollektor_max',
		},
		draw		=> {
			type	=> "hidden",
			name	=> "2_kollektor_last",
			vdef	=> "2_kollektor,LAST"
		},
		comment		=> ' last\:',
		gprint		=> {
			format	=> '%03.1lf\l',
			draw	=> '2_kollektor_last',
		},

		##### second pump #####
		draw		=> {
			dsname	=> 'V_spare_2',
			type	=> "hidden",
			name	=> '2_solpumpe'  # name fuer den hidden draw
		},
		draw		=> {
			color	=> 'ff6600',
			legend	=> '2. Pumpe an\l',
			type	=> 'area',
			cdef	=> "2_solpumpe,5,*"
		},
		comment		=> ' \s',
		comment		=> ' \s',
	);
} # solar_draw_second_field()
################################################################

