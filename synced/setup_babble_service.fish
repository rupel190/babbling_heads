#!/usr/bin/fish

# Define the service file path
set SERVICE_FILE "/etc/systemd/system/babbling_melon.service"

# Temporary file to store the service content
set TEMP_FILE "/tmp/babbling_melon.service"
set PYTHON_PARAMS "-v --dry-run"

# Write the service content to the temporary file
echo "Writing service file to temporary location..."
echo "[Unit]
Description=Run babbling melon script!
After=network.target

[Service]
User=rupel
Type=simple
ExecStart=/usr/bin/python3 /home/rupel/Documents/babbling_melons/synced/talk.py $PYTHON_PARAMS
WorkingDirectory=/home/rupel/Documents/babbling_melons
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
Restart=always

[Install]
WantedBy=multi-user.target" > $TEMP_FILE

# Verify the temporary file exists
if test -f $TEMP_FILE
    echo "Service file written successfully to $TEMP_FILE."
else
    echo "Failed to write service file to $TEMP_FILE."
    exit 1
end

# Move the temporary file to the systemd directory with sudo
echo "Moving service file to $SERVICE_FILE..."
sudo mv $TEMP_FILE $SERVICE_FILE

# Reload systemd to recognize the new service
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting service..."
sudo systemctl enable babbling_melon.service
sudo systemctl restart babbling_melon.service
sudo systemctl status babbling_melon.service

