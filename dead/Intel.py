from struct import unpack, calcsize
import os
import time
from collections import namedtuple

# https://stackoverflow.com/questions/4193514/how-to-get-hard-disk-serial-number-using-python

"""
/* Disk configuration info. */
#define IMSM_MAX_DEVICES 255
struct imsm_disk {
	__u8 serial[MAX_RAID_SERIAL_LEN];/* 0xD8 - 0xE7 ascii serial number */
	__u32 total_blocks_lo;		 /* 0xE8 - 0xEB total blocks lo */
	__u32 scsi_id;			 /* 0xEC - 0xEF scsi ID */
#define SPARE_DISK      __cpu_to_le32(0x01)  /* Spare */
#define CONFIGURED_DISK __cpu_to_le32(0x02)  /* Member of some RaidDev */
#define FAILED_DISK     __cpu_to_le32(0x04)  /* Permanent failure */
#define JOURNAL_DISK    __cpu_to_le32(0x2000000) /* Device marked as Journaling Drive */
	__u32 status;			 /* 0xF0 - 0xF3 */
	__u32 owner_cfg_num; /* which config 0,1,2... owns this disk */
	__u32 total_blocks_hi;		 /* 0xF4 - 0xF5 total blocks hi */
#define	IMSM_DISK_FILLERS	3
	__u32 filler[IMSM_DISK_FILLERS]; /* 0xF5 - 0x107 MPB_DISK_FILLERS for future expansion */
};
ASSERT_SIZE(imsm_disk, 48)

/* map selector for map managment
 */
#define MAP_0		0
#define MAP_1		1
#define MAP_X		-1

/* RAID map configuration infos. */
struct imsm_map {
	__u32 pba_of_lba0_lo;	/* start address of partition */
	__u32 blocks_per_member_lo;/* blocks per member */
	__u32 num_data_stripes_lo;	/* number of data stripes */
	__u16 blocks_per_strip;
	__u8  map_state;	/* Normal, Uninitialized, Degraded, Failed */
#define IMSM_T_STATE_NORMAL 0
#define IMSM_T_STATE_UNINITIALIZED 1
#define IMSM_T_STATE_DEGRADED 2
#define IMSM_T_STATE_FAILED 3
	__u8  raid_level;
#define IMSM_T_RAID0 0
#define IMSM_T_RAID1 1
#define IMSM_T_RAID5 5		/* since metadata version 1.2.02 ? */
	__u8  num_members;	/* number of member disks */
	__u8  num_domains;	/* number of parity domains */
	__u8  failed_disk_num;  /* valid only when state is degraded */
	__u8  ddf;
	__u32 pba_of_lba0_hi;
	__u32 blocks_per_member_hi;
	__u32 num_data_stripes_hi;
	__u32 filler[4];	/* expansion area */
#define IMSM_ORD_REBUILD (1 << 24)
	__u32 disk_ord_tbl[1];	/* disk_ord_tbl[num_members],
				 * top byte contains some flags
				 */
};
ASSERT_SIZE(imsm_map, 52)

struct imsm_vol {
	__u32 curr_migr_unit;
	__u32 checkpoint_id;	/* id to access curr_migr_unit */
	__u8  migr_state;	/* Normal or Migrating */
#define MIGR_INIT 0
#define MIGR_REBUILD 1
#define MIGR_VERIFY 2 /* analagous to echo check > sync_action */
#define MIGR_GEN_MIGR 3
#define MIGR_STATE_CHANGE 4
#define MIGR_REPAIR 5
	__u8  migr_type;	/* Initializing, Rebuilding, ... */
#define RAIDVOL_CLEAN          0
#define RAIDVOL_DIRTY          1
#define RAIDVOL_DSRECORD_VALID 2
	__u8  dirty;
	__u8  fs_state;		/* fast-sync state for CnG (0xff == disabled) */
	__u16 verify_errors;	/* number of mismatches */
	__u16 bad_blocks;	/* number of bad blocks during verify */
	__u32 filler[4];
	struct imsm_map map[1];
	/* here comes another one if migr_state */
};
ASSERT_SIZE(imsm_vol, 84)

struct imsm_dev {
	__u8  volume[MAX_RAID_SERIAL_LEN];
	__u32 size_low;
	__u32 size_high;
#define DEV_BOOTABLE		__cpu_to_le32(0x01)
#define DEV_BOOT_DEVICE		__cpu_to_le32(0x02)
#define DEV_READ_COALESCING	__cpu_to_le32(0x04)
#define DEV_WRITE_COALESCING	__cpu_to_le32(0x08)
#define DEV_LAST_SHUTDOWN_DIRTY	__cpu_to_le32(0x10)
#define DEV_HIDDEN_AT_BOOT	__cpu_to_le32(0x20)
#define DEV_CURRENTLY_HIDDEN	__cpu_to_le32(0x40)
#define DEV_VERIFY_AND_FIX	__cpu_to_le32(0x80)
#define DEV_MAP_STATE_UNINIT	__cpu_to_le32(0x100)
#define DEV_NO_AUTO_RECOVERY	__cpu_to_le32(0x200)
#define DEV_CLONE_N_GO		__cpu_to_le32(0x400)
#define DEV_CLONE_MAN_SYNC	__cpu_to_le32(0x800)
#define DEV_CNG_MASTER_DISK_NUM	__cpu_to_le32(0x1000)
	__u32 status;	/* Persistent RaidDev status */
	__u32 reserved_blocks; /* Reserved blocks at beginning of volume */
	__u8  migr_priority;
	__u8  num_sub_vols;
	__u8  tid;
	__u8  cng_master_disk;
	__u16 cache_policy;
	__u8  cng_state;
	__u8  cng_sub_state;
	__u16 my_vol_raid_dev_num; /* Used in Unique volume Id for this RaidDev */

	/* NVM_EN */
	__u8 nv_cache_mode;
	__u8 nv_cache_flags;

	/* Unique Volume Id of the NvCache Volume associated with this volume */
	__u32 nvc_vol_orig_family_num;
	__u16 nvc_vol_raid_dev_num;

#define RWH_OFF 0
#define RWH_DISTRIBUTED 1
#define RWH_JOURNALING_DRIVE 2
#define RWH_MULTIPLE_DISTRIBUTED 3
#define RWH_MULTIPLE_PPLS_JOURNALING_DRIVE 4
#define RWH_MULTIPLE_OFF 5
	__u8  rwh_policy; /* Raid Write Hole Policy */
	__u8  jd_serial[MAX_RAID_SERIAL_LEN]; /* Journal Drive serial number */
	__u8  filler1;

#define IMSM_DEV_FILLERS 3
	__u32 filler[IMSM_DEV_FILLERS];
	struct imsm_vol vol;
};
ASSERT_SIZE(imsm_dev, 164)

struct imsm_super {
	__u8 sig[MAX_SIGNATURE_LENGTH];	/* 0x00 - 0x1F */
	__u32 check_sum;		/* 0x20 - 0x23 MPB Checksum */
	__u32 mpb_size;			/* 0x24 - 0x27 Size of MPB */
	__u32 family_num;		/* 0x28 - 0x2B Checksum from first time this config was written */
	__u32 generation_num;		/* 0x2C - 0x2F Incremented each time this array's MPB is written */
	__u32 error_log_size;		/* 0x30 - 0x33 in bytes */
	__u32 attributes;		/* 0x34 - 0x37 */
	__u8 num_disks;			/* 0x38 Number of configured disks */
	__u8 num_raid_devs;		/* 0x39 Number of configured volumes */
	__u8 error_log_pos;		/* 0x3A  */
	__u8 fill[1];			/* 0x3B */
	__u32 cache_size;		/* 0x3c - 0x40 in mb */
	__u32 orig_family_num;		/* 0x40 - 0x43 original family num */
	__u32 pwr_cycle_count;		/* 0x44 - 0x47 simulated power cycle count for array */
	__u32 bbm_log_size;		/* 0x48 - 0x4B - size of bad Block Mgmt Log in bytes */
	__u16 num_raid_devs_created;	/* 0x4C - 0x4D Used for generating unique
					 * volume IDs for raid_dev created in this array
					 * (starts at 1)
					 */
	__u16 filler1;			/* 0x4E - 0x4F */
	__u64 creation_time;		/* 0x50 - 0x57 Array creation time */
#define IMSM_FILLERS 32
	__u32 filler[IMSM_FILLERS];	/* 0x58 - 0xD7 RAID_MPB_FILLERS */
	struct imsm_disk disk[1];	/* 0xD8 diskTbl[numDisks] */
	/* here comes imsm_dev[num_raid_devs] */
	/* here comes BBM logs */
};
ASSERT_SIZE(imsm_super, 264)
"""

