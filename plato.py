import pymem
import pymem.process
import psutil
from pymem.ressources.structure import MEMORY_BASIC_INFORMATION
import ctypes

def get_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if name.lower() in proc.info['name'].lower():
            return proc.info['pid']
    return None

def scan_for_value(pm, value):
    matches = []
    address = 0x00000000
    max_address = 0x7FFFFFFF_FFFFFFFF
    mbi = MEMORY_BASIC_INFORMATION()

    value_bytes = value.to_bytes(4, byteorder='little')
    allowed_protect = [0x04, 0x02, 0x20, 0x40, 0x80] 

    while address < max_address:
        try:
            if ctypes.windll.kernel32.VirtualQueryEx(pm.process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
                if mbi.State == 0x1000 and mbi.Protect in allowed_protect and mbi.RegionSize > 512:
                    try:
                        chunk = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                        for i in range(len(chunk) - len(value_bytes)):
                            if chunk[i:i + len(value_bytes)] == value_bytes:
                                found_addr = mbi.BaseAddress + i
                                matches.append(found_addr)
                    except:
                        pass
                address += mbi.RegionSize
            else:
                break
        except:
            address += 0x1000
    return matches

def filter_by_new_value(pm, addresses, new_value):
    new_value_bytes = new_value.to_bytes(4, byteorder='little')
    confirmed = []
    for addr in addresses:
        try:
            current = pm.read_bytes(addr, 4)
            if current == new_value_bytes:
                confirmed.append(addr)
        except:
            continue
    return confirmed

def modify_value(pm, addresses, new_value):
    new_value_bytes = new_value.to_bytes(4, byteorder='little')
    for addr in addresses:
        try:
            pm.write_bytes(addr, new_value_bytes, 4)
            print(f"Value at {hex(addr)} updated to {new_value}")
        except:
            print(f"Failed to write at {hex(addr)}")

process_name = "client.exe"
pid = get_pid_by_name(process_name)
if not pid:
    print("Process not found.")
    exit()

pm = pymem.Pymem()
pm.open_process_from_id(pid)

# First Scan
old_val = int(input("🎯 Enter current value (before buying): ").strip())
print("🔎 Scanning...")
initial_results = scan_for_value(pm, old_val)
print(f"✅ Found {len(initial_results)} matches")

# Next Scan
input("\nNow go buy something in-game, then press Enter to continue...")

new_val = int(input("🔄 Enter new value (after buying): ").strip())
filtered_results = filter_by_new_value(pm, initial_results, new_val)
print(f"Filtered to {len(filtered_results)} matching addresses")

# Modify
change_val = int(input("Enter value to change to (e.g. 99999): ").strip())
modify_value(pm, filtered_results, change_val)
