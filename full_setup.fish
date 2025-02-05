#!/usr/bin/fish

set REMOTE_HOST "feetfirst"
set WORKING_DIR "/home/rupel/Documents/babbling_melons"
set SYNC_DIR "/synced"
set SCRIPT_DIR "$WORKING_DIR$SYNC_DIR"

echo "Syncing sync $SYNC_DIR folder to $REMOTE_HOST..."
fish "$WORKING_DIR/syncedfolder_sync.fish"

echo "Setting up Fish shell on $REMOTE_HOST..."
ssh $REMOTE_HOST "bash $SCRIPT_DIR/setup_fish.sh"

echo "Configuring firewall on $REMOTE_HOST..."
ssh $REMOTE_HOST "fish $SCRIPT_DIR/setup_firewall.fish"

echo "Enabling serial and UART on $REMOTE_HOST..."
ssh $REMOTE_HOST "fish $SCRIPT_DIR/setup_serial_uart.fish"

echo "Setting up the printer on $REMOTE_HOST..."
ssh $REMOTE_HOST "bash $SCRIPT_DIR/setup_printer.sh"

echo "Setting up babbling service on $REMOTE_HOST..."
ssh $REMOTE_HOST "fish $SCRIPT_DIR/setup_babble_service.fish"

echo "Setup complete on $REMOTE_HOST!"

echo "Rebooting $REMOTE_HOST..."
ssh $REMOTE_HOST "sudo reboot"
