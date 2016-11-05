#!/usr/bin/perl
use strict;
use warnings FATAL=>'all';

use POSIX qw(strftime);
use Sys::Hostname;


########################################################################
# WHAT IS THAT?
#
# The basic script to synchronize data and make backup!

# VERSION: Sun Jan 10 16:21:32 CET 2016
########################################################################



########################################################################
# Global variables
########################################################################

# BPD dir
my $BPD_DIR = '/home/nobackup/BPD';

# just a shorthand to use only in the completion of @CHOICES
my $REMOTE_DIR = '/mnt/removable/backpack';
# log file
my $LOG_FILE = "$REMOTE_DIR/LOG";

# list of choices available to the user; the format is
# [ { name => NAME_TO_BE_SHOWN,
#     source => SOURCE_DIR,
#     target => TARGET_DIR,
#     local_to_remote => BOOLEAN,
#     bpd => BOOLEAN }, # if this is false or if the key doesn't
#                       # exist, the script asks the user
#   { ... },
#   ...
# ]
my @CHOICES = (

   { name => "bruno",
     source => "/home/bruno",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => 1 },

   { name => "bruno",
     source => "$REMOTE_DIR/bruno",
     target => "/home",
     local_to_remote => '',
     bpd => 1 },


   { name => "storeroom",
     source => "/home/storeroom",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => 1 },

   { name => "storeroom",
     source => "$REMOTE_DIR/storeroom",
     target => "/home",
     local_to_remote => '',
     bpd => 1 },


   { name => "TODO",
     source => "/home/TODO",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => 1 },

   { name => "TODO",
     source => "$REMOTE_DIR/TODO",
     target => "/home",
     local_to_remote => '',
     bpd => 1 },


   { name => "papps",
     source => "/home/papps",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "papps",
     source => "$REMOTE_DIR/papps",
     target => "/home",
     local_to_remote => '',
     bpd => '' },


   { name => "blib",
     source => "/home/blib",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "blib",
     source => "$REMOTE_DIR/blib",
     target => "/home",
     local_to_remote => '',
     bpd => '' },


   { name => "pendingblib",
     source => "/home/pendingblib",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "pendingblib",
     source => "$REMOTE_DIR/pendingblib",
     target => "/home",
     local_to_remote => '',
     bpd => '' },


   { name => "playground",
     source => "/home/playground",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "playground",
     source => "$REMOTE_DIR/playground",
     target => "/home",
     local_to_remote => '',
     bpd => '' },


   { name => "STORAGE: big 01 important",
     source => "/media/bruno/storage/big_01_important",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "STORAGE: big 01 important",
     source => "$REMOTE_DIR/big_01_important",
     target => "/media/bruno/storage",
     local_to_remote => '',
     bpd => '' },

   { name => "STORAGE: big 02 useful",
     source => "/media/bruno/storage/big_02_useful",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "STORAGE: big 02 useful",
     source => "$REMOTE_DIR/big_02_useful",
     target => "/media/bruno/storage",
     local_to_remote => '',
     bpd => '' },

   { name => "STORAGE: big 03 less useful",
     source => "/media/bruno/storage/big_03_less_useful",
     target => $REMOTE_DIR,
     local_to_remote => 1,
     bpd => '' },

   { name => "STORAGE: big 03 less useful",
     source => "$REMOTE_DIR/big_03_less_useful",
     target => "/media/bruno/storage",
     local_to_remote => '',
     bpd => '' },


   { name => "TEST",
     source => "/home/bruno/scripts/newbackpack/testing/test_local",
     target => "/home/bruno/scripts/newbackpack/testing/test_remote",
     local_to_remote => 1,
     bpd => 1 },

   { name => "TEST",
     source => "/home/bruno/scripts/newbackpack/testing/test_remote",
     target => "/home/bruno/scripts/newbackpack/testing/test_local",
     local_to_remote => '' },

);


my $ASCII_ART_TO_LOCAL =<<"END";
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
END

my $ASCII_ART_TO_REMOTE = <<"END";
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
END


########################################################################
# Ask the input data to the user (source and target directories, BPD).
# Return an array: (SOURCE, TARGET, BPD).
#
# Check that the source and target exist.  Ask confirmation.
#
# Return FALSE if the user wants to quit.
########################################################################

