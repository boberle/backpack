if [ "$LOGNAME" != "root" ]; then
   echo "You're not root!"
   exit
fi

sync
echo 3 > /proc/sys/vm/drop_caches
blockdev --flushbufs /dev/sdc
sdparm -v --command sync /dev/sdc

echo "done!"
