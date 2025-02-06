import os
import requests


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
