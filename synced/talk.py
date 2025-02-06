#!/usr/bin/env python3

import os
import csv
import json
import argparse
from itertools import islice
import thermo_printer
import motion_detector
import flask_server
import print_client
import atexit
import time
import data_source

DIR_PREFIX = "/home/rupel/Documents/babbling_honeymelons/"
DIR_PREFIX = "./"
CSV_FILE = os.path.join(DIR_PREFIX, "short_data.csv")
STATE_FILE = os.path.join(DIR_PREFIX, "../state.json")


def save_state(position):
    with open(STATE_FILE, "w") as f:
        print(f"Save state with position {position}.")
        json.dump({"position": position}, f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            print(f"Load state with position {state.get('position')}")
            return state.get("position", 0)  # Default
    else:
        save_state(0)
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Thermoprint csv with dry-run option")
    parser.add_argument(
        "--dry-run", action="store_true", help="Deactivate physical printer"
    )
    parser.add_argument("-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--delay",
        type=int,
        default=60,
        help="Delay between processing batches in seconds (default: 60)",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=2,
        help="Number of lines to print per batch (default: 4)",
    )
    parser.add_argument(
        "--detection-pause",
        type=int,
        default=30,
        help="Motion detection timeout after print in seconds (default: 30)",
    )
    return parser.parse_args()


def trigger_print(data_source, local_printer, print_client):
    print("Motion sensor callback!!!")
    start_pos = load_state()
    start_pos = 1  # TODO: Remove
    lines = data_source.fetch_data(start_pos, start_pos + args.lines)

    for i, row in lines.items():
        formatted = (
            f"{row['title']}\n{row['author']}\n{row['published_at'].split(' ')[0]}"
        )
        print(
            f"\n>>> Sending {formatted} to {'Local' if i % 2 == 0 else 'Remote'}\n<<<"
        )
        if i % 2 == 0:
            # Even index → Local Printer
            if not args.dry_run:
                local_printer.thermo_print(formatted)
        else:
            # Odd index → Remote Printer
            if not args.dry_run:
                print_client.send_print_request(formatted)

        time.sleep(args.delay)


# Main function to trigger processing
def main():
    global args
    args = parse_args()

    try:
        # Printers
        thermo = thermo_printer.ThermoPrinter()
        remote_printer = print_client.PrintClient()  # TODO: Re-init on fail?
        # Data Source
        csv = data_source.CsvDataSource(CSV_FILE)
        # Motion Detectors
        motion_detectors = motion_detector.MotionDetector(
            debounce_time=args.detection_pause,
            callback=lambda: trigger_print(csv, thermo, remote_printer),
        )
        if args.v:
            print("Printers initialized: ", thermo, remote_printer)
            print("Motion detectors initialized: ", motion_detectors)
        # Print Server
        server = flask_server.FlaskServer(thermo)
        atexit.register(server.stop)
        server.start()
        print("Flask print server running...")

        time.sleep(7)
        motion_detectors.on_motion_detected("debugging")

    except (RuntimeError, ValueError) as e:
        if args.dry_run:
            print(
                "⚠️ Dry-run: ThermoPrinter not initializing. Simulating motion detection..."
            )
            trigger_print(data_source.CsvDataSource(CSV_FILE), None, None)
        else:
            print(f"⚠️ Warning: Failed to initialize ThermoPrinter: {e}")


if __name__ == "__main__":
    # TODO: Delete when run as service
    try:
        main()  # Start all components
        # Keep the script running indefinitely
        print("Script is running... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting gracefully...")
