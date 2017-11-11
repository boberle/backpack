import sys, os, time, socket, subprocess, collections, parse_rsync_log

## parameters ##########################################################

Data = collections.namedtuple("Data", "local_path force_bpd")

TEST_MODE = False

if TEST_MODE:
    REMOTE_DIR = '/tmp/backpack/remote'
    BPD_DIR = '/tmp/backpack/BPD';
    DATA = [
        Data('/tmp/backpack/local/somedir', True),
        Data('/tmp/backpack/local/someotherdir', False)
    ]

else:
    REMOTE_DIR = '/mnt/removable/backpack'
    BPD_DIR = '/home/nobackup/BPD';
    DATA = [
        Data('/home/bruno', True),
        Data('/home/storeroom', True),
        Data('/home/blib', True),
        Data('/home/pendingblib', True),
        Data('/home/papps', False),
        Data('/home/playground', False),
        Data('/home/TODO', False),
        Data('/media/bruno/storage/big_01_important', False),
        Data('/media/bruno/storage/big_02_useful', False),
        Data('/media/bruno/storage/big_03_less_useful', False),
    ]


########################################################################
#                  NO MODIFICATION REQUIRED BELOW THIS LINE
########################################################################

## constants ###########################################################

TO_REMOTE = 1
TO_LOCAL = 2

ASCII_TO_LOCAL = r"""
                                             ._________________.
  .-----------------.                        | ._____________. |
  |  .-----------.  |                        | |root #       | |
  |[]|           |[]|             |\         | |             | |
  |  |           |  |             | \        | |             | |
  |  |           |  |     +-------+  \       | |             | |
  |  `-----------'  |     |           \      | !_____________! |
  |     _______ _   |     |           /      !_________________!
  |    |  _    | |  |     +-------+  /          ._[_______]_.
  |    | |_|   | |  |             | /       .___|___________|___
  \____|_______|_|__|             |/        |::: ____           |
                                            |    ~~~~ [CD-ROM]  |
                                            !___________________!
"""

ASCII_TO_REMOTE = r"""
   ._________________.                        
   | ._____________. |                        .-----------------.
   | |root #       | |                        |  .-----------.  |
   | |             | |              |\        |[]|           |[]|
   | |             | |              | \       |  |           |  |
   | |             | |      +-------+  \      |  |           |  |
   | !_____________! |      |           \     |  `-----------'  |
   !_________________!      |           /     |     _______ _   |
      ._[_______]_.         +-------+  /      |    |  _    | |  |
  .___|___________|___              | /       |    | |_|   | |  |
  |::: ____           |             |/        \____|_______|_|__|
  |    ~~~~ [CD-ROM]  |                       
  !___________________!                       
"""

## common functions ####################################################

def print_in_red(msg):
    print("\033[31;1m%s\033[0m" % msg)

def print_in_yellow(msg):
    print("\033[33;1m%s\033[0m" % msg)

def ask_for_direction():
    while True:
        buf = input("Choose direction [l = to local, r = to remote, quit]: ")
        buf = buf.strip().lower()
        if buf == 'l':
            while True:
                print("\033[1;31m"+ASCII_TO_LOCAL+"\033[0m")
                buf = input("Type `erase local data' to confirm (or quit): ")
                buf = buf.strip().lower()
                if buf == 'erase local data':
                    return TO_LOCAL
                elif buf == 'quit':
                    raise QuitException
                print("Invalid answer.  Try again.")
        elif buf == 'r':
            while True:
                print("\033[1;32m"+ASCII_TO_REMOTE+"\033[0m")
                buf = input("Is this correct [y/n]? ")
                buf = buf.strip().lower()
                if buf == 'y':
                    return TO_REMOTE
                elif buf == 'quit' or buf == 'n':
                    raise QuitException
                print("Invalid answer.  Try again.")
        elif buf == 'quit':
            raise QuitException
        print("Invalid answer.  Try again.")

def get_bpd_dir(bpd_base_dir, timestamp):
    if not os.path.exists(bpd_base_dir):
        raise FileNotFoundError("%s not found" % bpd_base_dir)
    if not os.path.isdir(bpd_base_dir):
        raise FileNotFoundError("%s not a directory" % bpd_base_dir)
    path = os.path.join(bpd_base_dir, timestamp)
    if os.path.exists(path):
        raise FileExistsError("%s exists" % path)
    return path

def confirm(msg, default=None):
    while True:
        buf = input(msg).strip()
        if buf == 'y':
            return True;
        elif buf == 'n':
            return False
        elif buf == '' and default != None:
            return default
        else:
            print("Invalid answer.  Please try again.")

