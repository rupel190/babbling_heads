#!/usr/bin/fish

# Install Firewall (with SSH open)
if not type -q ufw
    echo "Installing UFW..."
    sudo apt-get update && sudo apt-get install -y ufw
    if test $status -ne 0
        echo "Failed to install UFW. Exiting."
        exit 1
    end
else
    echo "UFW already installed."
end

echo "Configuring UFW..."
sudo ufw allow OpenSSH &&
sudo ufw enable -y &&
echo 'UFW configured and enabled.'
echo "Verify UFW status..."
sudo ufw status


# Install ZeroTier Remote VPN Tunnel
echo "Installing ZeroTier..."
if command -v zerotier-cli
	echo "ZeroTier already installed"
else
	echo "Installing ZeroTier..."
	curl -s https://install.zerotier.com | sudo bash
	set -U fish_user_paths /usr/sbin $fish_user_paths
end

set zerotier_network_id "9bee8941b57f6ca4"
echo "Joining ZeroTier network: $zerotier_network_id"
sudo zerotier-cli join $zerotier_network_id
if test $status -ne 0
    echo "Failed to join ZeroTier network. Exiting."
    exit 1
end
echo "Successfully joined ZeroTier network."
echo "Restarting zerotier service..."
sudo systemctl restart zerotier-one
echo "Checking network status..."
sleep 2
eval "sudo /usr/sbin/zerotier-cli listnetworks"



# Connect to Wi-Fi
set wlan_ssid "RupelZFold3" # Replace with Wi-Fi SSID
set wlan_password "yzxe3435" # Replace with Wi-Fi password
set wlan_interface "wlan0" 

# Add Wi-Fi network
echo "Scan Wi-Fi devices..."
nmcli device wifi list
echo "Adding Wi-Fi network: $wlan_ssid..."
sudo nmcli device wifi connect $wlan_ssid password $wlan_password hidden yes
if test $status -ne 0
    echo "Failed to connect to Wi-Fi network: $wlan_ssid"
    exit 1
end
echo "Network information: "
nmcli -gpc device show wlan0

