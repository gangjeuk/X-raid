from struct import unpack, calcsize
import os
import time
from collections import namedtuple
from typing import *


MAGIC = "RAIDCore"

SECTOR_SIZE = 0x200
ANCHOR_OFFSET = 0xA00000
METADATA_OFFSET = 0xB00000

ANCHOR = namedtuple(
    "ANCHOR",
    [
        "checksum",
        "signature",
        "disk_id",
        "padding1",
        "offset_sec",
        "padding2",
        "ddf_count",
    ],
)

HEADER = namedtuple(
    "HEADER",
    [
        "checksum",
        "checksum_parameter",
        "signature",
        "padding1",
        "disk_offset",
        "disk_size",  # number of disk = disk_size / (size_of_disk_metadata = 0x80)
        "vdisk_offset",
        "vdisk_size",  # number of vdisk = vdisk_size / (size_of_vdisk_metadata = 0x290)
        "padding2",
        "controller_offset",
        "controller_size"  # number of controller = controller_data_size / (size_of_controller_data_metadata = 0x88)
        "metadata_size",
    ],
)

DISK = namedtuple(
    "DISK",
    [
        "signature",
        "id",
        "unknown1",
        "unknown2",
        "padding1",
        "sector_count",
    ],
)
'''
VDISK = namedtuple(
    "VDISK",
    [
        "signature",
        "status",
        "padding1",
        "raid_signature",
        "padding2",
        "id",
        "padding3",
        "sector_count",
        "padding4",
        "total_count",
        "first_count",
        "second_count",
        "dummy_count",
        "padding5",
        "cts",
        "padding6",
        "hidden",
        "padding7",
        "name",
        "config",
    ],
)
'''
VDISK = namedtuple(
    "VDISK",
    [
        "signature",
        "status",
        "padding1",
        "raid_signature",
        "padding2",
        "id",
        "padding3",
        "sector_count",
        "padding4",
        "total_count",
        "first_count",
        "second_count",
        "dummy_count",
        "padding5",
        "hidden",
        "padding6",
        "name",
        "padding7",
        "cts",
        "config",
    ],
)
CONFIG = namedtuple(
    "CONFIG",
    [
        "id",
        "hd",  # hd(deviceroute) == disk index
        "rt",  # rt(coreroute): ??
        "padding1",
        "begin",
        "end",
    ],
)


# TODO: use ENUM for return value
def get_raid_level(vdisk: VDISK):
    raid_signature = vdisk.raid_signature
    first_count = vdisk.first_count
    second_count = vdisk.second_count

    if raid_signature == 0x1BF6:
        if first_count == 1 and second_count == 2:
            return 1
        elif first_count > 1 and second_count == 1:
            return 0
        elif first_count > 1 and second_count == 2:
            return 10
    elif raid_signature == 0x1BF5:
        if first_count == 1 and second_count > 2:
            return 5
    elif raid_signature == 0x1BF7:
        return "JBOD"


def get_stripe_size(vdisk: VDISK):
    if vdisk.cts == 1:
        return "64KB"
    elif vdisk.cts == 2:
        return "128KB"
    elif vdisk.cts == 3:
        return "256KB"


