# pi_monitor

Once a minute this script monitors system status including CPU temperature, load, power status, NVMe temperature, and connectivity.

It logs the status to a file (most recent entry at the top, and deleting entries after 3 hours to keep the file small) and handles connection issues by restarting the network connection (and reporting that in the error log).

If you don't have an NVMe drive attached you should comment that code out.

Uses `visudo` to allow some specific commands using `sudo` to run without requiring a password, and I have it configured as a service to automatically start on a reboot.

# why did I write this?

While my raspberryPi 3B+ has no problems staying on the network, my [raspberryPi 5 loses it's connection randomly](https://github.com/raspberrypi/trixie-feedback/issues/25) in as little as an hour, and at most about 36 hours. It's got worse since installing the M.2 Hat+ and NVMe drive (both first party), so I wanted to see if there were undervoltage or over temperature issues happening (there aren't) and force the device to reconnect if the network can't ping either a known external or internal host.
Frustrating thing was that I wanted to move pihole and my in-bound vpn connection from the rPi 3B+, but the lack of reliability means that plan is on hold. 

# improvements?

Could maybe do with some throttling to stop it continually trying to restart network if (for instance) we actually lose internet, or the external host is down for any reason.
Best improvement would be a fix to the wifi issue that allows me to retire the script ;)
