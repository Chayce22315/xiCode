import os
import sys
import subprocess
import shutil
import argparse
import webbrowser

# Target URLs for user guidance
GITHUB_RELEASES_URL = "https://github.com/Chayce22315/xiCode/releases"
APPLE_DEV_URL = "https://developer.apple.com/download/all/"
ITUNES_URL = "https://support.apple.com/en-us/HT210384"

# MSYS2 Pathing configuration
MSYS2_BIN = r"C:\msys64\ucrt64\bin"

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

class XiCodeInstaller:
    def __init__(self):
        self.bundle_id = "com.pixelatedstudios.xiCode"
        # Prioritize MSYS2 local toolchain binaries, then check global PATH
        self.bin_dirs = [MSYS2_BIN] if os.path.exists(MSYS2_BIN) else []
        
        self.ideviceinstaller = self._find_tool("ideviceinstaller")
        self.afcclient = self._find_tool("afcclient")
        self.idevice_id = self._find_tool("idevice_id")
        
        # Locate 7-Zip
        self.seven_zip = shutil.which("7z")
        if not self.seven_zip and os.path.exists(r"C:\Program Files\7-Zip\7z.exe"):
            self.seven_zip = r"C:\Program Files\7-Zip\7z.exe"

    def _find_tool(self, name):
        """Locates binary paths seamlessly across environments."""
        for d in self.bin_dirs:
            path = os.path.join(d, f"{name}.exe")
            if os.path.exists(path): 
                return path
        return shutil.which(name)

    def verify_environment(self, needs_7z=False):
        """Checks if required utilities live locally or in system environments."""
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
            print("\n==================================================")
            print("     ⚠️  MISSING DEPENDENCIES DETECTED  ⚠️")
            print("==================================================")
            print("The following utilities are required to deploy to your iPhone:")
            for item in missing: # Fixed: changed from missing_list to missing
                print(f"  ❌ {item}")
            print("-" * 50)
            print(f"[!] Please ensure MSYS2 is installed and tools are in: {MSYS2_BIN}")
            print("[!] Or add the folder containing these .exe files to your PATH.")
            return False
        
        print("[+] Environment check successful! All tools are ready.")
        return True

    def check_device_connected(self):
        """Verifies an iOS device is connected and trusted over USB."""
        print("[*] Establishing handshakes with iOS device over USB...")
        try:
            # Use self.idevice_id which contains the full path
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

    # --- Interactive Wizard Interface ---
    if not args.ipa:
        print("\n[💡] Missing IPA parameter details.")
        user_ipa = input("👉 Enter local file path to 'xiCode.ipa' (or press Enter to visit GitHub): ").strip().strip('"')
        if not user_ipa:
            webbrowser.open(GITHUB_RELEASES_URL)
            user_ipa = input("👉 Enter the local file path once downloaded: ").strip().strip('"')
        args.ipa = user_ipa

    using_xip = False
    if not args.sdk:
        print("\n[💡] Missing SDK parameter details.")
        print("    1. I have an extracted 'iPhoneOS.sdk' folder.")
        print("    2. I have a 'Xcode.xip' archive.")
        choice = input("👉 Select option (1 or 2): ").strip()
        
        if choice == "2":
            user_sdk = input("👉 Path to 'Xcode.xip': ").strip().strip('"')
            if not user_sdk:
                webbrowser.open(APPLE_DEV_URL)
                user_sdk = input("👉 Enter local path to 'Xcode.xip' once downloaded: ").strip().strip('"')
            using_xip = True
        else:
            user_sdk = input("👉 Path to 'iPhoneOS.sdk' folder: ").strip().strip('"')
        args.sdk = user_sdk
    elif args.sdk.lower().endswith('.xip'):
        using_xip = True

    if not args.ipa or not args.sdk:
        print("\n[!] Path invalid. Aborting.")
        sys.exit(1)

    # --- Execution ---
    if not installer.verify_environment(needs_7z=using_xip):
        sys.exit(1)
    if not installer.check_device_connected():
        sys.exit(1)

    final_sdk_path = args.sdk
    if using_xip:
        final_sdk_path = installer.extract_sdk_from_xip(args.sdk)
        if not final_sdk_path:
            sys.exit(1)

    print("\n==================================================")
    print("        🚀 STARTING SETUP MOUNT SEQUENCER         ")
    print("==================================================")
    
    if installer.install_base_ipa(args.ipa):
        if installer.inject_sdk_folder(final_sdk_path):
            print("\n==================================================")
            print("   🎉 SUCCESS: xiCode Environment Online! 🎉")
            print("==================================================")

if __name__ == "__main__":
    main()