def read_csv(path):
    with open(path, "r") as f:
        lines = f.readlines()
    return [int(line.strip()) for line in lines[1:]]
