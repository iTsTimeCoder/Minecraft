import os
import sys
import json
import subprocess
import time
import shutil
import minecraft_launcher_lib

# ألوان التيرمنال (مدعومة بالكامل في لينكس)
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"
C_WHITE = "\033[37m"

# استخدام مجلد المنزل (Home Directory) في لينكس
home_path = os.path.expanduser('~')
minecraft_directory = os.path.join(home_path, ".mylauncher")
config_path = os.path.join(minecraft_directory, "launcher_config.json")
logs_directory = os.path.join(minecraft_directory, "logs")

os.makedirs(minecraft_directory, exist_ok=True)
os.makedirs(logs_directory, exist_ok=True)

def load_settings():
    default_settings = {
        "username": "Player",
        "version": "1.16.5",
        "max_ram": 2048
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_settings
    return default_settings

def save_settings(settings):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except:
        pass

def clear_console():
    os.system('clear')

def set_status(status: str):
    print(f"{C_YELLOW}[Status]{C_RESET} {status}")

def set_progress(progress: int):
    pass

def is_version_installed(version_id):
    version_jar = os.path.join(minecraft_directory, "versions", version_id, f"{version_id}.jar")
    return os.path.exists(version_jar)

def install_version_with_retry(version_id, attempts=5):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                version=version_id,
                minecraft_directory=minecraft_directory,
                callback={"setStatus": set_status, "setProgress": set_progress}
            )
            return True
        except Exception as e:
            last_error = e
            print(f"{C_YELLOW}[Retry {attempt}/{attempts}] Download interrupted ({e}). Retrying in 3 seconds...{C_RESET}")
            if attempt < attempts:
                time.sleep(3)
    print(f"{C_RED}Installation failed after {attempts} attempts: {last_error}{C_RESET}")
    return False

def get_system_ram_suggestion():
    try:
        # قراءة حجم الرام الكلي في لينكس
        total_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        total_gb = round(total_bytes / (1024 ** 3))
        
        if total_gb <= 4:
            suggested_mb = 2048
        elif total_gb <= 8:
            suggested_mb = 4096
        elif total_gb <= 16:
            suggested_mb = 6144
        else:
            suggested_mb = 8192
        return total_gb, suggested_mb
    except:
        return 8, 4096

def find_java_executable(version_id):
    runtime_dir = os.path.join(minecraft_directory, "runtime")
    
    if os.path.exists(runtime_dir):
        runtimes = ["java-runtime-epsilon", "java-runtime-delta", "java-runtime-gamma", "java-runtime-beta", "jre-legacy"]
        
        for rt in runtimes:
            rt_path = os.path.join(runtime_dir, rt)
            if os.path.exists(rt_path):
                for root, dirs, files in os.walk(rt_path):
                    if "java" in files:
                        return os.path.join(root, "java")

        for root, dirs, files in os.walk(runtime_dir):
            if "java" in files:
                return os.path.join(root, "java")
                
    return "java"

