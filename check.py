#!/usr/bin/python3
import os, time, sys

REFTIME_FILE = 'timeref'
DIR_PREFIX_LOCAL = '/home'
DIR_PREFIX_REMOTE = '/mnt/removable/backpack'

DIR_LIST = [
    #'bruno',
    'storeroom',
    'blib',
    'playground',
    'papps',
    'pendingblib',
    'TODO',
    #'libinuse',
    #'library',
    #'libwasinuse',
    #'nobackup',
    #'storage',
]

def remove_hidden(items):
    l = len(items)
    i = 0
    while i < l:
        if (items[i].startswith('.')):
            del items[i]
            l -= 1
        else:
            i += 1

def walk(topdir):
    print("Browsing "+topdir)
    is_toplevel = True
    for root, dirs, files in os.walk(topdir):
        if is_toplevel:
            remove_hidden(dirs)
            remove_hidden(files)
            is_toplevel = False
        for x in (dirs+files):
            path = os.path.join(root, x)
            if os.lstat(path).st_mtime > reftime:
                print("dir has changed, file: "+path)
                return True
    return False

if __name__ == '__main__':

    # get ref time
    print("Getting reftime from "+REFTIME_FILE)
    reftime = os.lstat(REFTIME_FILE).st_mtime
    print("Ref time is: "+time.ctime(reftime))

    # get the direction
    while True:
        buf = input("What direction [1 = to usb (backup), 2 = to local "
            "(restore)]? ")
        buf = buf.strip()
        if buf == "1":
            prefix = DIR_PREFIX_LOCAL
            break
        elif buf == "2":
            prefix = DIR_PREFIX_REMOTE
            break

    # analyse each dirs
    changed_dirs = []
    for topdir in DIR_LIST:
        path = os.path.join(prefix, topdir)
        if walk(path):
            changed_dirs.append(path)

    # print result
    print("SUMMARY:")
    for path in changed_dirs:
        print(" - "+path)