def get_rounded_size(size: Optional[int], unit: Literal["KB", "MB", "GB"]) -> str:
    if size is None:
        return None

    if unit == "KB":
        return str(size // 1000) + unit
    elif unit == "MB":
        return str(size // 1000000) + unit
    elif unit == "GB":
        return str(size // 1000000000) + unit


def check_is_amd_raid(file_name) -> bool:
    with open(file_name, "rb") as f:
        f.seek(ANCHOR_OFFSET, os.SEEK_SET)
        data = f.read(SECTOR_SIZE * 2)
        if data[8:16].decode() == MAGIC:
            return True
        else:
            return False


def dump_anchor(anchor: ANCHOR, verbose=False):
    print("======== ANCHOR ==========")
    print("Number of DDF Header: {}".format(anchor.ddf_count))
    print("Offset of latest version: {}".format(hex(anchor.offset_sec * SECTOR_SIZE)))
    print("Disk ID: {}".format(anchor.disk_id))


def dump_disk(disk: DISK, verbose=False):
    print("======== DISK Info ==========")
    print("ID: {}".format(hex(disk.id)))
    print("Size: {}".format(get_rounded_size(disk.sector_count * SECTOR_SIZE, "GB")))


def dump_vdisk(vdisk: VDISK, verbose=False):
    print("======== VDISK Info =========")
    print("ID: {}".format(vdisk.id))
    print("RAID Level: {}".format(get_raid_level(vdisk)))
    print("Stripe size: {}".format(get_stripe_size(vdisk)))
    print("Size: {}".format(get_rounded_size(vdisk.sector_count * SECTOR_SIZE, "GB")))
    print("Total disk count: {}".format(vdisk.total_count))
    print("Name: {}".format(vdisk.name))
    if verbose is True:
        print("----------------------------------------------------")
        print("[Order] Disk ID: Start Offset / End Offset")
        for config in vdisk.config:
            print(
                "[{}] {}: {}({}) - {}({})".format(
                    config.hd,
                    hex(config.id),
                    hex(config.begin * SECTOR_SIZE),
                    get_rounded_size(config.begin * SECTOR_SIZE, "GB"),
                    hex((config.begin + config.end) * SECTOR_SIZE),
                    get_rounded_size((config.begin + config.end) * SECTOR_SIZE, "GB"),
                )
            )
            print()
        print("----------------------------------------------------")

def parse_metadata(file_name) -> Tuple[ANCHOR, HEADER, list[DISK], list[VDISK]]:
    FORMAT = ""
    FORMAT_SIZE = 0
    f = open(file_name, "rb")
    data = b""

    header = b""
    anchor = b""
    disk_lst, vdisk_lst = [], []

    if not check_is_amd_raid(file_name):
        print("No AMD RAID Signature found")
        return None

    f.seek(ANCHOR_OFFSET, os.SEEK_SET)
    data = f.read(SECTOR_SIZE * 2)

    FORMAT = "<Q8sQ496pH38pH"
    FORMAT_SIZE = calcsize(FORMAT)
    anchor = ANCHOR._make(unpack(FORMAT, data[:FORMAT_SIZE]))

    # Read latest version
    f.seek(anchor.offset_sec * SECTOR_SIZE, os.SEEK_SET)
    data = f.read(SECTOR_SIZE)

    FORMAT = "<QLL20pLLLL8pLL"
    FORMAT_SIZE = calcsize(FORMAT)
    header = HEADER._make(unpack(FORMAT, data[:FORMAT_SIZE]))

    data = f.read(header.disk_size)
    for i in range(header.disk_size // 0x80):
        FORMAT = "<LQHH12pQ"
        FORMAT_SIZE = calcsize(FORMAT)
        disk_lst.append(
            DISK._make(unpack(FORMAT, data[0x80 * i : 0x80 * i + FORMAT_SIZE]))
        )

    vdisk_offset = 0
    data = f.read(header.vdisk_size)
    while vdisk_offset != header.vdisk_size:
        FORMAT = "<LLLL28pQ28pQ16pLLLL12pL32pH6p24sc"
        FORMAT = "<LLLL28pQ28pQ16pLLLL48pH6p24s72pHc"
        FORMAT_SIZE = calcsize(FORMAT)
        vdisk_lst.append(
            VDISK._make(unpack(FORMAT, data[vdisk_offset : vdisk_offset + FORMAT_SIZE]))
        )
        vdisk_offset += SECTOR_SIZE
        config = []
        for _ in range(vdisk_lst[-1].total_count):
            FORMAT = "<QHH20pQQ"
            FORMAT_SIZE = calcsize(FORMAT)
            config.append(
                CONFIG._make(
                    unpack(FORMAT, data[vdisk_offset : vdisk_offset + FORMAT_SIZE])
                )
            )
            vdisk_offset += 0x40
        vdisk_lst[-1] = vdisk_lst[-1]._replace(config=config)
        vdisk_offset += 0x10

    f.close()

    return anchor, header, disk_lst, vdisk_lst


def reconstruct(file_names: list[str], output_path: str):
    if output_path is None:
        print("No output path")
        return
    
    file_disk_map = {}

    # Check every disk image and match DiskID with file
    for file_name in file_names:
        anchor, header, disk_lst, vdisk_lst = parse_metadata(file_name)
        file_disk_map[anchor.disk_id] = file_name

    # TODO: Metadata validation for each disk
    # Use metadata in the first file in list for now

    # TODO
    # RAID0 tested
    # RAID1 tested
    # RAID10 not tested
    # JBOD not tested

    anchor, header, disk_lst, vdisk_lst = parse_metadata(file_names[0])
    for vdisk in vdisk_lst:
        output_name = ""
        stripe_size = 1 << (15 + vdisk.cts)
        raid_level = get_raid_level(vdisk)
        size = get_rounded_size(vdisk.sector_count * SECTOR_SIZE, "GB")
        fd_disk_map = {}
        for config in vdisk.config:
            fd_disk_map[config.id] = open(file_disk_map[config.id], "rb")

        output_name = str(vdisk.id) + "_RAID-" + str(raid_level) + "_" + size + ".img"
        print("Reconstructing VDISK ID: {}".format(output_name))
        dump_vdisk(vdisk, True)
        with open(os.path.join(output_path, output_name), "wb") as fw:
            # set each disk SEEK position
            for config in vdisk.config:
                fd_disk_map[config.id].seek(config.begin * SECTOR_SIZE, os.SEEK_SET)

            if raid_level == 0:
                # calc how many times to loop
                for i in range((vdisk.config[0].end * SECTOR_SIZE) // stripe_size):
                    # reconstruct by disk order
                    # AMD RAID follow the order in vdisk.config
                    data = b""
                    for config in vdisk.config:
                        data += fd_disk_map[config.id].read(stripe_size)
                    fw.write(data)

            elif raid_level == 1:
                # calc how many times to loop
                for i in range((vdisk.config[0].end * SECTOR_SIZE) // stripe_size):
                    data = fd_disk_map[vdisk.config[0].id].read(stripe_size)
                    fw.write(data)

            # TODO: RAID10 and JBOD
            # elif

        map(lambda x: x.close(), fd_disk_map.keys())

    return 1


def print_info(file_name, verbose):
    anchor, _, disk_list, vdisk_list = parse_metadata(file_name)

    dump_anchor(anchor)
    
    for i, disk in enumerate(disk_list):
        if i == 0:
            continue
        dump_disk(disk, verbose)

    for vdisk in vdisk_list:
        dump_vdisk(vdisk, verbose)


def print_help():
    print("Print information")
    print("python main.py --system AMD -i [-v] --files [disk_image.img]")
    print("\n")
    print("Reconstruction")
    print("python main.py --system AMD -r --files [disk_image1.img] --files [disk_image2.img] --output_path ./output")
    

if __name__ == "__main__":
    file_name = "data/AMD/hex"
    _, header, disk_lst, vdisk_lst = parse_metadata(file_name)

    dump_disk(disk_lst[1])
    for vdisk in vdisk_lst:
        dump_vdisk(vdisk, verbose=True)
