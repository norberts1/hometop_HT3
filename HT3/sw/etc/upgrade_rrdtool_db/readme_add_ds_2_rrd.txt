Procedure to upgrade the current available rrdtool-database.

Precondition:
    Perl CPAN - Modul: 'RRD::Simple' has to be installed

    1.1 Download file: 'http://search.cpan.org/CPAN/authors/id/N/NI/NICOLAW/RRD-Simple-1.44.tar.gz'

    1.2 untar file:
        tar xzvf RRD-Simple-1.44.tar.gz

    1.3 install addons
        perl Build installdeps

    1.4 Make and install RRD-Simple
        cd RRD-Simple-1.44/
        perl Makefile.PL
        make
        sudo make install

Upgrade-procedure:
    2.1 Stop at first the currently running data-logger:
        sudo /etc/init.d/ht3_logger stop

    2.2 running upgrade-tool using upgrade-file:
        add_ds_2_rrd.pl upgrade_rrddb_to_0_2.csv

    remark:
        This procedure takes a lot of time, please wait for termination.

Postconditions:
    3.1 Install / Update the HT-application to the latest release.

    3.2 Start again the data-logger:
        sudo /etc/init.d/ht3_logger start
