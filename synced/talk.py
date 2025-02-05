#!/usr/bin/env python3

import os
import csv
import time
import json
import cups
import argparse
from gpiozero import MotionSensor
from itertools import islice
from flask import Flask, request, jsonify
import threading
import requests


# csv_file = "databreaches_kaggle.csv"
DIR_PREFIX = "/home/rupel/Documents/babbling_melons/"

CSV_FILE = os.path.join(DIR_PREFIX, "data_world.csv")
STATE_FILE = os.path.join(DIR_PREFIX, "state.json")

TMP_DIR = os.path.join(DIR_PREFIX, "temp")
os.makedirs(TMP_DIR, exist_ok=True)
TMP_FILE = os.path.join(DIR_PREFIX, TMP_DIR, "printbuffer.txt")


class FlaskServer:
    def __init__(self, thermo_printer):
        """
        Initialize Flask server to handle print requests from other pi.
        :param thermo_printer: Instance of ThermoPrinter to handle print jobs
        """
        self.thermo_printer = thermo_printer
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Define Flask routes"""

        @self.app.route("/print", methods=["POST"])
        def print_text():
            content = request.json.get("message", "No content")
            print(f"Received print request: {content}")
            self.thermo_printer.thermo_print(content)  # Call the ThermoPrinter instance
            return jsonify({"status": "Printed", "content": content}), 200

    def start(self, host="0.0.0.0", port=5000):
        """Start Flask server in a separate thread to avoid blocking the main application"""
        server_thread = threading.Thread(
            target=self.app.run,
            kwargs={"host": host, "port": port, "debug": False, "use_reloader": False},
            daemon=True,
        )
        server_thread.start()


class PrintClient:
    def __init__(self):
        """Determine other Pi's hostname dynamically"""
        hostname = os.popen("hostname").read().strip()

        if "feetfirst" in hostname:
            self.other_pi = "http://headfirst:5000/print"
        else:
            self.other_pi = "http://feetfirst:5000/print"

    def send_print_request(self, message):
        """Send print request to other Pi"""
        try:
            response = requests.post(
                self.other_pi, json={"message": message}, timeout=5
            )
            print(
                f"Triggered other Pi {self.other_pi} to print! Response: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            print(f"Failed to reach {self.other_pi}. Error: {e}")


class ThermoPrinter:
    def __init__(self, printer_name=None):
        # Initialize CUPS connection
        self.conn = cups.Connection()

        # Set printer name (use first printer if not specified)
        if printer_name is None:
            printers = self.conn.getPrinters()
            if not printers:
                raise ValueError("No printers found.")
            self.printer_name = next(iter(printers))
        else:
            self.printer_name = printer_name

        print(f"Initialized ThermoPrinter with printer: {self.printer_name}")

    def thermo_print(self, content):
        # Write the content to a temporary file
        with open(TMP_FILE, "w") as f:
            f.write(content)
        # Print the temporary file
        print_job = self.conn.printFile(
            self.printer_name, TMP_FILE, "Thermo Print Job", {}
        )
        print(f"Print job {print_job} submitted.")


class MotionDetector:
    def __init__(self, debounce_time, callback=None):
        """
        MotionDetector class
        :param debounce_time: Time in seconds to prevent rapid re-triggers
        :param callback: Function to call on motion detection
        """
        self.debounce_time = debounce_time
        self.callback = callback if callback else self.default_callback
        self.last_triggered = 0

        self.PIR_SENSOR_1 = 23  # TODO: Make sure it's correct
        self.PIR_SENSOR_2 = 24
        self.pir1 = MotionSensor(self.PIR_SENSOR_1)
        self.pir2 = MotionSensor(self.PIR_SENSOR_2)

        self.pir1.when_motion = lambda: self.on_motion_detected("Pir 23")
        self.pir2.when_motion = lambda: self.on_motion_detected("Pir 24")

    # TODO: Debounce
    def on_motion_detected(self, name):
        """Debounced motion detection"""
        current_time = time.time()
        if current_time - self.last_triggered <= self.debounce_time:
            self.last_triggered = current_time
            self.callback(name)
        else:
            print(f"Motion ignored / name = {name}!")  # TODO: Delete, too much output

    def default_callback(self, name):
        print(f"Motion detected / name = {name}!")


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
    thermo = ThermoPrinter()
    remote_printer = PrintClient()
    motion = MotionDetector(
        debounce_time=args.detection_pause,
        callback=lambda: trigger_print(thermo, remote_printer),
    )
    server = FlaskServer(thermo)
    server.start()
    print("Flask print server running...")


if __name__ == "__main__":
    main()
