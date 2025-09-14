import pandas as pd
from datetime import datetime

def parse_rinex_obs(filename):
    records = []

    with open(filename, "r") as f:
        lines = f.readlines()

    # Skip header
    start_idx = 0
    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            start_idx = i + 1
            break

    i = start_idx
    current_time = None

    while i < len(lines):
        line = lines[i].strip()

        # Epoch line starts with ">"
        if line.startswith(">"):
            parts = line.split()
            year, month, day = map(int, parts[1:4])
            hour, minute = map(int, parts[4:6])
            sec = float(parts[6])
            current_time = datetime(year, month, day, hour, minute, int(sec))
            i += 1
            continue

        # Satellite observation line
        if line.startswith("G"):  # only GPS sats
            sat_id = int(line[1:3])
            # Columns are fixed width 16 chars each
            values = [
                line[3:19].strip(),   # C1C
                line[19:35].strip(),  # L1C
                line[35:51].strip(),  # D1C
                line[51:67].strip(),  # S1C
            ]
            values = [float(v) if v != "" else None for v in values]

            time_seconds = (
                current_time.hour * 3600
                + current_time.minute * 60
                + current_time.second
            )

            records.append([time_seconds, sat_id] + values)

        i += 1

    # Create DataFrame
    df = pd.DataFrame(records, columns=["Time_seconds", "SatelliteID", "C1C", "L1C", "D1C", "S1C"])
    return df


# Example usage
filename = r"./rinex_out/20240214-041908.obs"
df = parse_rinex_obs(filename)

# Save as tab-delimited file
df.to_csv("test_RTK1.txt", sep="\t", index=False)

print(df.head())
