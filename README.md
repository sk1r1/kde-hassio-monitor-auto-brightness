# kde-hassio-monitor-autobrightness

AI generated script for changing brightness automatically on KDE/Plasma based by lux values, provided from Home Assistant 

(assuming you can change your monitor brightness under System Settings > Display Configuration > Brightness)

0. provide HomeAssistant URL, API token and entity to config section
1. install `kscreen-doctor` and find out your monitors output with `kscreen-doctor --outputs`
2. write them down to `DISPLAY_OUTPUTS`
3. create user service `mkdir -p ~/.config/systemd/user`, then `nano ~/.config/systemd/user/auto-brightness.service`
4. enable user service by `systemctl --user enable auto-brightness.service` and `systemctl --user start auto-brightness.service`
5. forget about manually changing brightness!

P.S. LUX_BRIGHTNESS_MAPPING requires tuning individually. 
