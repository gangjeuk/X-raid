from struct import unpack, calcsize
import os
import time
import sys
import gc
from collections import namedtuple
from typing import *
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
# https://stackoverflow.com/questions/4193514/how-to-get-hard-disk-serial-number-using-python


SECTOR_SIZE = 512
sector_size_candi = [512, 1024, 2048, 4096]

SEEK_END = 2


IMSM_DISK = namedtuple(
    "IMSM_DISK",
    [
        "serial",
        "total_blocks_lo",
        "scsi_id",
        "status",
        "owner_cfg_num",
        "total_blocks_hi",
    ],
)  #'filler']) NOT USED

IMSM_DEV = namedtuple(
    "IMSM_DEV",
    [
        "volume",
        "size_low",
        "size_high",
        "status",
        "reserved_blocks",
        "migr_priority",
        "num_sub_vols",
        "tid",
        "cng_master_disk",
        "cache_policy",
        "cng_state",
        "cng_sub_state",
        "my_vol_raid_dev_num",
        "nv_cache_mode",
        "nv_cache_flags",
        "nvc_vol_orig_family_num",
        "nvc_vol_raid_dev_num",
        "rwh_policy",
        "jd_serial",
        "imsm_vol",
    ],
)  # ,'filler1','filler']) NOT USED

IMSM_VOL = namedtuple(
    "IMSM_VOL",
    [
        "curr_migr_unit",
        "checkpoint_id",
        "migr_state",
        "migr_type",
        "dirty",
        "fs_state",
        "verify_errors",
        "bad_blocks",
        "imsm_map",
    ],
)  # ,'filler']) NOT USED

IMSM_MAP = namedtuple(
    "IMSM_MAP",
    [
        "pba_of_lba0_lo",
        "blocks_per_member_lo",
        "num_data_stripes_lo",
        "blocks_per_strip",
        "map_state",
        "raid_level",
        "num_members",
        "num_domains",
        "failed_disk_num",
        "ddf",
        "pba_of_lba0_hi",
        "blocks_per_member_hi",
        "num_data_stripes_hi",
        "disk_ord_tbl",
    ],
)


IMSM_SUPER = namedtuple(
    "IMSM_SUPER",
    [
        "sig",
        "check_sum",
        "mpb_size",
        "family_num",
        "generation_num",
        "error_log_size",
        "attributes",
        "num_disks",
        "num_raid_devs",
        "error_log_pos",
        "fill",
        "cache_size",
        "orig_family_num",
        "pwr_cycle_count",
        "bbm_log_size",
        "num_raid_devs_created",
        "filler1",
        "creation_time",
    ],
)
MAGIC = "Intel Raid ISM Cfg Sig. "


