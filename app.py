import subprocess
from pathlib import Path
import time
import pandas as pd
from datetime import datetime

def ubx_to_rinex(ubx_file: str, output_dir: str, convbin_path: str):
    """
    Convert UBX file to RINEX 3.02 using convbin from RTKLIB 2.4.3+
    """
    ubx_path = Path(ubx_file).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Command for RTKLIB 2.4.3+ with RINEX 3.02 support
    cmd = [
        str(Path(convbin_path).resolve()),
        str(ubx_path),
        "-r", "ubx",           # Input format: u-blox
        "-v", "3.02",          # RINEX version 3.02
        "-od", "-os",          # Include Doppler and SNR
        "-d", str(out_dir)     # Output directory
    ]

    print("Running:", " ".join(cmd))
    
    # Run the conversion with timeout
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120  # 2 minute timeout
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"convbin failed with code {result.returncode}")
    
    # Give the system a moment to finish writing files
    time.sleep(1)
    
    # Verify RINEX version in the output files
    #verify_rinex_version(out_dir)

    print("Conversion finished. Files written to:", out_dir)
    return list(out_dir.glob("*.*"))  # return all files created

def verify_rinex_version(output_dir: Path):
    """
    Verify that the generated files are RINEX 3.02
    """
    output_dir = Path(output_dir)
    
    for obs_file in output_dir.glob("*.obs"):
        try:
            with open(obs_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
            
            if '3.02' in first_line:
                print(f"✓ Verified: {obs_file.name} is RINEX 3.02")
            else:
                print(f"⚠ Warning: {obs_file.name} is not RINEX 3.02 (found: {first_line})")
                
        except Exception as e:
            print(f"Error reading {obs_file}: {e}")

def check_convbin_version(convbin_path: str):
    """
    Check the convbin version to ensure it supports RINEX 3.02
    """
    try:
        cmd = [str(Path(convbin_path).resolve()), "-h"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if "version" in result.stdout.lower() or "2.4.3" in result.stdout:
            print("✓ convbin version appears to support RINEX 3.02")
        else:
            print("ℹ convbin version info:", result.stdout[:200] + "...")
            
    except Exception as e:
        print(f"Error checking convbin version: {e}")

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
if __name__ == "__main__":
    convbin_path = r"convbin.exe"
    ubx_name = "20240214-041908"
    
    # First check the version
    #check_convbin_version(convbin_path)
    
    # Then perform conversion
    files = ubx_to_rinex(
        ubx_name+".UBX",
        r"rinex_out",
        convbin_path
    )
    print("Generated files:", [f.name for f in files])

    # Example usage
    filename = f"./rinex_out/{ubx_name}.obs"
    df = parse_rinex_obs(filename)

    # Save as tab-delimited file
    df.to_csv("test_RTK1.csv")

    print(df.head())