# X-raid
--------------
***X-raid*** (RAID Scanning, Reconstruction, and Recovery for Intel & AMD RAID Systems) is a tool designed to automate the reconstruction of RAID images, particularly for Intel & AMD RAID systems. Check the Usage section for more details.

1. [X-raid](#x-raid)
2. [Options](#options)
3. [Usage](#usage)
4. [Requirements](#requirements)

# Options

```
$ python main.py [--mode {dead,live,helper}] [--system {Intel,AMD}] [-h] [-H] [-i] [-v] [-r] [--files FILES] [--output_path OUTPUT_PATH]
```

|option|Description|
|------|----|       
| --mode {dead, live, helper}         | Select the mode: dead \| live \| helper (Only for Intel) |
| --system {Intel,AMD}          |Select the system type: Intel \| AMD|
| -h, --help                    |Show help message for each system|
| -H, --history                 |Show history of virtual disk (Only for AMD)|
| -i, --info                    |Show virtual disk Information|
| -v, --verbose                 |Enable verbose mode for detailed output|
| -s, --scan                    |Select the scan type: quick \| deep|
| -r, --reconstruct_recovery             |Reconstruct or recovery virtual disk|
| --files FILES                 |Specify files for reconstruction|
| --output_path OUTPUT_PATH     |Set the output directory for the reconstructed virtual disk|
| --helper_args                 |Set additional arguments for helper mode (Only for helper mode)|

# Usage
**X-raid** offers three modes for different purposes

1. Dead: Scan, Reconstruct or Recovery virtual disk
2. Live: Check live systems for RAID usage
3. Helper: Assist with Intel RAID reconstruction


## Dead system (Image Reconstruct)
This mode allows you to reconstruct or recover separate RAID-configured storage devices into a single volume, or simply scan to check if image files are part of an Intel/AMD RAID system.

Use the --mode dead option.

**Examples**
```
# Get help for dead mode with Intel system
$ python3 main.py --mode dead --system Intel --help  

# Scan disk image files to check whether they are part of an Intel/AMD RAID system
$ python3 main.py --mode dead --scan quick --files [image_file_01.img] [image_file_02.img]
$ python3 main.py --mode dead --scan deep --files [image_file_01.img] [image_file_02.img]

# Reconstruct AMD RAID images with default output path
$ python3 main.py --mode dead --system AMD -r --files [image_file_01.img] [image_file_02.img] --output_path .  

# Reconstruct Intel RAID with custom output path (Serial number used as image file name)
$ python3 main.py --mode dead --system Intel -r --files [image_file_01.img] [image_file_02.img] --output_path /path/to/output  
```
**Note**: For Intel RAID, the image file names should match the product's serial numbers.


## Live system
This mode checks whether the live system is currently using RAID and searches for evidence of past RAID usage on storage devices.

Use the --mode live option.

**Example**

```
$ python3 main.py --mode live  # Check live system for RAID usage
```

## Helper 
This mode helps with Intel RAID reconstruction in two steps:

1. Check helper message
2. Trying reconstruction

### Step1: Check Helper Message

**X-raid** analyzes the image files to gather reconstruction hints, such as disk order, RAID level, and start offset candidates. 

Use the --mode helper --system Intel options.

**Example**

```python
$ python3 main.py --mode helper --system Intel -r --files S1SUNSAG353817Z.img S3YKNC0Z134189U.img
Checking disk order...
Found Partition Record. First disk: S1SUNSAG353817Z.img, Offset: 0x200
Checking RAID level...
Guessed RAID level: RAID0
Checking start offset...
Might take some time...
Start offset candidates: {0, 8388608, 118758178816, 118749790208}
```

### Step2: Reconstruction (Requires additional arguments)
Based on the information from *step 1*, you can attempt reconstruction using the --helper_args option. 

The option arguments are as follows: stripe size, start offset, vdisk size, raid level.

Options are used to specify additional informations for reconstruction, such as stripe size. 

Since stripe size cannot be determined automatically, you may need to test values like 16KB, 32KB, 64KB, or 128KB manually.

**However**, certain file systems can help infer the stripe size.
For example, for NTFS, we can utilize $Upcase file([128KB file full of capital letters](https://flatcap.github.io/linux-ntfs/ntfs/files/upcase.html)).

More details can be found in the PDF file located in src.

**Example**
Inferred arguments in *step 1* are order of disks, RAID level, and candidates of start offset. 

Then we can try reconstruction with inferenced values.
```python
$ python3 main.py --mode helper --system Intel -r --files S1SUNSAG353817Z.img S3YKNC0Z134189U.img --helper_args 65536 0 118749790208 0
```
**Note**
When reconstructing deleted volumes, 
the order of the image file names must match the actual order of the disks (first disk comes first in the file names).
The virtual disk size in the example is set to the largest difference between the start offset candidates.

# Requirements
--------------
No additional packages are required for reconstructing disk images.

However, for live system checking, two dependencies need to be installed

1. pywin32: Used to read storage size accurately. Install it with python -m pip install pywin32.
2. CrystalDiskInfo: Provides detailed information about drivers and storage. This tool will be included in the release. 

**Install**
```
python -m pip install pywin32
```
