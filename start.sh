# mounting

if [ "$LOGNAME" != "root" ]; then
   echo "You're not root!"
   exit
fi

dev="/dev/sdc1"
umount $dev
mount -o noatime $dev /mnt/removable

echo "done!"
