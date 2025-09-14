import pandas as pd

# Step 1: Read your RINEX-like text (assuming it's tab-separated)
df = pd.read_csv("test_RTK1.txt", sep="\t")

# Step 2: Save to CSV
df.to_csv("obs.csv", index=False)