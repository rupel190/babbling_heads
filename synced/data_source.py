import os
import csv
import json
import requests
from itertools import islice
from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def fetch_data(self, start_pos, end_pos):
        """Fetch data method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")


class CsvDataSource(DataSource):
    def __init__(self, file_path):
        self.file_path = file_path

    def fetch_data(self, start_pos, end_pos):
        """
        Read range of lines from the CSV file.
        :param line_range: A range object or list specifying the lines to read (e.g., range(0, 5))
        :return: List of rows as dictionaries
        """
        data = {}
        try:
            with open(self.file_path, mode="r") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(
                    islice(reader, start_pos, end_pos), start=start_pos
                ):
                    data[i] = row
                print(f"Read {len(data)} rows from the CSV file.")
        except FileNotFoundError:
            print(f"Error: CSV file '{self.file_path}' not found.")
        except Exception as e:
            print(f"Error: reading CSV file: {e}")
        return data


#
# API Data Source
class APIDataSource(DataSource):
    def __init__(self, api_url, api_key=None):
        self.api_url = api_url
        self.api_key = api_key

    def fetch_data(self, start_pos, end_pos):
        """
        Fetch data from API.
        :return: List of rows as dictionaries.
        """
        try:
            print("Fetching data from the API...")
            headers = (
                {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response = requests.get(
                self.api_url, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()  # Raise an error for HTTP errors
            data = response.json()  # Assuming the API returns JSON
            print(f"Fetched {len(data)} rows from the API.")
            return data
        except (requests.RequestException, ValueError) as e:
            print(f"API request failed: {e}.")
            return []
