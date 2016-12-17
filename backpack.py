import sys, os, time, calendar, socket, subprocess, re


# OPTIONS
TEST_MODE = False
if TEST_MODE:
    REMOTE_BASE_DIR = '/home/bruno/scripts/newbackpack/testing/removable'
    BPD_BASE_DIR = '/tmp/BPD';
else:
    REMOTE_BASE_DIR = '/mnt/removable/backpack'
    BPD_BASE_DIR = '/home/nobackup/BPD';

# CONSTANTS
TO_REMOTE = 1
TO_LOCAL = 0

ASCII_TO_LOCAL = """
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
"""

ASCII_TO_REMOTE = """
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
"""


########################################################################

class QuitException(Exception):
    pass

class FileExistsError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

########################################################################

class BackupItem():
    direction = None
    remote_base_dir = None
    def __init__(self, local_dir, advise_bpd, name=None):
        super().__init__()
        assert self.direction != None
        assert self.remote_base_dir
        if name:
            self.name = name
        else:
            self.name = os.path.basename(local_dir)
        self.local_dir = local_dir
        self.basename = os.path.basename(self.local_dir)
        self.advise_bpd = advise_bpd
        self._ready_for_sync = None
        self._use_bpd = None
    @property
    def source(self):
        assert direction == TO_LOCAL or direction == TO_REMOTE
        if direction == TO_LOCAL:
            return os.path.join(self.remote_base_dir, self.basename)
        else:
            return self.local_dir
    @property
    def target(self):
        assert direction == TO_LOCAL or direction == TO_REMOTE
        if direction == TO_LOCAL:
            return os.path.dirname(self.local_dir)
        else:
            return self.remote_base_dir
    @property
    def use_bpd(self):
        assert self._use_bpd != None
        return self._use_bpd
    @property
    def ready_for_sync(self):
        assert self._ready_for_sync != None
        return self._ready_for_sync
    @property
    def source_exists(self):
        return os.path.exists(self.source)
    def __str__(self):
        return "%s: %s -> %s" % (self.name, self.source,
            self.target)
    def _remove_hidden(self, items):
        l = len(items)
        i = 0
        while i < l:
            if (items[i].startswith('.')):
                del items[i]
                l -= 1
            else:
                i += 1
    def has_changed(self, reftime):
        print("Walking through `%s' to find a change..." % self.source)
        is_toplevel = True
        for root, dirs, files in os.walk(self.source):
            if is_toplevel:
                self._remove_hidden(dirs)
                self._remove_hidden(files)
                is_toplevel = False
            for x in (dirs+files):
                path = os.path.join(root, x)
                if os.lstat(path).st_mtime > reftime:
                    print("... `%s' has changed!" % path)
                    return True
        return False
    def prepare(self, reftime=None):
        # must sync?
        if self.source_exists:
            directory = os.path.join(self.target, self.basename)
            target_exists = True
            if not os.path.exists(directory):
                print("\033[31;1mWarning: The target directory `%s' doesn't "
                    "exist.\033[0m" % directory)
                target_exists = False
            if reftime:
                if self.has_changed(reftime):
                    self._ready_for_sync = confirm("Do you want to save "
                        "`\033[33;1m%s\033[0m' (`%s'), "
                        "which has \033[33;1mchanged\033[0m [Y/n]? " %
                        (self.name, self.source), True and target_exists)
                else:
                    self._ready_for_sync = confirm("Do you want to save "
                        "`\033[33;1m%s\033[0m' (`%s'), "
                        "which has \033[33;1mNOT\033[0m changed [y/N]? " %
                        (self.name, self.source), False)
            else:
                self._ready_for_sync = confirm("Do you want to save "
                    "`\033[33;1m%s\033[0m' (`%s') [y/n]? " % (self.name,
                    self.source))
        else:
            self._ready_for_sync = False
            print("\033[31;1mSkipping `%s' because the source dir `%s' "
                "doesn't exist.\033[0m" % (self.name, self.source))
        # use bpd?
        if self._ready_for_sync:
            if self.advise_bpd:
                self._use_bpd = True
            else:
                self._use_bpd = confirm("Do you want to use BPD [y/n]? ",
                    False)

class RsyncLauncher():
    default_args = (
        "rsync",
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
    )
    def __init__(self, source, target, bpd_dir=None):
        self.args = list(self.default_args)
        self.source = source
        self.target = target
        self.bpd_dir = bpd_dir
        if self.bpd_dir:
            self.args.extend(('--backup', '--backup-dir', self.bpd_dir))
        self.args.extend(('--exclude', '/%s/.*' %
            os.path.basename(self.source)))
        self.args.append(source)
        self.args.append(target)
    def run(self):
        subprocess.run(self.args, check=True)
    def __str__(self):
        return ' '.join(self.args)