def get_rounded_size(size: Optional[int], unit: Literal["KB", "MB", "GB"]) -> str:
    if size is None:
        return None

    if unit == "KB":
        return str(size // 1000) + unit
    elif unit == "MB":
        return str(size // 1000000) + unit
    elif unit == "GB":
        return str(size // 1000000000) + unit

def print_imsm_super(imsm_super: IMSM_SUPER, verbose: bool = False):
    print("-----------Header------------")
    print("Magic : {}".format(imsm_super.sig[: len(MAGIC)]))
    print("Version : {}".format(imsm_super.sig[len(MAGIC) :]))
    print("Orig Family: " + hex(imsm_super.orig_family_num))
    print("Family: " + hex(imsm_super.family_num))
    print("Generation: " + hex(imsm_super.generation_num))
    print("Creation Time: " + time.ctime(imsm_super.creation_time))
    print("Disk count: {}".format(imsm_super.num_disks))
    print("VDisk count: {}".format(imsm_super.num_raid_devs))
    print("-----------------------------")


def print_imsm_disk(imsm_disk: IMSM_DISK, verbose: bool = False):
    print("------------DISK------------")
    print("Serial: {}".format(imsm_disk.serial))
    print("Size: {}".format(get_rounded_size(get_total_blocks(imsm_disk) * SECTOR_SIZE, 'GB')))
    print("SCSI ID: {}".format(imsm_disk.scsi_id))
    print("------------------------------")


def print_imsm_dev(imsm_dev: IMSM_DEV, verbose: bool = False):
    imsm_map = imsm_dev.imsm_vol.imsm_map
    print("------------VDISK------------")
    print("Name: {}".format(imsm_dev.volume))
    print("Size: {}".format(get_rounded_size(get_dev_size(imsm_dev) * SECTOR_SIZE, 'GB')))
    print("TID: {}".format(imsm_dev.tid))
    print("Start Offset: {}".format(get_pba_of_lba0(imsm_map) * SECTOR_SIZE))
    print("Stipe Size: {}".format(imsm_map.blocks_per_strip * SECTOR_SIZE))
    print("Number of stripe of Disk: {}".format(get_num_data_stripes(imsm_map)))
    print("Number of VDisk: {}".format(get_blocks_per_member(imsm_map)))
    print("RAID Level: {}".format(get_imsm_raid_level(imsm_map)))
    print("Disk Order: {}".format(imsm_map.disk_ord_tbl))
    print("------------------------------")


def get_imsm_raid_level(imsm_map: IMSM_MAP) -> int:
    if imsm_map.raid_level == 1:
        if imsm_map.num_members == 2:
            return 1
        else:
            return 10

    return imsm_map.raid_level


# UTIL_BEGIN
def join_u32(lo: int, hi: int) -> int:
    return (hi << 32) + lo


def get_dev_size(imsm_dev: IMSM_DEV):
    return join_u32(imsm_dev.size_low, imsm_dev.size_high)


def get_blocks_per_member(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.blocks_per_member_lo, imsm_map.blocks_per_member_hi)


def get_num_data_stripes(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.num_data_stripes_lo, imsm_map.num_data_stripes_hi)


def get_pba_of_lba0(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.pba_of_lba0_lo, imsm_map.pba_of_lba0_hi)


def get_total_blocks(imsm_disk: IMSM_DISK):
    return join_u32(imsm_disk.total_blocks_lo, imsm_disk.total_blocks_hi)


def read_rest_meta_sec(file_name, mpb_size):
    ret = b""
    sec_size = mpb_size // SECTOR_SIZE
    with open(file_name, "br") as f:
        f.seek(-1 * (sec_size + 2) * SECTOR_SIZE, SEEK_END)
        ret = f.read(mpb_size - SECTOR_SIZE)
    if len(ret) != mpb_size - SECTOR_SIZE:
        print("SECTOR read error")
        exit(1)
    return ret

# UTIL_END  x

def read_first_meta_sec(file_name):
    ret = b""
    with open(file_name, "br") as f:
        f.seek(-1 * SECTOR_SIZE * 2, SEEK_END)
        ret = f.read(SECTOR_SIZE * 1)

    if len(ret) != SECTOR_SIZE:
        print("SECTOR read error")
        exit(1)
    return ret


def check_is_intel_raid(file_name) -> int:
    global SECTOR_SIZE
    global sector_size_candi
    for candi in sector_size_candi:
        SECTOR_SIZE = candi
        metadata = read_first_meta_sec(file_name)
        if metadata[: len(MAGIC)].decode('ascii') == MAGIC:

            return True
        elif metadata[1: len(MAGIC)].decode('ascii') == MAGIC[1:]:
            print("Intel RAID detected but metadata has been deleted!!!")
            print("It has to be recovered manually!!")
            return False
    return False


def quick_scan(file_names):
    if check_is_intel_raid(file_names) == True:
        print("\033[34mIntel\033[0m RAID \033[32mdetected!\033[0m")

    else:
        print("\033[34mIntel\033[0m RAID \033[31mNOT\033[0m detected..")


def read_chunk(file_name, start_offset, chunk_size, target_bytes):
    results = []

    with open(file_name, "rb") as f:
        f.seek(start_offset)
        chunk = f.read(chunk_size)

        found_offset = 0
        while (found_offset := chunk.find(target_bytes, found_offset)) != -1:
            actual_offset = start_offset + found_offset
            results.append(f"[FOUND] Target hex at offset: {actual_offset} (0x{actual_offset:X})")
            found_offset += 1

    return results, len(chunk)


def deep_scan(file_names: str, chunk_size=128 * 1024 * 1024, num_threads=os.cpu_count()):
    target_bytes = bytes.fromhex("496E74656C20526169642049534D2043666720536967")  # Intel Raid ISM Cfg Sig
    file_size = os.path.getsize(file_names)
    chunk_ranges = [(i * chunk_size, min((i + 1) * chunk_size, file_size)) for i in
                    range((file_size // chunk_size) + 1)]

    start_time = time.time()

    with tqdm(total=file_size, unit="B", unit_scale=True, desc="Scanning") as pbar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(read_chunk, file_names, start, end - start, target_bytes): (start, end)
                       for start, end in chunk_ranges}

            for future in futures:
                results, chunk_length = future.result()
                for result in results:
                    print(result)
                pbar.update(chunk_length)

    total_time = time.time() - start_time
    print(f"\nScanning Complete! Total Time: {total_time:.2f} seconds")


def parse_header(metadata, disk_offset):
    FORMAT = "<32sLLLLLLBBBBLLLLHHQ"
    FORMAT_SIZE = calcsize(FORMAT)
    imsm_super = IMSM_SUPER._make(unpack(FORMAT, metadata[:FORMAT_SIZE]))
    disk_offset += 0xD8
    return imsm_super, disk_offset

def parse_disk(metadata, disk_offset):
    FORMAT = "<16sLLLLL"
    FORMAT_SIZE = calcsize(FORMAT)
    imsm_disk = IMSM_DISK._make(unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE]))
    disk_offset += 0x30
    return imsm_disk, disk_offset

def parse_dev(metadata, disk_offset):
    FORMAT = "<16sLLLLBBBBHBBHBBLHB16s"
    FORMAT_SIZE = calcsize(FORMAT)
    device = unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE])
    disk_offset += 0x50

    FORMAT = "<LLBBBBHH"
    FORMAT_SIZE = calcsize(FORMAT)
    volume = unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE])
    disk_offset += 0x20

    FORMAT = "<LLLHBBBBBBLLL"
    FORMAT_SIZE = calcsize(FORMAT)
    map_info = unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE])
    disk_offset += 0x30

    num_members = map_info[6]

    FORMAT = "<" + "L" * num_members
    FORMAT_SIZE = calcsize(FORMAT)
    disk_ord_tbl = unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE])
    disk_offset += FORMAT_SIZE

    imsm_map = IMSM_MAP._make([*map_info, disk_ord_tbl])
    imsm_vol = IMSM_VOL._make([*volume, imsm_map])
    imsm_dev = IMSM_DEV._make([*device, imsm_vol])

    return imsm_dev, disk_offset


