import os
import threading
from flask import Flask, request, jsonify


class FlaskServer:
    def __init__(self, thermo_printer):
        """
        Initialize Flask server to handle print requests from other Pi.
        :param thermo_printer: Instance of ThermoPrinter to handle print jobs
        """
        self.thermo_printer = thermo_printer
        self.app = Flask(__name__)
        self.setup_routes()
        self.server_thread = None

    def setup_routes(self):
        """Define Flask routes"""

        @self.app.route("/print", methods=["POST"])
        def print_text():
            content = request.json.get("message", "No content")
            print(f"Received print request: {content}")
            self.thermo_printer.thermo_print(content)  # Call the ThermoPrinter instance
            return jsonify({"status": "Printed", "content": content}), 200

        @self.app.route("/shutdown", methods=["POST"])
        def shutdown():
            """Shutdown Flask server"""
            print("Shutting down Flask server...")
            shutdown_func = request.environ.get("werkzeug.server.shutdown")
            if shutdown_func:
                shutdown_func()
            return jsonify({"status": "Server shutting down"}), 200

    def start(self, host="0.0.0.0", port=5000):
        """Start Flask server in a separate thread"""
        self.server_thread = threading.Thread(
            target=self.app.run,
            kwargs={"host": host, "port": port, "debug": False, "use_reloader": False},
            daemon=True,
        )
        self.server_thread.start()

    def stop(self):
        """Send a request to Flask server to shut it down"""
        import requests

        try:
            requests.post("http://127.0.0.1:5000/shutdown", timeout=3)
            print("Flask server shutdown triggered.")
        except requests.exceptions.RequestException:
            print("Error while shutting down Flask server.")
