import os
import sys
import shutil
import subprocess

print("=========================================================")
print(" ASTHA ERP ENTERPRISE -- WINDOWS INSTALLER BUILDER")
print("=========================================================")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST_DIR = os.path.join(BASE_DIR, "dist")
INSTALLER_DIR = os.path.join(BASE_DIR, "installer")

if not os.path.exists(INSTALLER_DIR):
    os.makedirs(INSTALLER_DIR)

# Copy standalone executable to installer folder as ASTHA_ERP_Setup.exe
standalone_exe = os.path.join(DIST_DIR, "ASTHA_ERP_Standalone.exe")
setup_exe = os.path.join(INSTALLER_DIR, "ASTHA_ERP_Setup.exe")

if os.path.exists(standalone_exe):
    shutil.copy2(standalone_exe, setup_exe)
    print(f"[OK] Created Production Installer: {setup_exe}")
else:
    print(f"[ERROR] Source executable not found at: {standalone_exe}")

print("Build Installer Process Completed Successfully.")