def change_version(settings):
    clear_console()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}          MINECRAFT VERSIONS            {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_GREEN}Local Installed Versions:{C_RESET}")
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        if installed_versions:
            for v in installed_versions:
                print(f"  {C_WHITE}- {v['id']}{C_RESET}")
        else:
            print(f"  {C_RED}No local versions found.{C_RESET}")
    except:
        print(f"  {C_RED}Could not read local versions.{C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_WHITE}[1]{C_RESET} Releases (Stable)")
    print(f" {C_WHITE}[2]{C_RESET} Snapshots (Experimental)")
    print(f" {C_WHITE}[3]{C_RESET} Type Version ID Manually")
    print(f"{C_CYAN}========================================{C_RESET}")
    choice = input(f" {C_GREEN}Select an option (1-3):{C_RESET} ").strip()

    new_ver = ""
    if choice in ("1", "2"):
        ver_type = "release" if choice == "1" else "snapshot"
        clear_console()
        print(f"{C_CYAN}Fetching {ver_type} versions from Mojang servers...{C_RESET}")
        try:
            version_list = minecraft_launcher_lib.utils.get_version_list()
            ids = [v["id"] for v in version_list if v["type"] == ver_type]
        except Exception as e:
            print(f"{C_RED}Failed to fetch versions: {e}{C_RESET}")
            input("\nPress Enter to return...")
            return
        if not ids:
            print(f"{C_RED}No {ver_type} versions found.{C_RESET}")
            input("\nPress Enter to return...")
            return

        filter_text = input(f" {C_GREEN}Filter (e.g., 1.20 or 26.2) [Enter = show all]:{C_RESET} ").strip().lower()
        if filter_text:
            ids = [v for v in ids if filter_text in v.lower()]
        if not ids:
            print(f"{C_RED}No versions match your filter.{C_RESET}")
            input("\nPress Enter to return...")
            return

        print(f"\n{C_CYAN}Available versions ({len(ids)}):{C_RESET}")
        shown = ids[:100]
        for idx, vid in enumerate(shown):
            print(f"  {C_WHITE}[{idx + 1}]{C_RESET} {vid}")
        if len(ids) > len(shown):
            print(f"  {C_YELLOW}... and {len(ids) - len(shown)} more (use the filter to narrow down){C_RESET}")

        sel = input(f"\n {C_GREEN}Select a version number (1-{len(shown)}):{C_RESET} ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(shown):
            new_ver = shown[int(sel) - 1]
        else:
            print(f"{C_RED}Invalid selection.{C_RESET}")
            input("\nPress Enter to return...")
            return
    else:
        new_ver = input(f" {C_GREEN}Enter Version ID (e.g., 1.16.5, 26.2):{C_RESET} ").strip()

    if new_ver:
        settings["version"] = new_ver
        save_settings(settings)
        print(f"\n{C_CYAN}Selected version:{C_RESET} {C_YELLOW}{new_ver}{C_RESET}")
        if not is_version_installed(new_ver):
            print(f"{C_YELLOW}Version not installed. Downloading automatically (auto-retry enabled)...{C_RESET}")
            if install_version_with_retry(new_ver):
                print(f"{C_GREEN}Version {new_ver} installed successfully!{C_RESET}")
            else:
                print(f"{C_RED}Installation could not be completed due to network issues.{C_RESET}")
                print(f"{C_YELLOW}Don't worry: the launcher will retry the download automatically when you press 'Launch'.{C_RESET}")
        else:
            print(f"{C_GREEN}Version already installed. Ready to launch.{C_RESET}")
    input("\nPress Enter to return...")

def change_ram(settings):
    clear_console()
    total_pc_ram, dynamic_suggestion = get_system_ram_suggestion()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}           RAM ALLOCATION               {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_WHITE}Your System Total RAM:{C_RESET} {C_GREEN}{total_pc_ram} GB{C_RESET}")
    print(f" {C_WHITE}AI Optimized Suggestion:{C_RESET} {C_CYAN}{dynamic_suggestion} MB{C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_YELLOW}Examples: 2048 MB (2GB) | 3072 MB (3GB) | 4096 MB (4GB){C_RESET}")
    print(f"{C_CYAN}----------------------------------------{C_RESET}")
    
    new_ram = input(f" {C_GREEN}Enter Max RAM size in MB [Leave empty for suggestion]:{C_RESET} ").strip()
    
    if new_ram.isdigit():
        ram_val = int(new_ram)
        
        if ram_val < 32:
            print(f"\n{C_YELLOW}[!] Detected GB notation. Automatically converting {ram_val}GB to {ram_val * 1024}MB...{C_RESET}")
            ram_val = ram_val * 1024
            time.sleep(1.5)
            
        if ram_val >= (total_pc_ram * 1024):
            print(f"\n{C_RED}[Warning] You are allocating ALL or MORE than your system RAM. Your OS might crash!{C_RESET}")
            confirm = input(" Are you sure you want to keep this setting? (y/n): ").strip().lower()
            if confirm != 'y':
                return

        settings["max_ram"] = ram_val
        save_settings(settings)
    elif not new_ram:
        settings["max_ram"] = dynamic_suggestion
        save_settings(settings)

