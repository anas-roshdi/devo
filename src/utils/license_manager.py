import subprocess
import hashlib

def get_device_fingerprint():
    """
    Retrieves a unique hardware ID (HWID) based on the motherboard's UUID,
    then hashes it for security and standard formatting.
    """
    try:
        # Run Windows command to get the motherboard UUID
        result = subprocess.check_output('wmic csproduct get uuid', shell=True)
        raw_uuid = result.decode('utf-8').split('\n')[1].strip()
        
        # Hash the raw UUID using SHA-256 to create a clean, uniform HWID
        hashed_uuid = hashlib.sha256(raw_uuid.encode()).hexdigest()
        
        # Return the first 16 characters in uppercase for readability
        # Example output: "A1B2C3D4E5F67890"
        return hashed_uuid[:16].upper()
        
    except Exception as e:
        # Fallback error handling if the command fails
        return f"ERROR_HWID"

# Simple test block to run directly
if __name__ == "__main__":
    hwid = get_device_fingerprint()
    print("-" * 30)
    print("Device Fingerprint (HWID):", hwid)
    print("-" * 30)