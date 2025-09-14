import georinex as gr
import pandas as pd

# Input RINEX observation file
filename = r"./rinex_out/20240214-041908.obs"

# Read RINEX data (xarray Dataset)
obs = gr.load(filename)

# Keep only GPS observations
gps = obs.sel(sv=[sv for sv in obs.sv.values if sv.startswith("G")])

# Convert to DataFrame
df = gps.to_dataframe().reset_index()

# Extract relevant columns (C1C, L1C, D1C, S1C)
df = df[["time", "sv", "C1C", "L1C", "D1C", "S1C"]]

# Convert 'sv' (e.g., 'G12') → SatelliteID = 12
df["SatelliteID"] = df["sv"].str[1:].astype(int)

# Convert time to total seconds
df["Time_seconds"] = (
    df["time"].dt.hour * 3600
    + df["time"].dt.minute * 60
    + df["time"].dt.second
)

# Reorder columns
df = df[["Time_seconds", "SatelliteID", "C1C", "L1C", "D1C", "S1C"]]

# Save as tab-delimited file
df.to_csv("test_RTK1.txt", sep="\t", index=False)