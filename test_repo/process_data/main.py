from process_data.utils import read_numbers

def process_data():
    numbers = read_numbers()
    total = sum(numbers)
    return {"sum": total}

