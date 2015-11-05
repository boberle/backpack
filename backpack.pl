#!/usr/bin/perl
use strict;
use warnings FATAL=>'all';

use POSIX qw(strftime);


########################################################################
# WHAT IS THAT?
#
# The basic script to make backups!

# VERSION: Fri Apr 24 22:10:09 CEST 2015
########################################################################



########################################################################
# Global variables
########################################################################

# list of backups available to the user; the format is
# BU_NAME => { source => SOURCE, target => TARGET }
my %DATA = ();

# just a shorthand to use only in the completion of the %DATA hash
my $LBACKUP = '/mnt/removable/lbackup';

# bruno's backup and restore

   $DATA{bruno} = { source => "/home/bruno",
                    target => "$LBACKUP",
                    bpd => 1,
                    is_restoration => '',
                    priority => 1 };

   $DATA{bruno_back} = { source => "$LBACKUP/bruno",
                         target => "/home",
                         bpd => 1,
                         is_restoration => 1,
                         priority => 2 };

   $DATA{general} =        { source => "/home/general",
                             target => "$LBACKUP",
                             bpd => 1,
                             is_restoration => '',
                             priority => 3 };

   $DATA{general_back} =        { source => "$LBACKUP/general",
                                  target => "/home",
                                  bpd => 1,
                                  is_restoration => 1,
                                  priority => 4 };

   # library

   $DATA{working_bib} = { source => "/home/library/01_WORKING",
                          target => "$LBACKUP/library",
                          bpd => '',
                          is_restoration => '',
                          priority => 5 };

   $DATA{working_bib_back} =  { source => "$LBACKUP/library/01_WORKING",
                                target => "/home/library",
                                bpd => '',
                                is_restoration => 1,
                                priority => 6 };

   $DATA{library} =       { source => "/home/library",
                            target => "$LBACKUP",
                            bpd => '',
                            is_restoration => '',
                            priority => 7 };

#   $DATA{library_back} =   { source => "$LBACKUP/library",
#                             target => "/home",
#                             bpd => '',
#                             is_restoration => 1,
#                             priority => 8 };

# storage backup

   #if (-f '/root/ldlc') {
      $DATA{storage} = { source => "/mnt/storage",
                         target => "$LBACKUP/more",
                         is_restoration => '',
                         bpd => '',
                         priority => 9 };
   #}


# test

   #$DATA{test} = { source => "/home/bruno/scripts/newbackpack/testing/source_test",
   #                target => "/home/bruno/scripts/newbackpack/testing/lbackup_test",
   #                is_restoration => '',
   #                bpd => '',
   #                priority => 100 };
   #$DATA{test_back} = { source => "/home/bruno/scripts/newbackpack/testing/lbackup_test/source_test",
   #                     target => "/home/bruno/scripts/newbackpack/testing",
   #                     is_restoration => 1,
   #                     bpd => '',
   #                     priority => 101 };

########################################################################
# Ask the user which backup to use.  Return the name of the backup
# (one of the keys of %DATA).
########################################################################

sub ask_which_backup {

   my $c = 1;
   my %choices = map{ $c++, $_ }
                 sort { $DATA{$a}->{priority} <=> $DATA{$b}->{priority} }
                 keys %DATA;

   print "List of backups/synchros:\n";
   for (sort { $a <=> $b } keys %choices) {
      printf " \033[%s;1m- %02d: %s (%s --> %s)\033[0m\n",
            $DATA{$choices{$_}}->{is_restoration} ? '31' : '32',
            $_, $choices{$_},
            $DATA{$choices{$_}}->{source},
            $DATA{$choices{$_}}->{target};
   }

   print "Your choice (one of the leading numbers): ";
   my $nb = <STDIN>; chomp $nb;

   die "$0: *** '$nb' is not valid ***\n" unless exists $choices{$nb};

   return $choices{$nb};

}


########################################################################
# Ask the user for confirmation.  Return TRUE if the user want to
# continue, FALSE otherwise.
########################################################################

sub ask_for_confirmation {

   LOOP: {
      print "Do you want to continue [y/n]? ";
      my $buf = <STDIN>;
      if ($buf =~ m/^\s*+y\s*+$/i) {
         print "Let's go!\n";
         return 1;
      } elsif ($buf =~ m/^\s*+n\s*+$/i) {
         print "Quit on user request.\n";
         return '';
      }
   }

}

########################################################################
# Ask the user for confirmation.  Return TRUE if the user want to
# continue, FALSE otherwise.
########################################################################

