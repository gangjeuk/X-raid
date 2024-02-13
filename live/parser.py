import os, sys
import subprocess
import re
import struct
# pip install pywin32
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
    _, controller_map, disk_list = parse_diskinfo_log()
    def when_bios_setup_enabled():
        r = re.compile(".*\+.*Intel.*RST")
        for line in controller_map.split("\n"):
            if r.search(line) != None:
                print("Intel RAID Found!")
                return True

        r = re.compile("AMD RAID Controller")
        for line in controller_map.split("\n"):
            if r.search(line) is not None:
                print("AMD RAID Found!")
                return True
        print("RAID not FOUND")
        return False

    # When bios setup is disabled, then we have to read physical disks and check the Signature
    def when_bios_setup_disabled():
        ret = False
        try:
            for i in range(0x10):
                # Set buffer to 0 to read the disk
                # https://stackoverflow.com/questions/9901792/wmi-win32-diskdrive-to-get-total-sector-on-the-physical-disk-drive
                pd_name = "\\\\.\\PHYSICALDRIVE{}".format(i)
                # get disk size
                pd = win32file.CreateFile(
                    pd_name,
                    win32file.GENERIC_READ,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_ATTRIBUTE_NORMAL,
                    0,
                )
                size = win32file.DeviceIoControl(
                    pd, winioctlcon.IOCTL_DISK_GET_LENGTH_INFO, None, 512, None
                )  # returns bytes
                size = struct.unpack(
                    "q", size
                )[
                    0
                ]  # convert 64 bit int from bytes to int -> first element of returned tuple
                pd.Close()
                
                print("Physical Drive {}".format(disk_list.split('\n')[i + 1]))
                with open(pd_name, "rb", buffering=0) as fr:
                    # Check AMD RAID
                    fr.seek(0xA00000, os.SEEK_SET)
                    data = fr.read(0x200)
                    if data[8:16] == b"RAIDCore":
                        print("AMD RAID Signature Found!!!")
                        ret = True
                    else:
                        print("AMD RAID not found")
                        print(data[8:16])


                    # Check Intel RAID
                    fr.seek(size - 0x400)
                    data = fr.read(0x200)
                    if data[: len("Intel Raid ISM Cfg Sig")] == b"Intel Raid ISM Cfg Sig":
                        print("Intel RAID Signature Found!!!!")
                        ret = True
                    elif data[1: len("Intel Raid ISM Cfg Sig")] == b"ntel Raid ISM Cfg Sig":
                        print("Intel RAID found but metadata has been erased - Need more CHECK!!")
                        ret = True
                    else:
                        print("Intel RAID Signature not found")
                        print(data[: len("Intel Raid ISM Cfg Sig")])
                print('\n\n')
        except:
            # No more Physical disk
            return ret
        return ret

    if when_bios_setup_enabled():
        return True
    elif when_bios_setup_disabled():
        return True

    return False


def run_crystaldiskinfo():
    r = subprocess.run([os.path.join(PATH, "DiskInfo64.exe"), "/CopyExit"])

    try:
        r.check_returncode()
    except subprocess.CalledProcessError:
        print("Exec CrystalDiskInfo Failed!!")
        exit()
    return


# noexcept for str.find()
def parse_diskinfo_log():
    log = ""

    with open(os.path.join(PATH, "DiskInfo.txt"), "r", encoding='utf8') as f:
        log = f.read()

    # TODO: code refactoring
    os_and_date = log[log.find("OS") : log.find("Controller Map")].replace("-", " ")
    controller_map = log[log.find("Controller Map") : log.find("Disk List")].replace("-", " ")
    disk_list = log[log.find("Disk List") : log.find("Model")].replace("-", " ")
    disk_list = disk_list[: disk_list.rfind("(01)")]
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


if __name__ == "__main__":
    run_crystaldiskinfo()
    check_is_raid()