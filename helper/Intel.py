import re
import os

SECTOR_SIZE = 0x200

def check_magic(data, magic) -> bool:
    # check magic values
    if data[:len(magic)] == magic:
        return True
    elif data[-2:] == b'\x55\xAA':
        return True
    return False

def disk_order_helper(file_names):
    print("Checking disk order...")
    dev_map = { file_name : {"offset": [], "order": -1} for file_name in file_names } 
    
    for file_name in file_names:
        with open(file_name, 'rb') as f:
            for i in range(0x10000):
                read_data = f.read(SECTOR_SIZE)
                # check EFI
                if check_magic(read_data, b'EFI PART'):
                    print("Found GPT Partition Signature. First disk: {}, Offset: {}".format(file_name, hex(i * SECTOR_SIZE)))
                    dev_map[file_name]["order"] = 1
                # check NTFS
                elif check_magic(read_data, b'\xEB\x52\x90NTFS'):
                    print("Found NTFS Signature. First disk: {}, Offset: {}".format(file_name, hex(i * SECTOR_SIZE)))
                    dev_map[file_name]["order"] = 1              
    return dev_map

def raid_level_helper(file_names, dev_map):
    print("Checking RAID level...")
    # We don't need think about RAID1 
    # If all disk have order == -1, something went wrong in previous process
    if len(list(filter(lambda x: dev_map[x]["order"] == -1, dev_map))) == len(dev_map):
        print("Something went wrong. RAID level has not been set in previous step")
        exit(1)
    # Only one disk should have EFI or BR. If not, it must be RAID1
    if len(list(filter(lambda x: dev_map[x]["order"] == 1, dev_map))) != 1:
        if len(file_names) == 2:
            print("RAID level must be 1. Check image files")
            exit(1)
        else:
            print("Something went wrong. Check image files")
            print("Manual Reconstruction might be needed")
            exit(1)
    elif len(list(filter(lambda x: dev_map[x]["order"] == 1, dev_map))) == 2 and len(file_names) == 4:
        print("Guessed RAID level: RAID10")
        return

    
    # check RAID5
    if len(dev_map) >= 3:
        data = b'\x00' * SECTOR_SIZE
        for file_name in file_names:
            with open(file_name, 'rb') as f:
                f.seek(0x200, os.SEEK_SET)
                data = bytes(i ^ j for i, j in zip(data, f.read(SECTOR_SIZE)))
        if data == b'\x00' * SECTOR_SIZE:
            print("Gussed RAID level: RAID5")
            return
    
    print("Gussed RAID level: RAID0")
    return

def start_offset_helper(file_name):
    print("Checking start offset...")
    print("Might take some time...")
    start_offset_candi = set()
    
    with open(file_name, 'rb') as f:
        i = 0
        while True:
            data = f.read(SECTOR_SIZE)
            if len(data) != SECTOR_SIZE:
                break
            if check_magic(data, b'EFI PART'):
                # fit in stripe unit size
                start_offset_candi.add(((i * SECTOR_SIZE) // 0x1000) * 0x1000)
            i += 1
    print("Start offset candidates: {}".format(start_offset_candi))

def print_metadata(file_names):
    '''
    # Print parsed metadata
    metadata = read_first_meta_sec(file_names[0])
    disk_offset = 0
    p = re.compile("[a-zA-Z0-9]{8,16}")
    
    imsm_super, disk_offset = parse_header(metadata, disk_offset)

    metadata += read_rest_meta_sec(file_names[0], SECTOR_SIZE * 2)

    print_imsm_super(imsm_super)

    while True:
        imsm_disk, tmp_offset = parse_disk(metadata, disk_offset)
        if p.match(imsm_disk.serial.decode().rstrip("\x00")):
            disk_offset = tmp_offset
            print_imsm_disk(imsm_disk)
        else:
            break

    # Maximum two vdisk
    for _ in range(2):
        imsm_dev, disk_offset = parse_dev(metadata, disk_offset)
        print_imsm_dev(imsm_dev)
    '''
    pass
        
def reconstruct_helper(
    file_names: str,
    output_path: str,
):
    if len(file_names) == 1:
        print("Wrong input")
        exit(1)

    dev_map = disk_order_helper(file_names)
    raid_level_helper(file_names, dev_map)
    first_disk = list(filter(lambda x: dev_map[x]["order"] == 1, dev_map))[0]
    
    # check start offset candidates
    start_offset_candi = start_offset_helper(first_disk)

    
def reconstruct(
    file_names: str, # file_names follow disk order
    strip_size: int,
    start_offset: int,
    vdisk_size: int,
    raid_level: int,
    output_path: str,
):

    disk_fds = [
        open(
            os.path.join(
                os.curdir, file_name
            ),
            "rb",
        )
        for file_name in file_names
    ]
    
    DISK_NAME = (
        "DISK_"
        + "_"
        + "RAID_LEVEL_"
        + str(raid_level)
        + ".img"
    )
    with open(os.path.join(output_path, DISK_NAME), "wb") as f:
        print("Recover Started")
        print("DISK NAME: " + DISK_NAME)
        # super-intel.c #1330
        if raid_level == 0:
            # set to lba
            [fd.seek(start_offset * SECTOR_SIZE, 0) for fd in disk_fds]
            for _ in range(vdisk_size // SECTOR_SIZE):
                buf = b""
                # read disk of strip size by disk order
                for disk_fd in disk_fds:
                    buf += disk_fd.read(strip_size)
                f.write(buf)

        if raid_level == 5:
            # set to lba
            [fd.seek(start_offset * SECTOR_SIZE, 0) for fd in disk_fds]
            for _ in range(vdisk_size // SECTOR_SIZE):
                buf = b""
                # read disk
                for i, disk_fd in enumerate(disk_fds):
                    # Intel RAID write parity bit like below
                    # d1 d2 d3
                    # .  .  p
                    # .  p  .
                    # p  .  .
                    parity_idx = i % len(file_names)
                    # pass parity stripe
                    if i != 0 and parity_idx == 0:
                        continue
                    buf += disk_fd.read(strip_size)
                    f.write(buf)

        [fd.close() for fd in disk_fds]
