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

DIR_PREFIX = "/home/rupel/Documents/babbling_honeymelons/"
CSV_FILE = os.path.join(DIR_PREFIX, "short_data.csv")
STATE_FILE = os.path.join(DIR_PREFIX, "state.json")


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


# Function to process the CSV in chunks
def process_csv_in_chunks(file_path, start_pos, chunk_size):
    with open(file_path, mode="r") as f:
        csv_reader = csv.reader(f)
        if args.v:
            print(f"Process csv path {file_path}:{start_pos}, chunk size {chunk_size}")
        # Get the header
        if start_pos <= 0:
            header = next(csv_reader)
            print(
                f"{header[0]:<20} {header[1]:<10} {header[2]:<10} {header[3]:<15} {header[4]}"
            )
            print("=" * 60)
        else:
            # Start enumeration at start_pos
            if args.v:
                print(f"Skipping csv reader to position {start_pos}")
            csv_reader = islice(csv_reader, start_pos, None)

        # Process file in chunks
        chunk = []
        for i, row in enumerate(csv_reader, start=start_pos):
            chunk.append(row)
            if i % chunk_size == 0:  # Trigger every 'chunk_size' rows
                yield chunk
                chunk = []
                save_state(i)
        if chunk:  # Yield the remaining rows
            yield chunk
            # Reset
            save_state(0)


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
        help="Number of lines to print per batch (default: 2)",
    )
    parser.add_argument(
        "--detection-pause",
        type=int,
        default=30,
        help="Motion detection timeout after print in seconds (default: 30)",
    )
    return parser.parse_args()


def format_row(row):
    return f"{row[4].strip()[:120]}\n{row[8].strip().split(' ')[0]} {row[3].strip()}"


def trigger_print(local_printer, print_client):
    print("Motion sensor callback!!!")
    start_pos = load_state()

    # TODO: For some reason prints the whole file here in a single callback.
    for chunk in process_csv_in_chunks(CSV_FILE, start_pos, chunk_size=args.lines):
        if args.v:
            print(f"\nPrint chunk of {CSV_FILE}:{start_pos} with size {args.lines}")
        for row in chunk:
            row = format_row(row)
            if args.v:
                print(f">>>\n{row}\n<<<")
            if not args.dry_run:
                local_printer.thermo_print(row)
            # Trigger second pi to print. Requires chunk > 2 lines.
            next_row = format_row(next(iter(chunk)))
            if args.v:
                print(f">>>\n{row}\n<<<")
            if not args.dry_run:
                print_client.send_print_request(next_row)


# Main function to trigger processing
def main():
    global args
    args = parse_args()

    thermo = thermo_printer.ThermoPrinter()
    remote_printer = print_client.PrintClient()  # TODO: Re-init on fail?

    motion_detectors = motion_detector.MotionDetector(
        debounce_time=args.detection_pause,
        callback=lambda: trigger_print(thermo, remote_printer),
    )

    if args.v:
        print("Printers initialized: ", thermo, remote_printer)
        print("Motion detectors initialized: ", motion_detectors)
    server = flask_server.FlaskServer(thermo)
    atexit.register(server.stop)
    server.start()
    print("Flask print server running...")

    time.sleep(7)
    motion_detectors.on_motion_detected("debugging")


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