"""
------------------------DISK LAYOUT---------------------------
|=========================================|
|imsm_super                               |
|=========================================|
|imsm_disk[imsm_super->num_disks]         |
|=========================================|
|imsm_dev[imsm_super->num_raid_devs]      |
|=========================================|
||---------------------------------------||
||imsm_vol[0]                            ||
|||=====================================|||
|||imsm_map[1]                            |
.
.
|||=====================================|||
||---------------------------------------||
|=========================================|
||---------------------------------------||
||imsm_vol[1]                            ||
|||=====================================|||
|||imsm_map[1]                            |
.
.
|||=====================================|||
||---------------------------------------||
|=========================================|
.
.
"""
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


def print_imsm_super(imsm_super: IMSM_SUPER):
    print("Magic : %s".format(imsm_super.sig[: len(MAGIC)]))
    print("Version : %s".format(imsm_super.sig[len(MAGIC) :]))
    print("Orig Family: " + hex(imsm_super.orig_family_num))
    print("Family: " + hex(imsm_super.family_num))
    print("Generation: " + hex(imsm_super.generation_num))
    print("Creation Time: " + time.ctime(imsm_super.creation_time))
    print("Disks: %d".format(imsm_super.num_disks))
    print("RAID Devices: %d".format(imsm_super.num_raid_devs))


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


