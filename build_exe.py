import os
import subprocess
import sys

def build_standalone_exe():
    print("============================================================")
    print("  ASTHA ERP — Building Standalone Windows Executable (.exe)")
    print("============================================================")

    # PyInstaller arguments
    # Bundles templates and API services into a single executable folder
    templates_src = os.path.join("services", "api", "app", "templates")
    templates_target = os.path.join("services", "api", "app", "templates")
    
    add_data_arg = f"{templates_src};{templates_target}"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=ASTHA_ERP",
        f"--add-data={add_data_arg}",
        "desktop_app.py"
    ]

    print(f"Executing build command: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    
    if res.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", "ASTHA_ERP", "ASTHA_ERP.exe"))
        print("\n============================================================")
        print("  BUILD SUCCESSFUL!")
        print(f"  Windows Desktop Executable Created At:")
        print(f"  {exe_path}")
        print("============================================================")
    else:
        print("\n[Build Error] PyInstaller failed to compile executable.")

if __name__ == "__main__":
    build_standalone_exe()