def ask_location():
    while True:
        buf = input("Enter your location: ")
        buf = buf.strip()
        if buf:
            return buf
        print("Invalid answer.  Try again.")

## exceptions ##########################################################

class QuitException(Exception):
    pass

class FileExistsError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

########################################################################

class SynchroItem():

    def __init__(self, name, local_dir, remote_dir, direction, force_bpd,
            log_file, bpd_dir):
        assert direction in (TO_LOCAL, TO_REMOTE)
        self.source_dir = os.path.join(local_dir if direction == TO_REMOTE
            else remote_dir, name)
        self.dest_dir = local_dir if direction == TO_LOCAL else remote_dir
        self.direction = direction
        self.remote_dir = remote_dir
        self.force_bpd = force_bpd
        self.log_file = log_file
        self.bpd_dir = bpd_dir
        self._use_bpd = False
        self._ok_to_synchronize = False
        self._parse_rsync_log = False
        self._ask()
        self._rsync_launcher = None
        if self.ok_to_synchronize:
            self._rsync_launcher = RsyncLauncher(source_dir=self.source_dir,
                dest_dir=self.dest_dir,
                log_file=self.log_file,
                bpd_dir=self.bpd_dir if self._use_bpd else None,
                parse_log=self._parse_rsync_log,
                remote_dir=self.remote_dir,
                direction=self.direction)

    @property
    def ok_to_synchronize(self):
        return self._ok_to_synchronize

    @property
    def use_bpd(self):
        return self._use_bpd

    @property
    def parse_rsync_log(self):
        return self._parse_rsync_log

    @property
    def rsync_launcher(self):
        return self._rsync_launcher

    def __str__(self):
        return "%s -> %s" % (self.source_dir, self.dest_dir)

    def _ask(self):
        # warning
        if not os.path.exists(self.source_dir):
            print_in_red("The source dir `%s' " "doesn't exist. Skipping."
                % self.source_dir)
            input("Press Enter to continue...")
            return
        target_dir = os.path.join(self.dest_dir,
            os.path.basename(self.source_dir))
        if not os.path.exists(target_dir):
            print_in_red("Warning: The target directory `%s' doesn't exist."
                % target_dir)
        # ask
        if not confirm("Synchronize `\033[1m%s\033[0m' [Y/n]? " %
                self.source_dir, True):
            print("Skipping `%s'." % self.source_dir)
            return
        self._ok_to_synchronize = True
        # use bpd?
        if self.force_bpd:
            self._use_bpd = True
        elif confirm("Use BPD [y/N]? ", False):
            self._use_bpd = True
        else:
            self._use_bpd = False
        # create md5?
        if confirm("Create md5 sums from log file [Y/n]?", True):
            self._parse_rsync_log = True

    def write_log(self, path, location, success=False):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        if success:
            state = "success"
        else:
            state = "not yet executed"
        open(path, 'a').write("%s @ %s: %s -> %s (%s)\n" % \
            (timestamp, location, self.source_dir, self.dest_dir, state))

########################################################################

class RsyncLauncher():

    default_args = (
        "rsync",
        # "--modify-window", "1", # loose comparison of timestamp
        "--recursive", # descend into directories
        "--times", # update timestamps
        "--perms", # update permissions
        "--owner", # update owner (only if rsync is run as superuser)
        "--group", # update group (idem)
        "--links", # copy symlinks as symlinks
        "--devices", # recreate character and block device files (only if run
                     # as superuser)
        "--specials", # recreate special files (socket, fifos (only if run as
                      #superuser))
        "--delete", # delete extraneous files from dest dirs (otherwise, these
                    # are kept)
        "--human-readable", # output numbers in a human-readable format
        #"-v", # verbose
        #"-v", # and more verbose
        "--progress", # show progress during transfer
    )

    def __init__(self, source_dir, dest_dir, log_file, bpd_dir=None,
            parse_log=False, remote_dir=None, direction=0):
        self.args = list(RsyncLauncher.default_args)
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.log_file = log_file
        self.bpd_dir = bpd_dir
        self.parse_log = parse_log
        self.remote_dir=remote_dir
        self.md5_file_written_to = False
        self.direction = direction
        if self.parse_log:
            assert self.remote_dir
            assert direction in (TO_LOCAL, TO_REMOTE)
        # more arguments for rsync
        self.args.extend(('--exclude', '/%s/.*' %
            os.path.basename(self.source_dir)))
        assert self.log_file
        self.args.extend(("--log-file", self.log_file))
        if self.bpd_dir:
            self.args.extend(('--backup', '--backup-dir', self.bpd_dir))
        self.args.append(self.source_dir)
        self.args.append(self.dest_dir)

    def run(self):
        subprocess.run(self.args, check=True)
        if self.parse_log:
            if self.direction == TO_REMOTE:
                log_dir = os.path.join(self.remote_dir, 'logs')
            else:
                log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)
            elif not os.path.isdir(log_dir):
                raise RuntimeError("`%s' is not a directory" % log_dir)
            output_file = os.path.join(log_dir, os.path.basename(self.log_file))
            output_file += ".md5"
            ans = parse_rsync_log.run(log_file=self.log_file,
                source_dir=os.path.dirname(self.source_dir),
                dest_dir=self.dest_dir,
                output_file=output_file)
            if ans:
                self.md5_file_written_to = output_file

    def __str__(self):
        return ' '.join(self.args)


