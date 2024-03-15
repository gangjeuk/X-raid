# AIRR
--------------
***AIRR*** (AMD & Intel RAID Reconstructor) is a tool designed to help with reassembling RAID images and assisting with RAID reconstruction, especially for Intel & AMD RAID.


# Option
```
$ python main.py [--mode {dead,live,helper}] [--system {Intel,AMD}] [-h] [-H] [-i] [-v] [-r] [--files FILES] [--output_path OUTPUT_PATH]
```
|option|help|
|------|----|       
| --mode {dead, live, helper}         | Type of system: dead \| live \| helper(Only for Intel) |
| --system {Intel,AMD}          |Type of system: Intel \| AMD|
| -h, --help                    |Show each system's help message|
| -H, --history                 |Show history of Virtual Disk (Only for AMD)|
| -i, --info                    |Show Virtual Disk Information|
| -v, --verbose                 |verbose mode|
| -r, --reconstruct             |Reconstruct Virtual Disk|
| --files FILES                 |Files for reconstruction|
| --output_path OUTPUT_PATH     |Output directory of reconstructed VDisk|
| --helper_args                 | Args for helper mode(Only for helper mode)|

## Usage
AIRR offers three modes for different purposes

1. Dead: Image Reassemble
2. Live: Live system checking
3. Helper: Helps with Intel RAID reconstruction


### Dead system (Image reassemble)
This mode allows you to reassemble separate RAID configured storages into a single volume.

Use the --mode dead option.

**Examples**
```
$ python3 main.py --mode dead --system Intel --help  # Get help for dead mode with Intel system
# Reassemble AMD RAID images with default output path
$ python3 main.py --mode dead --system AMD -r --files image_file1.img image_file2.img --output_path .  
# Reassemble Intel RAID with custom output path (Serial number used as image file name)
$ python3 main.py --mode dead --system Intel -r --files S3YKNC0N108175B.img S3YKNC0Z134189U.img --output_path /path/to/output  
```
**Note**: For Intel RAID, the image file names should match the product's serial number.


### Live system
This mode checks whether the live system is currently using RAID and searches for evidence of past RAID usage on the storage devices.

Use the --mode live option.

**Example**
```
$ python3 main.py --mode live  # Check live system for RAID usage
```

### Helper 
This mode helps with Intel RAID reconstruction in two steps:

1. Check helper message
2. Trying reconstruction

### Step1: Check Helper Message

AIRR analyzes the image files to find hints for reconstruction, including disk order, RAID level, and start offset list. 

Use the --mode helper --system Intel options.

**Example**
```python
$ python3 main.py --mode helper --system Intel -r --files S1SUNSAG353817Z.img S3YKNC0Z134189U.img
Checking disk order...
Found Partition Record. First disk: S1SUNSAG353817Z.img, Offset: 0x200
Checking RAID level...
Gussed RAID level: RAID0
Checking start offset...
Might take some time...
Start offset candidates: {0, 8388608, 118758178816, 118749790208}
```

### Step2: Reconstruction (Requires additional arguments)
Based on the information from *step 1*, you can attempt reconstruction using the --helper_args option. 

This option specifies additional information for reconstruction, such as stripe size.

Unfortunately, guessing stripe size rely on human guessing.

**However**, depends on file system, we can get few useful informations for guessing stripe size.
For example, for NTFS, we can utilize $Upcase file([128KB file full of capital letters](https://flatcap.github.io/linux-ntfs/ntfs/files/upcase.html)).

More details can be found in .pdf file in `src`.

**Example**
```python
$ python3 main.py --mode helper --system Intel -r --files file1.img file2.img --helper_args 65536 0 118749790208 0
```
**Note**
When reconstructing deleted volumes, 
the order of the image file names must match the actual order of the disks (first disk comes first in the file names).

# Requirements
--------------
No package dependency needed for reassembling disk images.

However, for checking live systems, you'll need:

However, for Live system checking, we need to solve two problems for this project.

1. pywin32: This package is used to read storage size accurately. Install it with python -m pip install pywin32.
2. CrystalDiskInfo: This tool provides detailed information about drivers and storage. It will be included in the release

**Install**
```
python -m pip install pywin32
```