sub ask_for_confirmation_for_direction {

   my $is_restoration = shift;
   my $source = shift;
   my $target = shift;

   if ($is_restoration) {

      print <<"END";
\033[31;1mSOURCE: $source
                                             ._________________.
  .-----------------.                        | ._____________. |
  |  .-----------.  |                        | |root #       | |
  |[]|           |[]|             |\\         | |             | |
  |  |           |  |             | \\        | |             | |
  |  |           |  |     +-------+  \\       | |             | |
  |  `-----------'  |     |           \\      | !_____________! |
  |     _______ _   |     |           /      !_________________!
  |    |  _    | |  |     +-------+  /          ._[_______]_.
  |    | |_|   | |  |             | /       .___|___________|___
  \\____|_______|_|__|             |/        |::: ____           |
                                            |    ~~~~ [CD-ROM]  |
                                            !___________________!
TARGET: $target\033[0m
END

   LOOP: {
      print "This is a restoration! Type either 'restore to computer' or 'quit': ";
      my $buf = <STDIN>;
      if ($buf =~ m/^\s*+restore to computer\s*+$/i) {
         print "Let's go!\n";
         return 1;
      } elsif ($buf =~ m/^\s*+quit\s*+$/i) {
         print "Quit on user request.\n";
         return '';
      }
   }

   } else {

      print <<"END";
\033[32;1mSOURCE: $source
   ._________________.                        
   | ._____________. |                        .-----------------.
   | |root #       | |                        |  .-----------.  |
   | |             | |              |\\        |[]|           |[]|
   | |             | |              | \\       |  |           |  |
   | |             | |      +-------+  \\      |  |           |  |
   | !_____________! |      |           \\     |  `-----------'  |
   !_________________!      |           /     |     _______ _   |
      ._[_______]_.         +-------+  /      |    |  _    | |  |
  .___|___________|___              | /       |    | |_|   | |  |
  |::: ____           |             |/        \\____|_______|_|__|
  |    ~~~~ [CD-ROM]  |                       
  !___________________!                       
TARGET: $target\033[0m
END

      LOOP: {
         print "This is a backup. Do you want to continue [y/n]? ";
         my $buf = <STDIN>;
         if ($buf =~ m/^\s*+y\s*+$/i) {
            print "Let's go!\n";
            return 1;
         } elsif ($buf =~ m/^\s*+n\s*+$/i) {
            print "Quit on user request.\n";
            return '';
         }
      }

   }

}


########################################################################
# Get rsync() options.
########################################################################

sub get_rsync_options {

   my $source = shift;
   my $target = shift;
   my $need_bpd = shift;

   my @rsync_opts = (
      "--modify-window", "1", # loose comparision of timestamp
      "--recursive", # descend into directories
      "--times", # update timestamps
      "--perms", # update permissions
      "--owner", # update owner (only if rsync is run as superuser)
      "--group", # update group (idem)
      "--links", # copy symlinks as symlinks
      "--devices", # recreate character and block device files (only if run as superuser)
      "--specials", # recreate special files (socket, fifos (only if run as superuser)
      "--delete", # delete extraneous files from dest dirs (otherwise, these are kept)
      "--human-readable", # output numbers in a human-readable format
      "-v", "-v", # verbose, and more verbose
      "--progress", # show progress during transfer
      "--log-file", "backup.log", # save a log file
   );

   if ($need_bpd) {
      my $timestamp = strftime("%Y%m%d_%H%M%S", gmtime);
      my $bpd_dir = "/home/nobackup/BPD/$timestamp/";
      die "$0: *** BPD dir '$bpd_dir' already exists ***\n" if -e $bpd_dir;
      push @rsync_opts, '--backup', '--backup-dir', $bpd_dir;
   }

   (my $dir_with_no_parents = $source) =~ s{^([^/]*+/)*+}{};
   push @rsync_opts, '--exclude', "/$dir_with_no_parents/.*";

   push @rsync_opts, $source, $target;

   return @rsync_opts;

}


########################################################################
# main()
########################################################################

sub main {

   # only root can do that!

   die "$0: *** you must be root ***\n"
      unless $ENV{LOGNAME} eq 'root' or exists $DATA{test};

   # ask the backup to be used

   my $backup_name = ask_which_backup();

   my $source = $DATA{$backup_name}->{source};
   my $target = $DATA{$backup_name}->{target};

   die "$0: *** source '$source' doesn't exist ***\n" unless -d-r-w-x $source;
   die "$0: *** target '$target' doesn't exist ***\n" unless -d-r-w-x $target;

   # ask confirmation for restoration

   if (exists $DATA{$backup_name}->{is_restoration}) {
      return unless ask_for_confirmation_for_direction(
         $DATA{$backup_name}->{is_restoration},
         $source, $target);
   } else {
      die "$0: *** no 'is_restoration' key in the DB ***\n";
   }

   # build the command

   my @rsync_opts = get_rsync_options(
      $source, $target, $DATA{$backup_name}->{bpd});

   # print summary

   print '-'x80, "\n";
   print 
      "Summary (check SOURCE, TARGET and BPD):\n"
      ."   Source:  $source\n"
      ."   Target:  $target\n"
      ."   Command: rsync @rsync_opts\n"
      ."   Note: No $source/.* files or dirs will be saved!\n";
   print '-'x80, "\n";

   # ask confirmation

   return unless ask_for_confirmation();

   # run the command

   print "Running the command...\n";

   system('rsync', @rsync_opts)
      and die "$0: *** error when running rsync ***\n$!"

}

main();
print "done!\n";