def get_blocks_per_member(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.blocks_per_member_lo, imsm_map.blocks_per_member_hi)


def get_num_data_stripes(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.num_data_stripes_lo, imsm_map.num_data_stripes_hi)


def get_pba_of_lba0(imsm_map: IMSM_MAP):
    return join_u32(imsm_map.pba_of_lba0_lo, imsm_map.pba_of_lba0_hi)


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
        if metadata[-1 * len(MAGIC) :].decode() == MAGIC:
            return True
        elif metadata[-1 * len(MAGIC) + 1 :].decode() == MAGIC[1:]:
            print("Intel Raid Detected But Metadata has been deleted!!!")
            print("It has to be recovered manually!!")
            return False
    return False


def parse_metadata(file_name) -> tuple[IMSM_SUPER, list[IMSM_DISK], list[IMSM_DEV]]:
    metadata = read_first_meta_sec(file_name)
    disk_offset = 0

    FORMAT = "<32sLLLLLLBBBBLLLLHHQ"
    FORMAT_SIZE = calcsize(FORMAT)
    imsm_super = IMSM_SUPER._make(unpack(FORMAT, metadata[:FORMAT_SIZE]))
    disk_offset += 0xD8

    if imsm_super.mpb_size > SECTOR_SIZE:
        metadata += read_rest_meta_sec(file_name, imsm_super.mpb_size)

    if len(metadata) != imsm_super.mpb_size:
        print("SECTOR size error")
        exit(1)

    imsm_disk_l = []
    imsm_dev_l = []
    FORMAT = "<16sLLLLL"
    FORMAT_SIZE = calcsize(FORMAT)
    for _ in range(imsm_super.num_disks):
        imsm_disk_l.append(
            IMSM_DISK._make(
                unpack(FORMAT, metadata[disk_offset : disk_offset + FORMAT_SIZE])
            )
        )
        disk_offset += 0x30

    for _ in range(imsm_super.num_raid_devs):
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

        imsm_dev_l.append(imsm_dev)

    print(imsm_super)
    print(imsm_disk_l)
    print(imsm_dev_l)
    return (imsm_super, imsm_disk_l, imsm_dev_l)