class LogFile():
    def __init__(self, filename, hostname, op_time):
        # op_time = struct_time
        super().__init__()
        self.filename = filename
        self.hostname = hostname
        self.op_time = op_time
        self._data = dict()
        self._read_data()
    def _read_data(self):
        # format: hostname: source -> target @ date... (date: xxxx-xx-xx xx:xx:xx)
        try:
            print("Reading `%s'..." % self.filename)
            for line in open(self.filename):
                match = re.match(self.hostname +
                    r": (?P<source>\S+) -> (?P<target>\S+) @ "
                    r"(?P<timestamp>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)", line)
                if match:
                    source = match.group('source')
                    target = match.group('target')
                    timestamp  = match.group('timestamp')
                    timestruct = time.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    assert time.strftime("%Y-%m-%d %H:%M:%S", timestruct) \
                        == timestamp
                    self._data[(source, target)] = (timestamp,
                        calendar.timegm(timestruct))
            print("Entries found in the log:")
            for item in self._data.items():
                print("- %s -> %s (%s)" % (item[0][0], item[0][1],
                    item[1][0]))
        except FileNotFoundError:
            print("Log file `%s' not found" % self.filename)
    def write(self, source, target, location, cmd):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", self.op_time)
        open(self.filename, 'a').write("%s: %s -> %s @ %s %s `%s'\n" % \
            (self.hostname, source, target, timestamp, location, cmd))
    def write_ok(self):
        open(self.filename, 'a').write("... ok!\n")
    def get_reftime_for(self, source, target):
        # returns a float timestamp
        res = self._data.get((source, target), None)
        if res:
            return res[1]
        return None

########################################################################

def ask_for_direction():
    while True:
        buf = input("Choose direction [l = to local, r = to remote, quit]: ")
        buf = buf.strip()
        if buf == 'l':
            while True:
                print("\033[1;31m"+ASCII_TO_LOCAL+"\033[0m")
                buf = input("Type `erase local data' to confirm (or quit): ")
                buf = buf.strip()
                if buf == 'erase local data':
                    return TO_LOCAL
                elif buf == 'quit':
                    raise QuitException
                print("Invalid answer.  Try again.")
        elif buf == 'r':
            while True:
                print("\033[1;32m"+ASCII_TO_REMOTE+"\033[0m")
                buf = input("Is this correct [y/n]? ")
                buf = buf.strip()
                if buf == 'y':
                    return TO_REMOTE
                elif buf == 'quit' or buf == 'n':
                    raise QuitException
                print("Invalid answer.  Try again.")
        elif buf == 'quit':
            raise QuitException
        print("Invalid answer.  Try again.")

def get_bpd_dir(bpd_base_dir, op_time):
    # op_time = struct_time
    if not os.path.exists(bpd_base_dir):
        raise FileNotFoundError("%s not found" % bpd_base_dir)
    if not os.path.isdir(bpd_base_dir):
        raise FileNotFoundError("%s not a directory" % bpd_base_dir)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
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


########################################################################

if __name__ == '__main__':
    # variables and constants
    if not (TEST_MODE or os.getenv('LOGNAME', '') == 'root'):
        raise Exception("you're not root!")
    if not os.path.exists(REMOTE_BASE_DIR):
        raise FileNotFoundError(REMOTE_BASE_DIR)
    try:
        direction = ask_for_direction()
    except QuitException:
        print("Aborted on user request.")
        sys.exit(0)
    op_time = time.gmtime()
    bpd_dir = get_bpd_dir(BPD_BASE_DIR, op_time)
    hostname = socket.gethostname()
    if not hostname:
        raise Exception("no hostname found")
    location = ask_location()
    BackupItem.remote_base_dir = REMOTE_BASE_DIR
    BackupItem.direction = direction
    # objects
    log = LogFile(os.path.join(REMOTE_BASE_DIR, 'LOG'), hostname, op_time)
    if TEST_MODE:
        items = [
            BackupItem('/home/bruno/scripts/newbackpack/testing/test_local',
                False),
        ]
    else:
        items = [
            BackupItem('/home/bruno', True),
            BackupItem('/home/storeroom', True),
            BackupItem('/home/blib', True),
            BackupItem('/home/pendingblib', True),
            BackupItem('/home/papps', False),
            BackupItem('/home/playground', False),
            BackupItem('/home/TODO', False),
            BackupItem('/media/bruno/storage/big_01_important', False),
            BackupItem('/media/bruno/storage/big_02_useful', False),
            BackupItem('/media/bruno/storage/big_03_less_useful', False),
        ]
    rsync_cmds = []
    for item in items:
        item.prepare(log.get_reftime_for(item.source, item.target))
        if item.ready_for_sync:
            bpd = bpd_dir if item.use_bpd else None
            rsync_cmds.append(RsyncLauncher(item.source, item.target, bpd))
    # confirm
    if not len(rsync_cmds):
        print("Nothing to synchronize!")
    else:
        print('-'*72)
        print("We will run the following commands:")
        for cmd in rsync_cmds:
            print(" - \033[1m%s -> %s (BPD: %s)\033[0m" % (cmd.source, cmd.target,
                "yes" if cmd.bpd_dir else "no"))
            print("   " + str(cmd))
        if confirm("Are you ok [Y/n]? ", True):
            for cmd in rsync_cmds:
                print("Running: " + str(cmd))
                log.write(cmd.source, cmd.target, location, str(cmd))
                cmd.run()
                log.write_ok()
        else:
            print("You're not ok. Nothing done!")
    print('done!')



