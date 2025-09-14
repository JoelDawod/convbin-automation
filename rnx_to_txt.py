import pandas as pd
from rinex_parser.obs_parser import RinexParser
from datetime import datetime
import re

rnx_file = "TWTF00TWN_R_20240740000_01D_30S_MO.rnx"

# Parse RINEX file
try:
    rnx_parser = RinexParser(rinex_file=rnx_file, rinex_version=3, sampling=30)
    rnx_parser.run()
except Exception as e:
    raise RuntimeError(f"Failed to parse RINEX file: {e}")

rows = []

# Custom function to parse RINEX timestamp format
def parse_rinex_time(time_str):
    """Parse RINEX timestamp format with variable spaces"""
    # Clean up the string - replace multiple spaces with single spaces
    cleaned = re.sub(r'\s+', ' ', str(time_str).strip())
    parts = cleaned.split(' ')
    
    if len(parts) >= 6:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        hour = int(parts[3])
        minute = int(parts[4])
        second = float(parts[5])
        
        return datetime(year, month, day, hour, minute, int(second), int((second - int(second)) * 1000000))
    else:
        raise ValueError(f"Invalid time format: {time_str}")

# Iterate over raw epochs
for epoch in rnx_parser.rinex_reader.rinex_epochs:
    # Get epoch timestamp directly
    epoch_time = getattr(epoch, "timestamp", None)
    
    if epoch_time is None:
        continue

    try:
        # Convert to datetime object
        if hasattr(epoch_time, 'strftime'):  # Already a datetime object
            epoch_dt = epoch_time
        else:
            # Use our custom parser for RINEX format
            epoch_dt = parse_rinex_time(epoch_time)
            
    except Exception as e:
        print(f"Warning: Could not parse time {epoch_time}: {e}")
        continue

    # Calculate seconds since start of day
    time_sec = epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second + epoch_dt.microsecond / 1000000

    # Get satellites for this epoch
    satellites = getattr(epoch, "satellites", [])
    if not satellites:
        continue

    # Process each satellite's observations
    for sat in satellites:
        # From debug output, we know it's a dict with 'id' and 'observations' keys
        if not isinstance(sat, dict):
            continue
            
        sat_id = sat.get('id')
        observations = sat.get('observations', {})
        
        # FILTER: Only process GPS satellites (start with 'G')
        if not sat_id or not sat_id.startswith('G') or not observations:
            continue

        # Extract just the satellite number (remove 'G' prefix)
        sat_number = int(sat_id[1:]) if len(sat_id) > 1 else 0
        
        row = {"Time_seconds": time_sec, "SatelliteID": sat_number}
        
        # Only extract the basic GPS observations we want
        obs_to_extract = ['C1C_value', 'L1C_value', 'D1C_value', 'S1C_value']
        
        for obs_key in obs_to_extract:
            if obs_key in observations:
                # Remove the '_value' suffix for cleaner column names
                col_name = obs_key[:-6]  # Remove '_value'
                row[col_name] = observations[obs_key]
        
        rows.append(row)

# Build DataFrame
if not rows:
    raise RuntimeError("No data parsed - check file format and attribute names")

df = pd.DataFrame(rows)

# Reorder columns with Time_seconds and SatelliteID first, then the observation types
cols = ["Time_seconds", "SatelliteID", "C1C", "L1C", "D1C", "S1C"]
# Only include columns that actually exist in the data
cols = [col for col in cols if col in df.columns]
df = df[cols]

# Save to file
try:
    df.to_csv("rinex_output.txt", sep="\t", index=False, float_format='%.3f')
    print(f"✅ Saved {len(df)} rows to rinex_output.txt")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample data:\n{df.head(10)}")
    
    # Additional info about the data
    print(f"\n📊 Data summary:")
    print(f"Total GPS satellites found: {df['SatelliteID'].nunique()}")
    print(f"GPS satellite numbers: {sorted(df['SatelliteID'].unique())}")
    print(f"Time range: {df['Time_seconds'].min():.1f} to {df['Time_seconds'].max():.1f} seconds")
    
except Exception as e:
    raise RuntimeError(f"Failed to save output: {e}")