def recover(
    imsm_disk_l: list[IMSM_DISK],
    imsm_dev_l: list[IMSM_DEV],
):
    LOCATION = "./Matrix RAID"
    print(imsm_disk_l)
    for dev in imsm_dev_l:
        strip_size = dev.imsm_vol.imsm_map.blocks_per_strip * SECTOR_SIZE
        stripes_count = get_num_data_stripes(dev.imsm_vol.imsm_map)
        start_lba = get_pba_of_lba0(dev.imsm_vol.imsm_map)
        raid_level = get_imsm_raid_level(dev.imsm_vol.imsm_map)
        disk_ord_tbl = dev.imsm_vol.imsm_map.disk_ord_tbl
        disk_fds = [
            open(
                os.path.join(
                    LOCATION, imsm_disk.serial.decode().rstrip("\x00") + ".img"
                ),
                "rb",
            )
            for imsm_disk in imsm_disk_l
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
            # array size = RAID 가 차지하는 전체 크기 ex) RAID1을 100, 100으로 하면 array는 200
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

            # TODO:
            # RAID0 tested
            # RAID1 tested
            # RAID5 tested
            # RAID10 not tested
            
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
                        # pass parity strip
                        if i != 0 and parity_idx == 0:
                            continue
                        buf += disk_fds[ord].read(strip_size)
                        f.write(buf)

        [fd.close() for fd in disk_fds]


if __name__ == "__main__":
    serial = ["S3YKNC0N108175B", "S3YKNX0M546512K"]

    FILE_NAME = "S3YKNC0N108175B.img"
    LOCATION = "./Matrix RAID"
    FILE_NAME = os.path.join(LOCATION, FILE_NAME)
    # SECTOR_SIZE = TODO: Sector size must be set by hand
    # Now SECTOR_SIZE is changed by function check_is_intel_raid
    if check_is_intel_raid(FILE_NAME) == False:
        print("Intel Raid is not detected")
        exit(1)
    print("Intel Raid has been detected")
    imsm_super, imsm_disk_l, imsm_dev_l = parse_metadata(FILE_NAME)
    FILE_NAME = "S3YKNX0M546512K.img"
    FILE_NAME = os.path.join(LOCATION, FILE_NAME)
    if check_is_intel_raid(FILE_NAME) == False:
        print("Intel Raid is not detected")
        exit(1)
    print("Intel Raid has been detected")
    imsm_super, imsm_disk_l, imsm_dev_l = parse_metadata(FILE_NAME)
    recover(imsm_disk_l, imsm_dev_l)


"""
| 포맷 | C형                | 파이썬 형        | 표준 크기 | 노트     |
| ---- | ------------------ | ---------------- | --------- | -------- |
| `x`  | 패드 바이트        | 값이 없습니다    |           | (7)      |
| `c`  | char               | 길이가 1인 bytes | 1         |          |
| `b`  | signed char        | 정수             | 1         | (1), (2) |
| `B`  | unsigned char      | 정수             | 1         | (2)      |
| `?`  | Bool              | bool             | 1         | (1)      |
| `h`  | short              | 정수             | 2         | (2)      |
| `H`  | unsigned short     | 정수             | 2         | (2)      |
| `i`  | int                | 정수             | 4         | (2)      |
| `I`  | unsigned int       | 정수             | 4         | (2)      |
| `l`  | long               | 정수             | 4         | (2)      |
| `L`  | unsigned long      | 정수             | 4         | (2)      |
| `q`  | long long          | 정수             | 8         | (2)      |
| `Q`  | unsigned long long | 정수             | 8         | (2)      |
| `n`  | `ssize_t`          | 정수             |           | (3)      |
| `N`  | `size_t`           | 정수             |           | (3)      |
| `e`  | (6)                | float            | 2         | (4)      |
| `f`  | float              | float            | 4         | (4)      |
| `d`  | double             | float            | 8         | (4)      |
| `s`  | char[]             | bytes            |           | (9)      |
| `p`  | char[]             | bytes            |           | (8)      |
| `P`  | void*              | 정수             |           | (5)      |
"""