sub ask_data_to_user {

   my @choices = @_;

   my $buf;

   # choice of direction

   my $to_remote;
   while (1) {
      print "Choose the direction:\n"
         ."- 0: to remote directory (backup)\n"
         ."- 1: to local directory (restoration)\n"
         ."Choice [0/1/quit]? ";
      $buf = <STDIN>;
      if ($buf =~ m/^\s*+0\s*+$/) {
         print "Choice made: to remote directory.\n";
         $to_remote = 1;
         last;
      } elsif ($buf =~ m/^\s*+1\s*+$/) {
         print "Choice made: to local directory.\n";
         $to_remote = "";
         last;
      } elsif ($buf =~ m/^\s*+quit\s*+$/i) {
         print "Aborted on user request.\n";
         return undef;
      }
      print "Invalid answer.  Try again.\n";
   }

   # choice of source and target dirs

   @choices =
      map { -e $_->{source} ? $_ : () }
      map { (($_->{local_to_remote} and $to_remote)
         or (!$_->{local_to_remote} and !$to_remote)) ? $_ : () } @choices;

   die "$0: *** no source directory available ***\n" unless @choices;

   my $source;
   my $target;
   my $bpd;
   while (1) {
      my $i = 0;
      print "Choose the directory:\n";
      for (@choices) {
         print " - $i: $_->{name}\n";
         $i++;
      }
      print "Choice (one of the leading number, or 'quit')? ";
      $buf = <STDIN>;
      if ($buf =~ m/^\s*+(\d++)\s*+$/ and $1 >= 0 and $1 < scalar @choices) {
         $source = $choices[$1]->{source};
         $target = $choices[$1]->{target};
         if (exists $choices[$1]->{bpd}) {
            $bpd = $choices[$1]->{bpd};
         } else {
            $bpd = '';
         }
         last;
      } elsif ($buf =~ m/^\s*+quit\s*+$/i) {
         print "Aborted on user request.\n";
         return undef;
      }
      print "Invalid answer.  Try again.\n";
   }

   die "$0: *** source directory '$source' doesn't exist ***\n"
      unless -d-r-w-x $source;

   die "$0: *** target directory '$target' doesn't exist ***\n"
      unless -d-r-w-x $target;

   # ask confirmation

   while (1) {
      my $color = $to_remote ? '32' : '31';
      print "Choice made:\n"
         ."\033[$color;1mSource:\n$source\n"
         .($to_remote ? $ASCII_ART_TO_REMOTE : $ASCII_ART_TO_LOCAL)
         .sprintf("% 65s\n", "Target:")
         .sprintf("% 65s\033[0m\n", $target);
      if ($to_remote) {
         print "Is this correct [y/n]? ";
      } else {
         print "Type 'erase local data' to continue (or 'quit'): ";
      }
      $buf = <STDIN>;
      if ($to_remote and $buf =~ m/^\s*+y\s*+$/) {
         last;
      } elsif ($to_remote and $buf =~ m/^\s*+n\s*+$/i) {
         print "Aborted on user request.\n";
         return undef;
      } elsif (!$to_remote and $buf =~ m/^\s*+quit\s*+$/i) {
         print "Aborted on user request.\n";
         return undef;
      } elsif (!$to_remote and $buf =~ m/^\s*+erase\s++local\s++data\s*+$/i) {
         last;
      }
      print "Invalid answer.  Try again.\n";
   }

   # ask for BPD

   unless ($bpd) {
      while (1) {
         print "Do you want to use BPD [y/n/quit]? ";
         $buf = <STDIN>;
         if ($buf =~ m/^\s*+y\s*+$/) {
            print "Choice made: use BPD.\n";
            $bpd = 1;
            last;
         } elsif ($buf =~ m/^\s*+n\s*+$/) {
            print "Choice made: no BPD.\n";
            $bpd = '';
            last;
         } elsif ($buf =~ m/^\s*+quit\s*+$/i) {
            print "Aborted on user request.\n";
            return undef;
         }
         print "Invalid answer.  Try again.\n";
      } # while
   } # unless

   return ($source, $target, $bpd);

}


########################################################################
# Build the rsync options.  Return an array with all the options, to
# be used with the system() command.
########################################################################