def install_local_jar():
    clear_console()
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}        MANUAL MODLOADER/JAR FILE       {C_RESET}")
    print(f"{C_CYAN}========================================{C_RESET}")
    print(f" {C_WHITE}Official Download Links:{C_RESET}")
    print(f" - OptiFine: {C_YELLOW}https://optifine.net/downloads{C_RESET}")
    print(f" - Forge:    {C_YELLOW}https://files.minecraftforge.net{C_RESET}")
    print(f"{C_CYAN}----------------------------------------{C_RESET}")
    
    print(f"\n{C_CYAN}Scanning for .jar files next to the launcher script...{C_RESET}")
    jar_files = [f for f in os.listdir('.') if f.endswith('.jar')]
    
    if not jar_files:
        print(f"{C_RED}No .jar files found! Please drop your OptiFine/Forge .jar file right next to this python script and try again.{C_RESET}")
        input("\nPress Enter to return...")
        return
    
    print(f"\n{C_GREEN}Found the following files:{C_RESET}")
    for idx, jar in enumerate(jar_files):
        print(f" [{idx + 1}] {jar}")
        
    f_choice = input(f"\nSelect the file to install (1-{len(jar_files)}): ").strip()
    if not f_choice.isdigit() or int(f_choice) < 1 or int(f_choice) > len(jar_files):
        print(f"{C_RED}Invalid Selection.{C_RESET}")
        input("\nPress Enter to return...")
        return
        
    selected_jar = jar_files[int(f_choice) - 1]
    
    print(f"\n{C_WHITE}Selected File:{C_RESET} {C_YELLOW}{selected_jar}{C_RESET}")
    custom_name = input(f" {C_GREEN}Enter Custom Profile Name (Leave empty for default name):{C_RESET} ").strip()
    
    versions_dir = os.path.join(minecraft_directory, "versions")
    os.makedirs(versions_dir, exist_ok=True)
    old_versions = set(os.listdir(versions_dir))
    
    print(f"\n{C_CYAN}Starting official installer process...{C_RESET}")
    try:
        java_executable = find_java_executable()
        
        if java_executable == "java":
            try:
                subprocess.run(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print(f"\n{C_RED}Error: Java could not be detected on your Linux system!{C_RESET}")
                print(f"{C_YELLOW}Please install Java (e.g., sudo apt install default-jre) or launch a Vanilla version first.{C_RESET}")
                input("\nPress Enter to continue...")
                return

        if "optifine" in selected_jar.lower():
            print(f"{C_YELLOW}Opening OptiFine GUI window. The launcher path has been filled automatically. Just click 'Install'.{C_RESET}")
            subprocess.run([java_executable, "-jar", selected_jar, minecraft_directory])
        else:
            print(f"{C_YELLOW}Installing Forge client silently... Please wait.{C_RESET}")
            subprocess.run([java_executable, "-jar", selected_jar, "--installClient", minecraft_directory])
            
        new_versions = set(os.listdir(versions_dir))
        added_versions = new_versions - old_versions
        
        if added_versions:
            detected_version = list(added_versions)[0]
            if custom_name:
                old_folder_path = os.path.join(versions_dir, detected_version)
                new_folder_path = os.path.join(versions_dir, custom_name)
                
                if os.path.exists(new_folder_path):
                    shutil.rmtree(new_folder_path)
                os.rename(old_folder_path, new_folder_path)
                
                old_json_path = os.path.join(new_folder_path, f"{detected_version}.json")
                new_json_path = os.path.join(new_folder_path, f"{custom_name}.json")
                if os.path.exists(old_json_path):
                    os.rename(old_json_path, new_json_path)
                    with open(new_json_path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                    json_data["id"] = custom_name
                    with open(new_json_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                print(f"\n{C_GREEN}Successfully installed and renamed to profile: {custom_name}{C_RESET}")
            else:
                print(f"\n{C_GREEN}Successfully installed profile: {detected_version}{C_RESET}")
        else:
            print(f"\n{C_RED}Installation completed, but no profile folder was generated. Ensure you clicked 'Install' or the jar file is correct.{C_RESET}")
    except Exception as e:
        print(f"\n{C_RED}An error occurred during installation: {e}{C_RESET}")
    input("\nPress Enter to continue...")

def install_modloaders(settings):
    while True:
        clear_console()
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f"{C_BOLD}{C_MAGENTA}         MOD LOADERS INSTALLER          {C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f" Target Version: {C_GREEN}{settings['version']}{C_RESET}")
        print(f"{C_CYAN}----------------------------------------{C_RESET}")
        print(f" {C_WHITE}[1]{C_RESET} Install {C_CYAN}Fabric{C_RESET} (Automatic)")
        print(f" {C_WHITE}[2]{C_RESET} Install {C_CYAN}Forge{C_RESET} (Automatic)")
        print(f" {C_WHITE}[3]{C_RESET} Install {C_CYAN}Local Jar / OptiFine{C_RESET} (Manual)")
        print(f" {C_WHITE}[4]{C_RESET} Back to Main Menu{C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        
        choice = input(f" {C_GREEN}Select an option (1-4):{C_RESET} ").strip()
        
        if choice == "1":
            clear_console()
            print(f"{C_CYAN}Step 1/2:{C_RESET} Verifying base vanilla files for {settings['version']}...")
            try:
                if not is_version_installed(settings["version"]):
                    install_version_with_retry(settings["version"])
                
                print(f"\n{C_CYAN}Step 2/2:{C_RESET} Fetching and installing latest Fabric loader...")
                minecraft_launcher_lib.fabric.install_fabric(settings["version"], minecraft_directory, callback={"setStatus": set_status, "setProgress": set_progress})
                
                print(f"\n{C_GREEN}Fabric successfully installed!{C_RESET}")
                print("Go to 'Select Version' in main menu to switch to the Fabric profile.")
            except Exception as e:
                print(f"\n{C_RED}Fabric installation failed: {e}{C_RESET}")
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            clear_console()
            print(f"{C_CYAN}Step 1/2:{C_RESET} Verifying base vanilla files for {settings['version']}...")
            try:
                if not is_version_installed(settings["version"]):
                    install_version_with_retry(settings["version"])
                
                print(f"\n{C_CYAN}Step 2/2:{C_RESET} Searching available Forge versions for {settings['version']}...")
                forge_version = minecraft_launcher_lib.forge.find_forge_version(settings["version"])
                if forge_version:
                    print(f"Found Forge ID: {C_YELLOW}{forge_version}{C_RESET}. Downloading installer components...")
                    minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_directory, callback={"setStatus": set_status, "setProgress": set_progress})
                    print(f"\n{C_GREEN}Forge successfully installed!{C_RESET}")
                    print("Go to 'Select Version' in main menu to switch to the Forge profile.")
                else:
                    print(f"\n{C_RED}No official Forge release found for version {settings['version']}.{C_RESET}")
            except Exception as e:
                print(f"\n{C_RED}Forge installation failed: {e}{C_RESET}")
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            install_local_jar()
            
        elif choice == "4":
            break

def show_error_dialog(title, message):
    # محاولة استخدام أدوات واجهة لينكس لعرض الخطأ، وإلا طباعته في التيرمنال
    try:
        subprocess.run(['zenity', '--error', '--title', title, '--text', message], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        try:
            subprocess.run(['kdialog', '--error', message, '--title', title], stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print(f"\n{C_RED}[{title}] {message}{C_RESET}")
            input("Press Enter to continue...")

def main():
    settings = load_settings()

    while True:
        clear_console()
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f"{C_BOLD}{C_MAGENTA}          LAUNCHER CONFIGURATION        {C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        print(f" {C_WHITE}[1]{C_RESET} {C_GREEN}Launch Minecraft{C_RESET}  ({settings['version']})")
        print(f" {C_WHITE}[2]{C_RESET} Edit Username     (Current: {C_YELLOW}{settings['username']}{C_RESET})")
        print(f" {C_WHITE}[3]{C_RESET} Select Version    (Current: {C_YELLOW}{settings['version']}{C_RESET})")
        print(f" {C_WHITE}[4]{C_RESET} Allocate RAM      (Current: {C_YELLOW}{settings['max_ram']} MB{C_RESET})")
        print(f" {C_WHITE}[5]{C_RESET} Install Mod Loader(Forge/Fabric/OptiFine)")
        print(f" {C_WHITE}[6]{C_RESET} {C_RED}Exit{C_RESET}")
        print(f"{C_CYAN}========================================{C_RESET}")
        
        choice = input(f" {C_GREEN}Select an option (1-6):{C_RESET} ").strip()

        if choice == "1":
            clear_console()
            
            try:
                if not is_version_installed(settings["version"]):
                    print(f"{C_YELLOW}Files missing or first time launch. Downloading game files...{C_RESET}")
                    install_version_with_retry(settings["version"])
                else:
                    print(f"{C_GREEN}Game files verified successfully. Preparing to launch...{C_RESET}")
                
                options = {
                    "username": settings["username"],
                    "uuid": "",
                    "token": "",
                    "jvmArguments": [f"-Xmx{settings['max_ram']}M", "-Xms512M"],
                    "executablePath": find_java_executable()
                }
                
                launch_command = minecraft_launcher_lib.command.get_minecraft_command(
                    version=settings["version"],
                    minecraft_directory=minecraft_directory,
                    options=options
                )
                
                log_path = os.path.join(logs_directory, "game_output.log")
                log_file = open(log_path, "w", encoding="utf-8")
                
                print(f"\n{C_CYAN}Launching Minecraft...{C_RESET}")
                
                # تشغيل اللعبة في لينكس ببساطة بدون قيود النوافذ المخفية الخاصة بالويندوز
                process = subprocess.Popen(
                    launch_command, 
                    stdout=log_file, 
                    stderr=log_file
                )
                
                time.sleep(3)
                
                if process.poll() is not None:
                    log_file.close()
                    error_msg = "Minecraft crashed instantly on startup!"
                    try:
                        with open(log_path, "r", encoding="utf-8") as f:
                            errors = f.read()
                            if errors:
                                error_msg += f"\n\nDetails:\n{errors[:500]}"
                    except:
                        pass
                    
                    show_error_dialog("Launch Error", error_msg)
                else:
                    sys.exit(0)
                    
            except Exception as e:
                print(f"\n{C_RED}An error occurred: {e}{C_RESET}")
                input("\nPress Enter to return to menu...")

        elif choice == "2":
            clear_console()
            new_user = input(f" {C_GREEN}Enter new username:{C_RESET} ").strip()
            if new_user:
                settings["username"] = new_user
                save_settings(settings)

        elif choice == "3":
            change_version(settings)

        elif choice == "4":
            change_ram(settings)
            
        elif choice == "5":
            install_modloaders(settings)

        elif choice == "6":
            sys.exit(0)

if __name__ == "__main__":
    main()