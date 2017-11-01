if [ "$LOGNAME" != "root" ]; then
   echo "You're not root!"
   exit
fi

dev="/dev/sdc"
umount $dev"1" && sync && eject $dev && udisksctl power-off -b $dev

echo "done!"
