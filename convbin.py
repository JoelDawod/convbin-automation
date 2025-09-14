import subprocess
from pathlib import Path
import time

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
    verify_rinex_version(out_dir)

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

# Example usage
if __name__ == "__main__":
    convbin_path = r"convbin.exe"
    
    # First check the version
    check_convbin_version(convbin_path)
    
    # Then perform conversion
    files = ubx_to_rinex(
        r"20240214-041908.UBX",
        r"rinex_out",
        convbin_path
    )
    print("Generated files:", [f.name for f in files])