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
#################################################################

#
use strict;
use warnings;
use RRDTool::OO;
use File::Spec;


my $mypath       =$ARGV[0];
my $mytargetpath =$ARGV[1];
my $myanzahlheizkreise=$ARGV[2];
my $mystart_param=$ARGV[3];
my $myend_param  =$ARGV[4];

if (not defined $mytargetpath) {
  $mytargetpath=$mypath;
}


my $rc = 0;
my $DB_heizgeraet   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_heizgeraet.rrd");
my $heizgeraet_rrdh = RRDTool::OO->new(file => $DB_heizgeraet);
my $DB_heizkreis1   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_heizkreis1.rrd");
my $heizkreis1_rrdh = RRDTool::OO->new(file => $DB_heizkreis1);
my $DB_heizkreis2   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_heizkreis2.rrd");
my $heizkreis2_rrdh = RRDTool::OO->new(file => $DB_heizkreis2);
my $DB_heizkreis3   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_heizkreis3.rrd");
my $heizkreis3_rrdh = RRDTool::OO->new(file => $DB_heizkreis3);
my $DB_heizkreis4   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_heizkreis4.rrd");
my $heizkreis4_rrdh = RRDTool::OO->new(file => $DB_heizkreis4);
my $DB_warmwasser   = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_warmwasser.rrd");
my $warmwasser_rrdh = RRDTool::OO->new(file => $DB_warmwasser);
my $DB_solar        = File::Spec->catfile($mypath,"/HT3/sw/var/databases/HT3_db_rrd_solar.rrd");
my $solar_rrdh      = RRDTool::OO->new(file => $DB_solar);
# 
# Set Starttime
my $start_time     = time()-2880*60;
my $end_time       = time()-60;

if ( defined $mystart_param && defined $myend_param ){
	if ($mystart_param < $myend_param) {
		$start_time = $mystart_param;
		$end_time   = $myend_param;
	} else {
		$start_time = $myend_param;
		$end_time   = $mystart_param;
	}
} else {
	if (defined $mystart_param) {
		$start_time = $mystart_param;
	}
}

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

my $ImageHG  = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Heizgeraet.png");
my $ImageHK1 = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Heizkreis1.png");
my $ImageHK2 = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Heizkreis2.png");
my $ImageHK3 = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Heizkreis3.png");
my $ImageHK4 = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Heizkreis4.png");
my $ImageWW  = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Warmwasser.png");
my $ImageSO  = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Solar.png");
my $ImageSO_ertrag = File::Spec->catfile($mytargetpath,"/HT3/sw/etc/html/HT3_Solarertrag.png");

$rc = $heizgeraet_rrdh->option_add("graph", "right_axis");
$rc = $heizgeraet_rrdh->option_add("graph", "right_axis_label");
$rc = $heizgeraet_rrdh->graph(
	image			=> $ImageHG,
	vertical_label	=> 'Temperaturen (Celsius)',
	right_axis	=> '1:0',
	right_axis_label	=> 'Temperaturen (Celsius)',
	start			=> $start_time,
	end				=> $end_time,
	width			=> $mywidth,
	height			=> $myheight,
	title			=> 'Heizgerät'.$timestring,
	color			=> { back => '#ffdd55',
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
		format	=> '%2.lf\l',
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
		format	=> '%2.lf\l',
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
		format	=> '%2.lf\l',
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
		format	=> '  Brenner ein         \: %6.lf Zähler',
		draw	=> 'brennereinheiz_last',
	},
	comment		=> ' \s',
	comment		=> ' \s',
);

