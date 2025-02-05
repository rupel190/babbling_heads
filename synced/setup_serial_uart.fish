#!/usr/bin/fish

set BOOT_CONFIG "/boot/firmware/config.txt"

set PRINTER_CONFIG "# Printer connection"
set UART_CONFIG "enable_uart=1"
set DISABLE_BT "dtoverlay=pi3-disable-bt"

if test -f $BOOT_CONFIG
    echo "Checking and updating boot config..."

    # Check and add each line individually
    for line in $PRINTER_CONFIG $UART_CONFIG $DISABLE_BT
        if not grep -q "$line" $BOOT_CONFIG
            echo "Adding missing line: $line"
            echo $line | sudo tee -a $BOOT_CONFIG > /dev/null
        else
            echo "Line already present: $line"
        end
    end

    echo "Boot config updated successfully. UART/Serial should be active. On modification a reboot may be required."
else
    echo "Boot config not found: $BOOT_CONFIG"
end