sub build_rsync_options {

   my $source = shift;
   my $target = shift;
   my $bpd = shift;
   my $timestamp = shift;

   my @rsync_options = (
      "--modify-window", "1", # loose comparision of timestamp
      "--recursive", # descend into directories
      "--times", # update timestamps
      "--perms", # update permissions
      "--owner", # update owner (only if rsync is run as superuser)
      "--group", # update group (idem)
      "--links", # copy symlinks as symlinks
      "--devices", # recreate character and block device files (only if run as superuser)
      "--specials", # recreate special files (socket, fifos (only if run as superuser))
      "--delete", # delete extraneous files from dest dirs (otherwise, these are kept)
      "--human-readable", # output numbers in a human-readable format
      "-v", "-v", # verbose, and more verbose
      "--progress", # show progress during transfer
      "--log-file", "backup.log", # save a log file
   );

   if ($bpd) {
      die "$0: *** BPD directory '$BPD_DIR' doesn't exist ***\n"
         unless -d-r-w-x $BPD_DIR;
      my $bpd_dir = sprintf('/home/nobackup/BPD/%s/', $timestamp);
      die "$0: *** BPD directory '$bpd_dir' already exists ***\n"
         if -e $bpd_dir;
      push @rsync_options, '--backup', '--backup-dir', $bpd_dir;
   }

   # dirname = dir name without the parent dirs
   (my $dirname = $source) =~ s{^([^/]*+/)*+}{};
   push @rsync_options, '--exclude', "/$dirname/.*";

   push @rsync_options, $source, $target;

   return @rsync_options;

}


########################################################################
# print log
########################################################################

sub write_log {

   my $file = shift;
   my $timestamp = shift; # if undef, just write 'ok'
   my $source = shift;
   my $target = shift;
   my $msg = shift;
   my @options = @_;

   open my $fh, ">>", $file or die "$0: *** can't open $file ***\n";

   if ($timestamp) {
      #print "time: $timestamp\n";
      #print "msg: $msg\n";
      #print "src: $source\n";
      #print "targ: $target\n";
      #print "opt: @options\n";
      my $host = hostname();
      print $fh "$timestamp ($host, $msg): $source --> $target (@options)\n";
   } else {
      print $fh "... ok\n";
   }

   close $fh or die "$0: *** can't close $file ***\n";

}



########################################################################
# main()
########################################################################

sub main {

   # only root can do that!
   my @choices;
   if ($ENV{LOGNAME} eq 'root') {
      @choices = map { $_->{name} !~ m/^TEST\b/ ? $_ : () } @CHOICES;
   } else {
      @choices = map { $_->{name} =~ m/^TEST\b/ ? $_ : () } @CHOICES;
   }

   # get the data
   my ($source, $target, $bpd) = ask_data_to_user(@choices);
   return unless $source and $target;

   my $timestamp = strftime("%Y%m%d_%H%M%S", gmtime);

   # build the command
   my @rsync_options = build_rsync_options($source, $target, $bpd, $timestamp);
   return unless @rsync_options;

   # print summary

   while (1) {
      print '-'x80, "\n";
      print 
         "Summary (check SOURCE, TARGET and BPD):\n"
         ."   \033[1;37mSource:\033[0m  $source\n"
         ."   \033[1;37mTarget:\033[0m  $target\n"
         ."   \033[1;37mUse BPD:\033[0m ".($bpd ? 'yes' : 'no')."\n"
         ."   \033[1;37mCommand:\033[0m rsync @rsync_options\n"
         ."   \033[1;37mNote:\033[0m No $source/.* files or dirs will be saved!\n";
      print '-'x80, "\n";
      print "Do you want to continue (last chance to stop) [y/n]? ";
      my $buf = <STDIN>;
      if ($buf =~ m/^\s*+y\s*+$/) {
         print "Ready to go.\n";
         last;
      } elsif ($buf =~ m/^\s*+n\s*+$/) {
         print "Aborted on user request.\n";
         return;
      }
      print "Invalid answer.  Try again.\n";
   }

   print "Enter some message for the log (home, library...): ";
   my $msg = <STDIN>;
   chomp $msg;
   write_log($LOG_FILE, $timestamp, $source, $target, $msg, @rsync_options);

   # run the command
   print "Running the command...\n";
   system('rsync', @rsync_options)
      and die "$0: *** error when running rsync ***\n$!";

   write_log($LOG_FILE);

}

main();
print "done!\n";
