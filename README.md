# AIRR
--------------
***AIRR*** (AMD & Intel RAID Reconstructor) is a tool for reconstructing (or reassembling) RAID image and checking RAID configuration for live system.

AIRR supports these functions for two RAID service: **Intel RST** & **AMD RAIDXpert2**.

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
There are three modes in AIRR: Dead, Live, Helper

Dead for reassembling RAID images to one image.

Alive for checking whether Live system is using RAID or not and even if system is not using RAID, AIRR checks the evidence that storage had been used for consisting RAID.

Helper for assisting RAID reconstruction, especially for Intel RAID.

### Dead system (Image reassemble)
For dead system we can select dead for `--mode' option.
```
$ python3 main.py --mode dead --system Intel --help 
$ python3 main.py --mode dead --system AMD -r --files image_file1.img image_file2.img --output_path .
$ python3 main.py --mode dead --system AMD --history
```
**In case of *Intel RAID***. The name of the image file should be the **Serial Number** of the product.

```
$ python3 main.py --mode dead --system Intel -r --files S3YKNC0N108175B.img S3YKNC0Z134189U.img --output_path .
```

### Live system
For dead system we can select live for `--mode' option.
If you select live then AIRR will check every artifacts related to RAID in system.
```
$ python3 main.py live
```

### Helper 
If you select helper, then you can choose two actions: reconstruct image and check helper message.

To reconstrut Intel RAID volume you should follow two steps
1. Check helper message
2. Trying reconstruction

For step1, AIRR assumes no more metadata in disk and tries to find hints for reconstruction.
AIRR searches
1. Disk ordering
2. RAID level
3. Start offset list

You can check the helper message like below

```python
$ python3 main.py --mode helper --system Intel -r --files file1.img file2.img
Checking disk order...
Found Partition Record. First disk: S1SUNSAG353817Z.img, Offset: 0x200
Checking RAID level...
Gussed RAID level: RAID0
Checking start offset...
Might take some time...
Start offset candidates: {0, 8388608, 118758178816, 118749790208}
```
By using these hints, we can try reconstruction.

Unfortunately, guessing stripe size rely on human guessing.
**However**, depends on file system, we can get few useful informations for guessing stripe size.
For example, for NTFS, we can utilize $Upcase file([128KB file full of capital letters](https://flatcap.github.io/linux-ntfs/ntfs/files/upcase.html)).

For step2, AIRR requires additional helper_args.

The usage is simple, just add arguments for --helper_args like below. 

```python
$ python3 main.py --mode helper --system Intel -r --files file1.img file2.img --helper_args 65536 0 118749790208 0
```

When you reconstruct deleted volume 

**The order of the image file name** stands for the order of the disk.

Therefore, the first disk must come first.

# Requirements
--------------
No package dependency needed for reassembling disk images.

However, for Live system checking, we need to solve two problems for this project.

 1. Window API
 2. Driver Info

First, to accomplish the first one we use pywin32 package.
It is needed for read exact size of the stoarge.

Second, to get exact information about driver and stoage, we use CrystalDiskInfo.

It will be included in release version, so you don't have to download it.

```
python -m pip install pywin32
```
