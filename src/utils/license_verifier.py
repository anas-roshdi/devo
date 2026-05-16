import os
import sys
import tkinter as tk
from tkinter import messagebox
import hashlib
import subprocess

# CRITICAL: This must exactly match the generator's salt
SECRET_SALT = "Devo_Pro_Edition_2026_@Secure!_anas"
LICENSE_FILE = "license.dat" # The file where the valid key will be saved

def get_device_fingerprint():
    """Retrieves the hardware ID."""
    try:
        result = subprocess.check_output('wmic csproduct get uuid', shell=True)
        raw_uuid = result.decode('utf-8').split('\n')[1].strip()
        hashed_uuid = hashlib.sha256(raw_uuid.encode()).hexdigest()
        return hashed_uuid[:16].upper()
    except Exception:
        return "ERROR_HWID"

def verify_key(hwid, key):
    """Validates if the provided key matches the HWID."""
    combined = hwid + SECRET_SALT
    expected_hash = hashlib.sha256(combined.encode()).hexdigest().upper()
    raw_key = expected_hash[:16]
    expected_key = f"{raw_key[:4]}-{raw_key[4:8]}-{raw_key[8:12]}-{raw_key[12:16]}"
    return key.strip() == expected_key

def is_licensed():
    """Checks if a valid license file already exists."""
    if not os.path.exists(LICENSE_FILE):
        return False
    
    with open(LICENSE_FILE, "r") as f:
        saved_key = f.read().strip()
        
    hwid = get_device_fingerprint()
    return verify_key(hwid, saved_key)

def show_license_screen():
    """Displays the activation GUI if not licensed."""
    root = tk.Tk()
    root.title("Devo - System Activation")
    root.geometry("450x250")
    
    # Center the window
    root.eval('tk::PlaceWindow . center')
    
    hwid = get_device_fingerprint()
    
    tk.Label(root, text="Welcome to Devo System", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(root, text="Please send this HWID to the developer to get your key:", font=("Arial", 10)).pack()
    
    # Entry for HWID (Read-only so client can copy it)
    hwid_entry = tk.Entry(root, font=("Arial", 12, "bold"), justify="center")
    hwid_entry.insert(0, hwid)
    hwid_entry.config(state="readonly")
    hwid_entry.pack(pady=5, fill="x", padx=40)
    
    tk.Label(root, text="Enter License Key here:", font=("Arial", 10)).pack(pady=5)
    
    # Entry for License Key
    key_entry = tk.Entry(root, font=("Arial", 12), justify="center")
    key_entry.pack(pady=5, fill="x", padx=40)
    
    def check_and_activate():
        """Handles the activation button click."""
        entered_key = key_entry.get().strip()
        if verify_key(hwid, entered_key):
            # Save the valid key to a hidden file
            with open(LICENSE_FILE, "w") as f:
                f.write(entered_key)
            
            # Hide the file in Windows (Optional but professional)
            if os.name == 'nt':
                os.system(f'attrib +h {LICENSE_FILE}')
                
            messagebox.showinfo("Success", "System Activated Successfully! Thank you.")
            root.destroy()
        else:
            messagebox.showerror("Error", "Invalid License Key!")

    tk.Button(root, text="Activate", command=check_and_activate, bg="#28a745", fg="white", font=("Arial", 12, "bold")).pack(pady=15)
    
    root.mainloop()
    
    # Return whether it's licensed after the window is closed
    return is_licensed()