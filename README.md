# Backup And Synchronization Tool

This is wrapper around rsync. It let you define directories that you can copy from a hard drive to a USB stick (or another external drive) and vice-versa so you can keep **synchronize** them accross different computers.

You can also use it has a **backup** tool.

The script compute the md5 checksum of each file that is copied to the external device. A helper script, `run_md5.py` let you check that the file are correctly copied (I once had a problem with a defective key).

The script let you choose which directories you want to copy, if you want to make a backup of every file that is deleted.

**More information to come.**
