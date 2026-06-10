import os
import sys
import subprocess
import shutil
import argparse
import webbrowser

# Target URLs for user guidance
LIBIMOBILE_URL = "https://github.com/libimobiledevice-win32/libimobiledevice-win32/releases"
ITUNES_URL = "https://support.apple.com/en-us/HT210384"
GITHUB_RELEASES_URL = "https://github.com/yourusername/xiCode/releases"
APPLE_DEV_URL = "https://developer.apple.com/download/all/"

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

class XiCodeInstaller:
    def __init__(self):
        self.bundle_id = "com.yourname.xiCode"
        self.ideviceinstaller = shutil.which("ideviceinstaller")
        self.afcclient = shutil.which("afcclient")
        self.idevice_id = shutil.which("idevice_id")
        
        # Locate 7-Zip
        self.seven_zip = shutil.which("7z")
        if not self.seven_zip and os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
            self.seven_zip = r"C:\Program Files\7-Zip\7z.exe"

    def verify_environment(self, needs_7z=False):
        """Checks if required utilities live in the system PATH."""
        clear_terminal()
        print("==================================================")
        print("   XiCode Tool v2.5 - System Environment Check   ")
        print("==================================================")
        print("[*] Inspecting dependencies...")
        
        missing = []
        if not self.ideviceinstaller: missing.append("ideviceinstaller")
        if not self.afcclient: missing.append("afcclient")
        if not self.idevice_id: missing.append("idevice_id")
        if needs_7z and not self.seven_zip: missing.append("7-Zip")

        if missing:
            return self.handle_missing_dependencies(missing, needs_7z)
        
        print("[+] Environment check successful! All tools are ready.")
        return True

    def handle_missing_dependencies(self, missing_list, needs_7z):
        """Interactive rescue wizard for installing missing dependencies."""
        print("\n==================================================")
        print("     ⚠️  MISSING DEPENDENCIES DETECTED  ⚠️")
        print("==================================================")
        print("The following utilities are required to deploy to your iPhone:")
        for item in missing_list:
            print(f"  ❌ {item}")
        print("--------------------------------------------------")

        # Handle 7-Zip via winget
        if "7-Zip" in missing_list:
            print("\n[📦] 7-Zip is required to unwrap Apple .xip archives.")
            choice = input("👉 Install 7-Zip automatically right now via Windows Winget? (y/n): ").strip().lower()
            if choice == 'y':
                print("[*] Requesting 7-Zip from Windows Package Manager (winget)...")
                try:
                    subprocess.run(["winget", "install", "-e", "--id", "7zip.7zip"], check=True)
                    print("[+] 7-Zip successfully installed!")
                    if os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
                        self.seven_zip = r"C:\Program Files\7-Zip\7z.exe"
                        missing_list.remove("7-Zip")
                except Exception as e:
                    print(f"[!] Auto-install failed: {e}. Please install 7-Zip manually.")

        # Handle libimobiledevice package
        ios_usb_missing = any(x in missing_list for x in ["ideviceinstaller", "afcclient", "idevice_id"])
        if ios_usb_missing:
            print("\n[📱] Your system is missing the 'libimobiledevice' iOS USB toolkit.")
            choice = input("👉 Open the GitHub Releases page to download the Windows binaries? (y/n): ").strip().lower()
            if choice == 'y':
                print("[*] Opening browser...")
                webbrowser.open(LIBIMOBILE_URL)
                print("\n💡 HOW TO FIX IT:")
                print("1. Download the latest release zip (e.g., libimobiledevice-win32-x64.zip).")
                print("2. Extract it somewhere memorable (like C:\\libimobiledevice).")
                print("3. Add that directory to your Windows System Environment PATH variables,")
                print("   OR move this 'xicodetool.py' file directly inside that folder.")
                input("\nPress Enter once you have set up the folder to re-scan...")

            print("\n[🔒] Driver Check: If your device fails to link after this, ensure")
            print("     official iTunes is installed so Windows loads Apple's Mobile USB drivers.")
            if input("👉 Need the official iTunes download link? (y/n): ").strip().lower() == 'y':
                webbrowser.open(ITUNES_URL)

        print("\n[*] Refreshing environment layout status...")
        self.ideviceinstaller = shutil.which("ideviceinstaller")
        self.afcclient = shutil.which("afcclient")
        self.idevice_id = shutil.which("idevice_id")
        if not self.seven_zip and os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
            self.seven_zip = r"C:\Program Files\7-Zip\7z.exe"

        still_missing = []
        if not self.ideviceinstaller: still_missing.append("ideviceinstaller")
        if not self.afcclient: still_missing.append("afcclient")
        if not self.idevice_id: still_missing.append("idevice_id")
        if needs_7z and not self.seven_zip: still_missing.append("7-Zip")

        if not still_missing:
            print("[+] Brilliant! All missing linkages repaired successfully.")
            return True
        else:
            print(f"[!] Unable to proceed. Missing dependencies remain: {', '.join(still_missing)}")
            print("Please fix the environment constraints and run the script again.")
            return False

    def check_device_connected(self):
        """Verifies an iOS device is connected and trusted over USB."""
        print("[*] Establishing handshakes with iOS device over USB...")
        try:
            result = subprocess.run([self.idevice_id, "-l"], capture_output=True, text=True, check=True)
            udid = result.stdout.strip()
            if not udid:
                print("[!] ERROR: No iPhone detected. Connect your device via USB and unlock it.")
                return False
            print(f"[+] Found Connected iPhone! (UDID: {udid[:12]}...{udid[-4:]})")
            return True
        except Exception:
            print("[!] ERROR: Failed to communicate with Apple Usbmuxd protocol framework.")
            return False

    def extract_sdk_from_xip(self, xip_path):
        """Extracts the raw iPhoneOS.sdk from a proprietary Apple Xcode .xip file."""
        output_dir = os.path.join(os.path.dirname(os.path.abspath(xip_path)), "Xcode_Decompressed")
        print(f"\n[*] Target extraction sandbox: {output_dir}")
        print("[*] Stage 1: Breaking down outer XAR container...")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            subprocess.run([self.seven_zip, "x", xip_path, f"-o{output_dir}", "-y"], check=True)
            
            content_payload = os.path.join(output_dir, "Content")
            if os.path.exists(content_payload):
                print("[*] Stage 2: Decompressing inner CPIO/Content binary matrix blocks...")
                print("    (This will take several minutes. Grab a coffee... ☕)")
                subprocess.run([self.seven_zip, "x", content_payload, f"-o{output_dir}", "-y"], check=True)

            print("[*] Stage 3: Recursively scanning folders for 'iPhoneOS.sdk' framework mapping...")
            for root, dirs, _ in os.walk(output_dir):
                if "iPhoneOS.sdk" in dirs:
                    discovered_sdk = os.path.join(root, "iPhoneOS.sdk")
                    print(f"[+] SDK harvest complete: {discovered_sdk}")
                    return discovered_sdk
            
            print("[!] ERROR: Decompression successful, but 'iPhoneOS.sdk' was missing from layout.")
            return None
        except Exception as e:
            print(f"[!] Extraction failure on step mapping layout: {e}")
            return None

    def install_base_ipa(self, ipa_path):
        """Deploys the core xiCode IPA package to the connected iOS unit."""
        print(f"\n[*] Step 1/2: Transferring {os.path.basename(ipa_path)} to device environment...")
        try:
            process = subprocess.Popen([self.ideviceinstaller, "--install", ipa_path], 
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"    > {output.strip()}")
            
            if process.returncode == 0:
                print("[+] Step 1 Complete: Base application container mounted.")
                return True
            print("[!] ERROR: Installation protocol dropped by device service handler.")
            return False
        except Exception as e:
            print(f"[!] Exception during app container creation sequence: {e}")
            return False

    def inject_sdk_folder(self, sdk_path):
        """Pushes SDK directories into the app container via Apple File Conduit (AFC)."""
        print(f"\n[*] Step 2/2: Injecting SDK directory into '{self.bundle_id}' sandboxed vault...")
        print("    (Streaming files over USB data pipeline, do not disconnect cable...)")
        try:
            cmd = [self.afcclient, "--documents", self.bundle_id, "put", "-rf", sdk_path, "/"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("[+] Step 2 Complete: SDK fully mirrored into application documents layout.")
                return True
            print(f"[!] ERROR: AFC payload transfer rejected.\nDetails: {result.stderr}")
            return False
        except Exception as e:
            print(f"[!] Exception thrown during USB file-sharing transfer stream: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="xiCode Deployment & Extraction Manager Engine")
    parser.add_argument("--ipa", help="Path to custom xiCode.ipa binary")
    parser.add_argument("--sdk", help="Path to custom iPhoneOS.sdk folder or raw Xcode.xip package")
    args = parser.parse_args()

    installer = XiCodeInstaller()

    # --- Interactive Wizard Architecture ---
    if not args.ipa:
        print("\n[💡] Missing IPA parameter details.")
        print("     Leave blank if you need to fetch the application from GitHub Releases.")
        user_ipa = input("👉 Enter local file path to 'xiCode.ipa' (or press Enter to visit GitHub): ").strip().strip('"')
        if not user_ipa:
            print(f"[*] Dispatching system web portal hook to: {GITHUB_RELEASES_URL}")
            webbrowser.open(GITHUB_RELEASES_URL)
            user_ipa = input("👉 Enter the local file path once downloaded from releases: ").strip().strip('"')
        args.ipa = user_ipa

    using_xip = False
    if not args.sdk:
        print("\n[💡] Missing SDK parameter details.")
        print("    1. I already have a loose extracted 'iPhoneOS.sdk' folder library.")
        print("    2. I have a clean, raw 'Xcode.xip' archive downloaded from Apple.")
        choice = input("👉 Select your asset source configuration option (1 or 2): ").strip()
        
        if choice == "2":
            user_sdk = input("👉 Enter file path to 'Xcode.xip' (or press Enter to download via Apple): ").strip().strip('"')
            if not user_sdk:
                print(f"[*] Routing to official Apple Developer Downloads archive portal: {APPLE_DEV_URL}")
                webbrowser.open(APPLE_DEV_URL)
                user_sdk = input("👉 Enter the local path to 'Xcode.xip' once downloaded: ").strip().strip('"')
            using_xip = True
        else:
            user_sdk = input("👉 Enter local file directory path to 'iPhoneOS.sdk': ").strip().strip('"')
        args.sdk = user_sdk
    elif args.sdk.lower().endswith('.xip'):
        using_xip = True

    # Validate parameters aren't completely empty strings
    if not args.ipa or not args.sdk:
        print("\n[!] Target assets definition invalid or cancelled. Installer aborting.")
        sys.exit(1)

    # --- Pipeline Execution Sequence ---
    if not installer.verify_environment(needs_7z=using_xip):
        sys.exit(1)
    if not installer.check_device_connected():
        sys.exit(1)

    # Extract XIP if required
    final_sdk_path = args.sdk
    if using_xip:
        final_sdk_path = installer.extract_sdk_from_xip(args.sdk)
        if not final_sdk_path:
            print("[!] Failed to obtain uncompressed SDK framework targets. Aborting pipeline.")
            sys.exit(1)

    # Execution Phase (Install IPA first, then inject documents assets)
    print("\n==================================================")
    print("        🚀 STARTING SETUP MOUNT SEQUENCER         ")
    print("==================================================")
    
    if not installer.install_base_ipa(args.ipa):
        print("[!] Execution pipeline broken at step 1.")
        sys.exit(1)
        
    if not installer.inject_sdk_folder(final_sdk_path):
        print("[!] Execution pipeline broken at step 2.")
        sys.exit(1)

    print("\n==================================================")
    print("   🎉 SUCCESS: xiCode Environment Online! 🎉")
    print("==================================================")
    print("Deployment finished successfully. Your workspace parameters are fully loaded.")
    print("You may safely detach the USB connection cable.")
    print("==================================================\n")

if __name__ == "__main__":
    main()