import json
from process_data.legacy import read_csv

def read_numbers():
    with open("config.json", "r") as f:
        config = json.load(f)
    
    format_type = config.get("format", "txt")
    
    if format_type == "csv":
        # Use legacy CSV reader for CSV format
        return read_csv("data/old_data.csv")
    else:
        # Default text format reader
        with open("data/raw_data.txt", "r") as f:
            return [int(x) for x in f.read().split()]
