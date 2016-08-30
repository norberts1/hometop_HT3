#!/usr/bin/perl -w

# Script to add a DS to an rrd
# Use at own risk

use strict;
use Getopt::Long qw(GetOptions);
use RRD::Simple;

if (@ARGV<1) {die("Need to supply at least the upgrade_file as argument\n");}
my $upgrade_file = shift @ARGV;
my $dbfolder = shift @ARGV;

if (defined($dbfolder) == 0) {
    $dbfolder = './HT3/sw/var/databases/';
}

my (@rrddb_filepathname, @logitem_name, @datatype, @datause, @max, @default);

open(FILE, $upgrade_file) || die "can't open file:<$upgrade_file>";
my @filecontent = <FILE>;
chomp(@filecontent);
close(FILE);

my $linecounter = 1;
foreach my $content (@filecontent) {
    my ($systempart, $logitem_name, $datatype, $datause, $max, $default);
    my $filepathname = "";
    ($systempart, $logitem_name, $datatype, $datause, $max, $default) = split(';',$content);
    if ($linecounter > 1) {
        $filepathname = $dbfolder.'HT3_db_rrd_'.$systempart.'.rrd';
        push @rrddb_filepathname, $filepathname;
        push @logitem_name , $logitem_name;
        push @datatype, $datatype;
        push @datause, $datause;
        push @max, $max;
        push @default,$default;
    }
    $linecounter = $linecounter + 1;
    ## print("$content\n");
};

my $rrd = RRD::Simple->new();
my $rc = 0;

sub IsSourceInDatabase($$) {
    my ($rrdfile, $logitem_name) = @_;
    my @sources = $rrd->sources($rrdfile);
    my $rtn = 0;
    foreach my $source (@sources) {
        # print("src:$source\n");
        if ($source =~ m/$logitem_name/) {
            $rtn = 1;
            # print("------ match found for logitem:$logitem_name -------------\n");
            last;
        }
    };
    return $rtn;
}

sub AddSource2Database($$$) {
    my ($rrdfile, $logitem_name, $datatype) = @_;
    print("Adding logitem:<$logitem_name> to file:<$rrdfile>\n");
    print(" Please wait, don't stop this procedure!\n");
    my $rc = $rrd->add_source($rrdfile, $logitem_name => $datatype);
    print(" Done\n");
    return $rc;
}

$linecounter = 0;
my $addcounter = 0;
foreach my $rrdfile (@rrddb_filepathname) {
    if (IsSourceInDatabase($rrdfile, $logitem_name[$linecounter])) {
        print("logitem:<$logitem_name[$linecounter]> is already in file:<$rrdfile>\n");
        # nothing to do
    } else {
        AddSource2Database($rrdfile, $logitem_name[$linecounter], $datause[$linecounter]);
        $addcounter = $addcounter + 1;
    }
    $linecounter = $linecounter + 1;
}

if ($addcounter == 0) {
    print("upgrade is already done.\n");
} else {
    print("upgrade done; $addcounter logitem(s) are writen.\n");
}

exit 0;