########################################################################

if __name__ == '__main__':

    if not (TEST_MODE or os.getenv('LOGNAME', '') == 'root'):
        raise RuntimeError("you're not testing and you're not root!")
    if not os.path.exists(REMOTE_DIR):
        raise FileNotFoundError(REMOTE_DIR)

    # variables
    try:
        direction = ask_for_direction()
    except QuitException:
        print("Aborted on user request.")
        sys.exit(0)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    bpd_dir = get_bpd_dir(BPD_DIR, timestamp)
    rsync_log_dir = 'logs'
    if not os.path.exists(rsync_log_dir):
        os.mkdir(rsync_log_dir)
    elif not os.path.isdir(rsync_log_dir):
        raise RuntimeError("`%s' is not a directory" % rsync_log_dir)
    rsync_log_file = os.path.join(rsync_log_dir, "backup_%s_%%s.log" %
        timestamp)
    backpack_log_file = os.path.join(REMOTE_DIR, 'LOG')
    hostname = socket.gethostname()
    if not hostname:
        raise RuntimeError("no hostname found")
    location = ask_location()
    location = "%s (%s)" % (hostname, location)

    items = []
    log_count = 0
    for data in DATA:
        items.append(SynchroItem(
            name=os.path.basename(data.local_path),
            local_dir=os.path.dirname(data.local_path),
            remote_dir=REMOTE_DIR,
            direction=direction,
            force_bpd=data.force_bpd,
            log_file=rsync_log_file % chr(log_count+97),
            bpd_dir=bpd_dir))
        log_count += 1

    count = 0
    for item in items:
        if item.ok_to_synchronize:
            count += 1

    # confirmation
    if not count:
        print("Nothing to synchronize!")
        sys.exit(0)
    print('='*72)
    print("I will run the following commands:")
    for item in items:
        if item.ok_to_synchronize:
            print("\033[1m%s:\033[0m" % item.source_dir)
            print(str(item.rsync_launcher))
    print("Summary:")
    bpd_yes = "\033[1;32mBPD\033[0m"
    bpd_no = "\033[1;31mBPD\033[0m"
    md5_yes = "\033[1;32mmd5\033[0m"
    md5_no = "\033[1;31mmd5\033[0m"
    for item in items:
        if item.ok_to_synchronize:
            print("- \033[1m%s -> %s \033[0m (%s, %s)" % (
                item.source_dir,
                item.dest_dir,
                bpd_yes if item.use_bpd else bpd_no,
                md5_yes if item.parse_rsync_log else md5_no))
        else:
            print("- \033[1;31m%s\033[0m (not synchronized)" % (item.source_dir))
    while True:
        buf = input("Are you ok (type `ok' or `q[uit]')? ")
        buf = buf.lower().strip()
        if buf == "ok":
            break
        elif buf in ("q", "quit"):
            print("You're not ok. Nothing done!")
            sys.exit(0)
        print("I don't understand. Try again.")

    for item in items:
        if item.ok_to_synchronize:
            print("\033[1m" + "="*72 + "\033[0m")
            item.write_log(backpack_log_file, location, False)
            print("Running: " + str(item.rsync_launcher))
            item.rsync_launcher.run() 
            item.write_log(backpack_log_file, location, True)

    print("List of md5 files:")
    for item in items:
        if item.ok_to_synchronize and item.rsync_launcher.md5_file_written_to:
            print("- %s" % item.rsync_launcher.md5_file_written_to)

    print('done!')

