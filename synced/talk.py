#!/usr/bin/env python3

import os
import csv
import time
import json
import cups
import argparse
from gpiozero import MotionSensor
from itertools import islice


# csv_file = "databreaches_kaggle.csv"
DIR_PREFIX = "/home/rupel/Documents/babbling_melons/"

CSV_FILE = os.path.join(DIR_PREFIX, "data_world.csv")
STATE_FILE = os.path.join(DIR_PREFIX, "state.json")

TMP_DIR = os.path.join(DIR_PREFIX, "temp")
os.makedirs(TMP_DIR, exist_ok=True)
TMP_FILE = os.path.join(DIR_PREFIX, TMP_DIR, "printbuffer.txt") 

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
        print_job = self.conn.printFile(self.printer_name, TMP_FILE, "Thermo Print Job", {})
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

        self.PIR_SENSOR_1 = 23 # TODO: Make sure it's correct
        self.PIR_SENSOR_2 = 24
        self.pir1 = MotionSensor(PIR_SENSOR_1)
        self.pir2 = MotionSensor(PIR_SENSOR_2)

        self.pir1.when_motion = lambda: on_motion_detected("Pir 23")
        self.pir2.when_motion = lambda: on_motion_detected("Pir 24")

    #TODO: Debounce
    def on_motion_detected(name):
        """ Debounced motion detection """"
        current_time = time.time()
        if current_time - self.last_triggered <= self.debounce_time:
            self.last_triggered = current_time
            self.callback(name)
        else:
            print(f"Motion ignored / name = {name}!") #TODO: Delete, too much output

    def default_callback():
        print(f"Motion detected / name = {name}!")


def trigger_print():
    print("MOtion sensor callback working")

def save_state(position):
    with open(STATE_FILE, "w") as f:
        print(f"Save state with position {position}.")
        json.dump({"position": position}, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            print(f"Load state with position {state.get('position')}")
            return state.get("position", 0) # Default
    else:
        save_state(0)
    return 0

# Function to process the CSV in chunks
def process_csv_in_chunks(file_path, start_pos, chunk_size=10):
    with open(file_path, mode="r") as f:
        csv_reader = csv.reader(f)
        if args.v: print(f"Process csv path {file_path}:{start_pos}, chunk size {chunk_size}")
        # Get the header
        if start_pos <= 0:
            header = next(csv_reader)
            print(f"{header[0]:<20} {header[1]:<10} {header[2]:<10} {header[3]:<15} {header[4]}")
            print("=" * 60)
        else:
            # Start enumeration at start_pos
            if args.v: print(f"Skipping csv reader to position {start_pos}")
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
    parser.add_argument("--dry-run", action="store_true", help="Deactivate physical printer")
    parser.add_argument("-v", action="store_true", help="Verbose output")
    parser.add_argument("--delay", type=int, default=60, help="Delay between processing batches in seconds (default: 60)")
    parser.add_argument("--lines", type=int, default=2, help="Number of lines to print per batch (default: 2)")
    parser.add_argument("--detection-pause", type=int, default=30, help="Motion detection timeout after print in seconds (default: 30)")
    return parser.parse_args()


# Main function to trigger processing
def main():
    global args
    args = parse_args()
    start_pos = load_state()
    thermo = ThermoPrinter()
    motion = MotionDetector(debounce_time = args.detection_pause, callback = trigger_print)


    for chunk in process_csv_in_chunks(CSV_FILE, start_pos, chunk_size=args.lines):
        if args.v: print(f"\nPrint chunk of {CSV_FILE}:{start_pos} with size {args.lines}")
        for row in chunk:
            row = f"{row[4].strip()[:120]}\n{row[8].strip().split(' ')[0]} {row[3].strip()}"
            if args.v: print(f">>>\n{row}\n<<<")
            if not args.dry_run:
                thermo.thermo_print(row)
        print(f"Waiting {args.delay} seconds before processing next batch...")
        print("." * 80)
        time.sleep(args.delay) 

if __name__ == "__main__":
    main()


