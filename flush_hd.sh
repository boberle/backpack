if [ "$LOGNAME" != "root" ]; then
   echo "You're not root!"
   exit
fi

sync
echo 3 > /proc/sys/vm/drop_caches
blockdev --flushbufs /dev/sda
hdparm -F /dev/sda # for SATA/IDE

echo "done!"
