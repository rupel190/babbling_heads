#!/bin/bash
PRINTER_NAME="ZJ-58"
DEVICE_URI="serial:/dev/serial0?baud=9600"
PPD_PATH="/usr/share/cups/model/zjiang/ZJ-58.ppd"
CUPS_SERVICE="cups"

echo "Updating and installing required packages..."
sudo apt-get update && sudo apt-get install -y cups libcups2-dev libcupsimage2-dev

echo "Install printer driver..."
if [ ! -f /usr/share/cups/model/zjiang/ZJ-58.ppd ]; then
    echo "Installing ZJ-58 printer driver..."
    git clone https://github.com/adafruit/zj-58.git /tmp/zj-58
    cd /tmp/zj-58
    make
    sudo ./install
    cd -
    rm -rf /tmp/zj-58
else
    echo "ZJ-58 printer driver already installed."
fi

echo "Ensuring CUPS is running..."
sudo systemctl enable $CUPS_SERVICE
sudo systemctl start $CUPS_SERVICE

echo "Adding user 'rupel' to lpadmin group..."
sudo usermod -aG lpadmin rupel

echo "Setting up the printer $PRINTER_NAME..."
sudo lpadmin -p $PRINTER_NAME -E -v $DEVICE_URI -P $PPD_PATH
lpoptions -d $PRINTER_NAME
echo "Restarting CUPS to apply changes..."
sudo systemctl restart $CUPS_SERVICE

echo "Printer setup complete. Testing printer..."
echo "Test print Raspberry Pi" | lp

#Usage
#ssh $REMOTE_HOST "chmod +x $REMOTE_SCRIPT_PATH && bash $REMOTE_SCRIPT_PATH"

