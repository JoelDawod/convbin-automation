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

        row = {"Time_seconds": time_sec, "SatelliteID": sat_id}
        
        # Process all observations
        for obs_name, obs_data in observations.items():
            # From debug output, observations have keys like 'C2I_value', 'C2I_ssi', etc.
            # We want to extract the main measurement values (those ending with '_value')
            if obs_name.endswith('_value'):
                # Get the base observation type (e.g., 'C2I' from 'C2I_value')
                base_name = obs_name[:-6]  # Remove '_value' suffix
                row[base_name] = obs_data
                
                # Also include signal strength if available
                ssi_key = f"{base_name}_ssi"
                if ssi_key in observations:
                    row[f"{base_name}_SSI"] = observations[ssi_key]
                
                # Also include LLI if available
                lli_key = f"{base_name}_lli"
                if lli_key in observations:
                    row[f"{base_name}_LLI"] = observations[lli_key]
        
        rows.append(row)

# Build DataFrame
if not rows:
    # More detailed debugging
    print("\n=== DEBUG INFORMATION ===")
    print(f"Number of epochs: {len(rnx_parser.rinex_reader.rinex_epochs)}")
    
    if rnx_parser.rinex_reader.rinex_epochs:
        first_epoch = rnx_parser.rinex_reader.rinex_epochs[0]
        print(f"First epoch type: {type(first_epoch)}")
        print(f"First epoch timestamp: {getattr(first_epoch, 'timestamp', 'Not found')}")
        print(f"First epoch satellites: {len(getattr(first_epoch, 'satellites', []))}")
        
        if hasattr(first_epoch, 'satellites') and first_epoch.satellites:
            first_sat = first_epoch.satellites[0]
            print(f"First satellite type: {type(first_sat)}")
            print(f"First satellite content: {first_sat}")
    
    raise RuntimeError("No data parsed - check file format and attribute names")

df = pd.DataFrame(rows)

# Reorder columns with Time_seconds and SatelliteID first
cols = ["Time_seconds", "SatelliteID"] + [col for col in df.columns 
                                         if col not in ["Time_seconds", "SatelliteID"]]
df = df[cols]

# Save to file
try:
    df.to_csv("rinex_output.txt", sep="\t", index=False, float_format='%.6f')
    print(f"✅ Saved {len(df)} rows to rinex_output.txt")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample data:\n{df.head()}")
    
    # Additional info about the data
    print(f"\n📊 Data summary:")
    print(f"Total GPS satellites found: {df['SatelliteID'].nunique()}")
    print(f"GPS satellite IDs: {sorted(df['SatelliteID'].unique())}")
    print(f"Time range: {df['Time_seconds'].min():.1f} to {df['Time_seconds'].max():.1f} seconds")
    
except Exception as e:
    raise RuntimeError(f"Failed to save output: {e}")