def parse_metadata(file_name) -> tuple[IMSM_SUPER, list[IMSM_DISK], list[IMSM_DEV]]:
    metadata = read_first_meta_sec(file_name)
    disk_offset = 0

    imsm_super, disk_offset = parse_header(metadata, disk_offset)

    if imsm_super.mpb_size > SECTOR_SIZE:
        metadata += read_rest_meta_sec(file_name, imsm_super.mpb_size)

    if len(metadata) != imsm_super.mpb_size:
        print("SECTOR size error")
        exit(1)

    imsm_disk_l = []
    imsm_dev_l = []

    for _ in range(imsm_super.num_disks):
        imsm_disk, disk_offset = parse_disk(metadata, disk_offset)
        imsm_disk_l.append(imsm_disk)

    for _ in range(imsm_super.num_raid_devs):
        imsm_dev, disk_offset = parse_dev(metadata, disk_offset)
        imsm_dev_l.append(imsm_dev)

    return (imsm_super, imsm_disk_l, imsm_dev_l)


def reconstruct(
    file_names: str,
    output_path: str,
):
    if check_is_intel_raid(file_names[0]) == False:
        print("Intel RAID is not detected")
        exit(1)

    imsm_super, imsm_disk_l, imsm_dev_l = parse_metadata(file_names[0])

    for dev in imsm_dev_l:
        strip_size = dev.imsm_vol.imsm_map.blocks_per_strip * SECTOR_SIZE
        stripes_count = get_num_data_stripes(dev.imsm_vol.imsm_map)
        start_lba = get_pba_of_lba0(dev.imsm_vol.imsm_map)
        raid_level = get_imsm_raid_level(dev.imsm_vol.imsm_map)
        disk_ord_tbl = dev.imsm_vol.imsm_map.disk_ord_tbl
        disk_fds = [
            open(
                os.path.join(
                    #output_path, imsm_disk.serial.decode().rstrip("\x00") + ".img"
                    os.curdir, file_name
                ),
                "rb",
            )
            #for imsm_disk in imsm_disk_l
            for file_name in file_names
        ]
        DISK_NAME = (
            "DISK"
            + str(dev.my_vol_raid_dev_num)
            + "_"
            + "RAID_LEVEL_"
            + str(raid_level)
            + ".img"
        )
        with open(DISK_NAME, "wb") as f:
            print("Recover Started")
            print("DISK NAME: " + DISK_NAME)
            print_imsm_dev(dev)
            # super-intel.c #1330
            if raid_level == 0:
                # set to lba
                [fd.seek(start_lba * SECTOR_SIZE, 0) for fd in disk_fds]
                for _ in range(stripes_count):
                    buf = b""
                    # read disk of strip size by disk order
                    for ord in disk_ord_tbl:
                        buf += disk_fds[ord].read(strip_size)
                    f.write(buf)

            if raid_level == 1:
                # set to lba
                [fd.seek(start_lba * SECTOR_SIZE, 0) for fd in disk_fds]
                for _ in range(stripes_count * 2):
                    buf = b""
                    # read only one disk of strip size by disk order
                    buf += disk_fds[disk_ord_tbl[0]].read(strip_size)
                    f.write(buf)


            if raid_level == 5:
                # set to lba
                [fd.seek(start_lba * SECTOR_SIZE, 0) for fd in disk_fds]
                for _ in range(stripes_count):
                    buf = b""
                    # read disk
                    for i, ord in enumerate(disk_ord_tbl):
                        # Intel RAID write parity bit like below
                        # d1 d2 d3
                        # .  .  p
                        # .  p  .
                        # p  .  .
                        parity_idx = i % len(disk_ord_tbl)
                        # pass parity stripe
                        if i != 0 and parity_idx == 0:
                            continue
                        buf += disk_fds[ord].read(strip_size)
                        f.write(buf)

        [fd.close() for fd in disk_fds]

    
def print_info(file_name, verbose):
    imsm_super, imsm_disk_l, imsm_dev_l = parse_metadata(file_name)

    print_imsm_super(imsm_super, verbose)

    for disk in imsm_disk_l:
        print_imsm_disk(disk, verbose)

    for dev in imsm_dev_l:
        print_imsm_dev(dev, verbose)


def print_help():
    print("help!!!")


if __name__ == "__main__":
    print("Intel RAID Main")

