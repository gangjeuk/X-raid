# Dataset

Dataset for AMD & Intel RAID

There are eight total cases:

AMD - Normal & Deleted

Intel - Normal & Deleted

Due to their large size, the files are uploaded to cloud storage.

Here's the link: [Image files](https://drive.google.com/drive/folders/1HN7gZ99xrn05FYJwakcVAFjw2Wbtg18X?usp=sharing)

## AMD RAID

AMD datasets were created using RAIDXpert2-enabled motherboards. Unlike Intel, AMD firmware RAID **preserves historical metadata**, allowing for **automated recovery of deleted volumes using version index**.

## Intel RAID

Intel RAID datasets were generated using motherboards equipped with Intel Rapid Storage Technology (RST). Since metadata is overwritten upon virtual disk deletion, **manual parameter estimation is required** for recovery (e.g., stripe size, disk order). X-raid provides a helper mode to assist with this.

### Dataset Scenarios

| Dataset ID | System | Configured RAID Levels   | Deleted Virtual Disk   | Number of Disks | Evaluation Purpose                         |
|------------|--------|---------------------------|-------------------------|------------------|---------------------------------------------|
| I-1        | Intel  | RAID 0 (x2)               | First RAID 0            | 2                | Recovery of deleted RAID 0 volume          |
| I-2        | Intel  | RAID 0, 1                 | None                    | 2                | Verification of normal RAID 0 and 1        |
| I-3        | Intel  | RAID 0, 1                 | RAID 1                  | 2                | Recovery of deleted RAID 1 volume          |
| I-4        | Intel  | RAID 10, 5                | None                    | 4                | Reconstruction of normal RAID 10 and 5     |
| I-5        | Intel  | RAID 10, 5                | RAID 5                  | 4                | Recovery of deleted RAID 5 volume          |
| I-6        | Intel  | RAID 0, 5                 | None                    | 3                | RAID 0 and 5 reconstruction evaluation      |
| A-1        | AMD    | RAID 0, 1, 5, 10, JBOD    | None                    | 4                | Evaluation of RAID detection and handling  |
| A-2        | AMD    | RAID 0, 1, 5, 10, JBOD    | RAID 0, 1, 5, 10        | 4                | Recovery of deleted volumes via index      |

