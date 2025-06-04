import subprocess
from concurrent.futures import ThreadPoolExecutor
import time

# 掃描網段設定
ip_base = "140.127.45."
ip_range = [f"{ip_base}{i}" for i in range(1, 255)]

# ping 單一 IP（靜音）
def ping(ip):
    result = subprocess.run(
        f"ping -n 1 -w 50 {ip}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return ip if result.returncode == 0 else None

# 取得目前 ARP 表（cp950 適用繁中 Windows）
def get_arp_table():
    try:
        output = subprocess.check_output("arp -a", shell=True, encoding="cp950")
        return output.splitlines()
    except Exception as e:
        print(f"Failed to read ARP table: {e}")
        return []

# 統一處理 MAC 格式（小寫＋冒號轉破折號）
def normalize_mac(mac_raw):
    return mac_raw.strip().lower().replace(":", "-")

def main():
    print("📡 Scanning network, please wait...")
    start = time.time()

    with ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(ping, ip_range))

    alive_ips = [ip for ip in results if ip]
    print(f"\n✅ Active IPs ({len(alive_ips)} found):")
    #for ip in alive_ips:
        #print(f"  {ip}")

    arp_lines = get_arp_table()
    mac_input = normalize_mac(input("\n🔎 Enter MAC address (e.g. 8C:CE:4E:A5:93:34): "))

    print("\n🔍 Search Result:")
    found = False
    for line in arp_lines:
        line = line.strip()
        if '-' not in line or line.lower().startswith("interface"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            mac = normalize_mac(parts[1])
            if mac == mac_input:
                print("  " + line)
                found = True

    if not found:
        print("  ⚠️ MAC not found in ARP table. Make sure the device is online.")

    print(f"\n⏱️ Done in {time.time() - start:.2f} seconds.")

if __name__ == "__main__":
    main()
