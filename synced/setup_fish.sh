#!/bin/bash

# Check if Fish is installed
if ! command -v fish &> /dev/null; then
    echo "Installing Friendly Interactive Shell (Fish)..."
    sudo apt-get update && sudo apt-get install -y fish
    if [ $? -ne 0 ]; then
        echo "Failed to install Fish. Exiting."
        exit 1
    fi
else
    echo "Fish is already installed."
fi

# Change default shell to Fish
echo "Changing default shell to Fish..."
chsh -s "$(command -v fish)"
if [ $? -eq 0 ]; then
    echo "Fish set as default shell. Log out and back in for the change to take effect."
else
    echo "Failed to change default shell. Ensure Fish is installed and you have permissions to change the shell."
    exit 1
fi

