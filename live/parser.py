import os, sys
import subprocess
import re
import struct
import win32file
import winioctlcon


LOG_FILE = "DiskInfo.txt"
DEBUG_LOG_FILE = "DiskInfo64.log"

INTEL_SIGNATURE = "Intel Raid ISM Cfg Sig. "
AMD_SIGNATURE = "RAIDCore"

PATH = os.path.dirname(os.path.realpath(__file__))
PATH = os.path.join(PATH, "CrystalDiskInfo9_2_2")

def check_is_raid():
    # When bios setup is enabled, then we have to check by CrystalDiskInfo
    def when_bios_setup_enabled():
        _, controller_map, disk_list = parse_diskinfo_log()
        r = re.compile(".*\+.*Intel.*RST")
        for line in controller_map.split('\n'):
            if r.search(line) != None:
                return True
            
        r = re.compile("AMD_DRIVER_NAME")
        for line in controller_map.split('\n'):
            if r.search(line) != None:
                return True
        return False

    # When bios setup is disabled, then we have to read physical disks and check the Signature
    def when_bios_setup_disabled():
        
        for i in range(10):
            # Set buffer to 0 to read the disk
            # https://stackoverflow.com/questions/9901792/wmi-win32-diskdrive-to-get-total-sector-on-the-physical-disk-drive
            pd_name = '\\\\.\\PhysicalDisk{}'.format(i)
            with open(pd_name, 'rb', buffering = 0) as fr:
                fr.seek(0xA00000, os.SEEK_SET)
                data = fr.read(0x200)
                if data[8:16] == "RAIDCore":
                    print("AMD RAID Signature Found!!!")
                    return


                # get disk size
                pd = win32file.CreateFile(pd_name, win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, 0)
                size = win32file.DeviceIoControl(pd, winioctlcon.IOCTL_DISK_GET_LENGTH_INFO, None, 512, None)  #returns bytes
                size = struct.unpack('q', size)[0]  #convert 64 bit int from bytes to int -> first element of returned tuple
                print(size)
                fr.seek(size - 0x200)
                data = fr.read(0x200)
                if data[: len("Intel Raid ISM Cfg Sig")] == "Intel Raid ISM Cfg Sig":
                    print("Intel RAID Signature Found!!!!")
                    return
    
    if when_bios_setup_enabled():
        return True
    elif when_bios_setup_disabled():
        return True
    print("RAID not found")
    return False
    
    
def run_crystaldiskinfo():

    r = subprocess.run([os.path.join(PATH, "DiskInfo64"), "/CopyExit"])

    try:
        r.check_returncode()
    except subprocess.CalledProcessError:
        print("Exec CrystalDiskInfo Failed!!")
        exit()
    return

# noexcept for str.find()
def parse_diskinfo_log():
    log = ""
    
    with open(os.join(PATH, "DiskInfo.txt"), 'r') as f:
        log = f.read()        
    
    os_and_date = log[log.find("OS"):log.find("Controller Map")].replace('-', ' ')
    controller_map = log[log.find("Controller Map"):log.find("Disk List")].replace('-', ' ')
    disk_list = log[log.find("Disk List"):log.find("-" * 10)].replace('-', ' ')
    
    print("OS")
    print("-----------------------------------------")
    print(os_and_date)
    print("Controller map")
    print("-----------------------------------------")
    print(controller_map)
    print("Disk list")
    print("-----------------------------------------")
    print(disk_list)

    return os_and_date, controller_map, disk_list
    
    

    
if __name__ == '__main__':
    check_is_raid()