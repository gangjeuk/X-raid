# Dataset

Dataset for Intel & AMD RAID

There are four total cases:

Intel - Normal & Deleted

AMD - Normal & Deleted

Due to their large size, the files are uploaded to cloud storage.

Here's the link: [Image files](https://drive.google.com/drive/folders/1HN7gZ99xrn05FYJwakcVAFjw2Wbtg18X?usp=sharing)

The following sections detail the data structure transitions for each case, along with visual representations.

## AMD RAID

- Volume Creation: Three volumes were created, each utilizing three storage devices.
- RAID Levels: Each volume was assigned a distinct RAID level:
    - Volume 1: RAID 0
    - Volume 2: RAID 1
    - Volume 3: JBOD
- Volume Deletion: Subsequently, the RAID 0 volume (Volume 1) was deleted.
The data structure transition for AMD RAID is visualized in the image below

![AMD](https://anonymous.4open.science/r/AIRR/src/img/AMD%20delete.png)

## Intel RAID

- Volume Creation: Two volumes were created, each utilizing two storage devices.
- Unified RAID Level: Both volumes were configured with the same RAID0
- Volume Deletion: Following creation, the first volume was deleted.
The data structure transition for Intel RAID is visualized in the image below

![Intel](https://anonymous.4open.science/r/AIRR/src/img/Intel%20delete.png)