$rc = $heizkreis1_rrdh->option_add("graph", "right_axis");
$rc = $heizkreis1_rrdh->option_add("graph", "right_axis_label");
$rc = $heizkreis1_rrdh->graph(
	image			=> $ImageHK1,
	vertical_label	=> 'Temperaturen (Celsius)',
	right_axis	=> '1:0',
	right_axis_label	=> 'Temperaturen (Celsius)',
	start			=> $start_time,
	end				=> $end_time,
	width			=> $mywidth,
	height			=> $myheight,
	title			=> 'Heizkreis 1'.$timestring,
	color			=> {back => '#ffeeaa',
						canvas => '#fff6d5',
	},
	draw		=> {
		dsname	=> 'T_soll_HK',
		name	=> 'TSoll_HK',
		legend	=> 'T-Soll (gewünscht)',
		color	=> 'ff0000'
	},
	draw		=> {
		type	=> "hidden",
		name	=> "TSoll_HK_last",
		vdef	=> "TSoll_HK,LAST"
	},
	comment		=> '                            last\:',
	gprint		=> {
		format	=> '%2.1lf\l',
		draw	=> 'TSoll_HK_last',
	},
	draw		=> {
		dsname	=> 'T_ist_HK',
		name	=> 'TIst_HK',
		legend	=> 'T-Ist  (Regler/Wand)',
		color	=> '00ff00'
	},
	draw		=> {
		type	=> "hidden",
		name	=> "TIst_HK_last",
		vdef	=> "TIst_HK,LAST"
	},
	comment		=> '                          last\:',
	gprint		=> {
		format	=> '%2.1lf\l',
		draw	=> 'TIst_HK_last',
	},
####### activate this if you are using a remote-controller #######################
#	draw		=> {
#		dsname	=> 'T_steuer_FB',
#		name	=> 'Raumtemperatur',
#		legend	=> 'T-Raum (FB10) min\:',
#		thickness => 2,
#		color	=> '8080ff'
#	},
#	# vdef for calculating Maximum, Minimum of 'Raumtemperatur'
#	draw		=> {
#		type	=> "hidden",
#		name	=> "Raumtemperatur_min",
#	vdef	=> "Raumtemperatur,MINIMUM",
#	},
#	gprint		=> {
#		format	=> '%3.1lf',
#		draw	=> 'Raumtemperatur_min',
#	},
#	draw		=> {
#		type	=> "hidden",
#		name	=> "Raumtemperatur_max",
#		vdef	=> "Raumtemperatur,MAXIMUM",
#	},
#	comment		=> 'max\:',
#	gprint		=> {
#		format	=> '%3.1lf',
#		draw	=> 'Raumtemperatur_max',
#	},
#	draw		=> {
#		type	=> "hidden",
#		name	=> "Raumtemperatur_HK_last",
#		vdef	=> "Raumtemperatur,LAST"
#	},
#	comment		=> '   last\:',
#	gprint		=> {
#		format	=> '%2.1lf\l',
#		draw	=> 'Raumtemperatur_HK_last',
#	},
##############################
#Rev.:0.1.8 ######### 'Betriebsart' added
#Rev.:0.2   ######### 'Betriebsart' changed to 'TemperaturNiveau'
	draw		=> {
		dsname	=> 'V_tempera_niveau',
		name	=> 'TemperaturNiveau',
		legend	=> 'Temperatur Niveau (3=Heizen 2=Sparen 1=Frost)\l',
		thickness => 2,
		color	=> '808080'
	},
);

if ($myanzahlheizkreise>1) {
	$rc = $heizkreis2_rrdh->option_add("graph", "right_axis");
	$rc = $heizkreis2_rrdh->option_add("graph", "right_axis_label");
	$rc = $heizkreis2_rrdh->graph(
		image			=> $ImageHK2,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height			=> $myheight,
		title			=> 'Heizkreis 2'.$timestring,
		color			=> {back => '#ffeeaa',
							canvas => '#fff6d5',
		},
		draw		=> {
			dsname	=> 'T_soll_HK',
			name	=> 'TSoll_HK',
			legend	=> 'T-Soll (gewünscht)',
			color	=> 'ff0000'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_last",
			vdef	=> "TSoll_HK,LAST"
		},
		comment		=> '                            last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TSoll_HK_last',
		},
		draw		=> {
			dsname	=> 'T_ist_HK',
			name	=> 'TIst_HK',
			legend	=> 'T-Ist  (Regler/Wand)',
			color	=> '00ff00'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_last",
			vdef	=> "TIst_HK,LAST"
		},
		comment		=> '                          last\:',
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
#Rev.:0.1.8 ######### 'Betriebsart' added
#Rev.:0.2   ######### 'Betriebsart' changed to 'TemperaturNiveau'
		draw		=> {
			dsname	=> 'V_tempera_niveau',
			name	=> 'TemperaturNiveau',
			legend	=> 'Temperatur Niveau (3=Heizen 2=Sparen 1=Frost)\l',
			thickness => 2,
			color	=> '808080'
		},
	);
}

if ($myanzahlheizkreise>2) {
	$rc = $heizkreis3_rrdh->option_add("graph", "right_axis");
	$rc = $heizkreis3_rrdh->option_add("graph", "right_axis_label");
	$rc = $heizkreis3_rrdh->graph(
		image			=> $ImageHK3,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height			=> $myheight,
		title			=> 'Heizkreis 3'.$timestring,
		color			=> {back => '#ffeeaa',
							canvas => '#fff6d5',
		},
		draw		=> {
			dsname	=> 'T_soll_HK',
			name	=> "TSoll_HK",
			legend	=> 'T-Soll (gewünscht)',
			color	=> 'ff0000'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_last",
			vdef	=> "TSoll_HK,LAST"
		},
		comment		=> '                            last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TSoll_HK_last',
		},
		draw		=> {
			dsname	=> 'T_ist_HK',
			name	=> "TIst_HK",
			legend	=> 'T-Ist  (Regler/Wand)',
			color	=> '00ff00'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_last",
			vdef	=> "TIst_HK,LAST"
		},
		comment		=> '                          last\:',
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
#Rev.:0.1.8 ######### 'Betriebsart' added
#Rev.:0.2   ######### 'Betriebsart' changed to 'TemperaturNiveau'
		draw		=> {
			dsname	=> 'V_tempera_niveau',
			name	=> 'TemperaturNiveau',
			legend	=> 'Temperatur Niveau (3=Heizen 2=Sparen 1=Frost)\l',
			thickness => 2,
			color	=> '808080'
		},
	);
}

