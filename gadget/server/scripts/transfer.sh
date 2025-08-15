#!/bin/bash
sudo modprobe -r g_mass_storage

sleep 5

sudo mount /gadget.img /mnt -o loop

sudo rm -rf /mnt/*
sudo cp /usr/local/bin/gadget/server/upload/* /mnt/
sudo rm -f /usr/local/bin/gadget/server/upload/*

sudo umount /mnt
sudo modprobe g_mass_storage file=/gadget.img removable=1 stall=0
