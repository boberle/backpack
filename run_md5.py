import os, subprocess, sys

TO_LOCAL = 1
TO_REMOVE = 2

LOCAL_LOGS = "logs"
REMOTE_LOGS = "/mnt/removable/backpack/logs"
#REMOTE_LOGS = "/tmp/backpack/remote/logs"

def ask_for_direction():
    while True:
        buf = input("Choose direction [l = to local, r = to remote, quit]: ")
        buf = buf.strip().lower()
        if buf == 'l':
            return TO_LOCAL
        elif buf == 'r':
            return TO_REMOVE
        elif buf == 'quit':
            sys.exit(0)
        print("Invalid answer.  Try again.")

def choose_file(directory):
    filenames = os.listdir(directory)
    if len(filenames) > 20:
        print("\033[1;33mWarning: The directory has %d items.\033[0m"
            % len(filenames))
    filenames.sort(key=lambda x: os.lstat(os.path.join(directory,
        x)).st_mtime_ns)
    filenames.reverse()
    filenames = [f for f in filenames if f.endswith('.dest')][0:20]
    for i, filename in enumerate(filenames):
        print("%02d: %s" % (i, filename))
    if not filenames:
        print("No file.")
        return None
    buf = ""
    while True:
        buf = input("Choose the file to use (a number or `q[uit]')? ")
        buf = buf.strip().lower()
        if buf in ("q", "quit"):
            return None
        args = [x for x in buf.split(" ") if x]
        fail = False
        for arg in args:
            if not arg.isdigit() or \
                    not (int(arg)>=0 and int(arg)<len(filenames)):
                print("I don't understand. Try again.")
                fail = True
                break
        if not fail:
            return [os.path.join(directory,
                filenames[int(arg)]) for arg in args]


if __name__ == "__main__":
    direction = ask_for_direction()
    if direction == TO_LOCAL:
        directory = LOCAL_LOGS
    else:
        directory = REMOTE_LOGS
    if not os.path.isdir(directory):
        raise RuntimeError("`%s' not a dir" % directory)
    filenames = choose_file(directory)
    if not filenames:
            sys.exit(0)
    for filename in filenames:
        args = ['md5sum', '-c', filename]
        while True:
            buf = input("Run `%s' [Y/n]? " % " ".join(args))
            if buf in "yY":
                run = True
                break
            elif buf in "nN":
                run = False
                break
            else:
                print("don't understand")
        if not run:
            continue
        proc = subprocess.run(args)
        if proc.returncode:
            input("\033[31;1m*** /!\\   Failed!   /!\\ ***\033[0m "
                "Press Enter...")
        else:
            input("\033[32;1mSuccess!\033[0m Press Enter...")

