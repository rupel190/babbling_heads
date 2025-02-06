import cups
import os

# csv_file = "databreaches_kaggle.csv"
DIR_PREFIX = "/home/rupel/Documents/babbling_melons/"

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
        print_job = self.conn.printFile(
            self.printer_name, TMP_FILE, "Thermo Print Job", {}
        )
        print(f"Print job {print_job} submitted.")
