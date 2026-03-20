```
sudo apt install rclone
rclone config
mkdir ~/{MOUNT PATH}
rclone mount gdrive:{DRIVE PATH} ~/{MOUNT PATH} --drive-shared-with-me --vfs-cache-mode full
sudo umount -l ~/{MOUNT PATH}
```