if ($myanzahlheizkreise>3) {
	$rc = $heizkreis4_rrdh->option_add("graph", "right_axis");
	$rc = $heizkreis4_rrdh->option_add("graph", "right_axis_label");
	$rc = $heizkreis4_rrdh->graph(
		image			=> $ImageHK4,
		vertical_label	=> 'Temperaturen (Celsius)',
		right_axis	=> '1:0',
		right_axis_label	=> 'Temperaturen (Celsius)',
		start			=> $start_time,
		end				=> $end_time,
		width			=> $mywidth,
		height			=> $myheight,
		title			=> 'Heizkreis 4'.$timestring,
		color			=> {back => '#ffeeaa',
							canvas => '#fff6d5',
		},
		draw		=> {
			dsname	=> 'T_soll_HK',
			name	=> "TSoll_HK",
			legend	=> 'T-Soll (gewünscht)',
			color	=> 'ff0000'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TSoll_HK_last",
			vdef	=> "TSoll_HK,LAST"
		},
		comment		=> '                            last\:',
		gprint		=> {
			format	=> '%2.1lf\l',
			draw	=> 'TSoll_HK_last',
		},
		draw		=> {
			dsname	=> 'T_ist_HK',
			name	=> "TIst_HK",
			legend	=> 'T-Ist  (Regler/Wand)',
			color	=> '00ff00'
		},
		draw		=> {
			type	=> "hidden",
			name	=> "TIst_HK_last",
			vdef	=> "TIst_HK,LAST"
		},
		comment		=> '                          last\:',
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
#Rev.:0.1.8 ######### 'Betriebsart' added
#Rev.:0.2   ######### 'Betriebsart' changed to 'TemperaturNiveau'
		draw		=> {
			dsname	=> 'V_tempera_niveau',
			name	=> 'TemperaturNiveau',
			legend	=> 'Temperatur Niveau (3=Heizen 2=Sparen 1=Frost)\l',
			thickness => 2,
			color	=> '808080'
		},
	);
}

$rc = $warmwasser_rrdh->option_add("graph", "right_axis");
$rc = $warmwasser_rrdh->option_add("graph", "right_axis_label");
$rc = $warmwasser_rrdh->graph(
	image			=> $ImageWW,
	vertical_label	=> 'Temperaturen (Celsius)',
	right_axis	=> '1:0',
	right_axis_label	=> 'Temperaturen (Celsius)',
	start			=> $start_time,
	end				=> $end_time,
	width			=> $mywidth,
	height			=> $myheight,
	title			=> 'Warmwasser'.$timestring,
	color			=> {back => '#aaccff',
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
);

$rc = $solar_rrdh->option_add("graph", "right_axis");
$rc = $solar_rrdh->option_add("graph", "right_axis_label");
$rc = $solar_rrdh->graph(
	image			=> $ImageSO,
	vertical_label	=> 'Temperaturen (Celsius)',
	right_axis	=> '1:0',
	right_axis_label	=> 'Temperaturen (Celsius)',
	start			=> $start_time,
	end				=> $end_time,
	width			=> $mywidth,
	height			=> $myheight,
	color			=> {	back => '#c6e9af',
			    			canvas => '#e3f4d7',
	},
	title	=> 'Solar'.$timestring,
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

$rc = $solar_rrdh->option_add("graph", "right_axis");
$rc = $solar_rrdh->option_add("graph", "right_axis_label");
$rc = $solar_rrdh->graph(
	image			=> $ImageSO_ertrag,
	vertical_label	=> '(k)Wh',
	right_axis	=> '1:0',
	right_axis_label	=> '(k)Wh',
	start			=> $start_time,
	end				=> $end_time,
	width			=> $mywidth,
	height			=> $myheight,
	color			=>	{	back => '#c6e9af',
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
		format	=> '  Laufzeit Pumpe    \:%5.1lf Stunden',
		draw	=> 'pumpenlauf_draw',
	},
	comment		=> ' \s',
	comment		=> ' \s',
	comment		=> ' \s',
	comment		=> ' \s',
	comment		=> ' \s',
	comment		=> ' \s',
	comment		=> ' \s',
);


