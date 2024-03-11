# AIRR
--------------
***AIRR*** (AMD & Intel RAID Reconstructor) is a tool for reconstructing (or reassembling) RAID image and checking RAID configuration for live system.

AIRR supports these functions for two RAID service: **Intel RST** & **AMD RAIDXpert2**.

# Option
```
$ python main.py [--mode {dead,live}] [--system {Intel,AMD}] [-h] [-H] [-i] [-v] [-r] [--files FILES] [--output_path OUTPUT_PATH]
```
|option|help|
|------|----|       
| --mode {dead,live}         | Type of system: dead \| live|
| --system {Intel,AMD}          |Type of system: Intel \| AMD|
| -h, --help                    |Show each system's help message|
| -H, --history                 |Show history of Virtual Disk (Only for AMD)|
| -i, --info                    |Show Virtual Disk Information|
| -v, --verbose                 ||
| -r, --reconstruct             |Reconstruct Virtual Disk|
| --files FILES                 |Files for reconstruction|
| --output_path OUTPUT_PATH     |Output directory of reconstructed VDisk|

## Usage
There are three modes in AIRR: Dead, Live, Helper

Dead for reassembling RAID images to one image.

Alive for checking whether Live system is using RAID or not and even if system is not using RAID, AIRR checks the evidence that storage had been used for consisting RAID.

Helper for assisting RAID reconstruction, especially for Intel RAID.

### Dead system (Image reassemble)
For dead system we can select dead for `--mode' option.
```
$ python3 main.py dead system Intel --help 
$ python3 main.py dead system AMD -r --files image_file1.img image_file2.img
$ python3 main.py dead system AMD --history
```
**In case of *Intel RAID***. The name of the image file should be the **Serial Number** of the product.

```
$ python3 main.py dead system Intel -r --files S3YKNC0N108175B.img S3YKNC0Z134189U.img
```

### Live system
For dead system we can select live for `--mode' option.
If you select live then AIRR will check every artifacts related to RAID in system.
```
$ python3 main.py live
```

### Helper 
If you select helper, then you can choose two actions: reconstruct image and check helper message.

AIRR assumes no more metadata in disk and tries to find hints for reconstruction.
AIRR searches
1. Disk ordering
2. RAID level
3. Start offset list

By using these hints, we can try reconstruction.

Unfortunately, guessing stripe size rely on human guessing.
**However**, depends on file system, there are few competent informations for guessing stripe size.
For example, for NTFS, we can utilize $Upcase file([https://flatcap.github.io/linux-ntfs/ntfs/files/upcase.html](128KB file full of capital letters)).

```python
$ python .\main.py --status dead --system Intel -rh --files dataset\raid0.deleted\S1SUNSAG353817Z.img dataset\raid0.deleted\S3YKNX0K713881M.img
Checking disk order...
Found Partition Record. First disk: .\data\Intel\dataset\raid0.deleted\S1SUNSAG353817Z.img, Offset: 0x200
Checking RAID level...
Gussed RAID level: RAID0
Checking start offset...
Might take some time...
Start offset candidates: {0, 8388608, 118758178816, 118749790208}
```

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
