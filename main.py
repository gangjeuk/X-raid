import os, sys
from dead import Intel, AMD
import argparse
from live import live_system_check
from helper import reconstruct_helper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AIRR(AMD & Intel RAID Reconstructor)",
        add_help=False,
    )

    parser.add_argument(
        "--status",
        choices=["dead", "live"],
        help="Type of system: dead | live",
        type=str,
    )
    
    parser.add_argument(
        "--system",
        choices=["Intel", "AMD"],
        help="Type of system: Intel | AMD",
        type=str,
    )

    parser.add_argument(
        "-h", "--help", action="store_true", help="Show each system's help message"
    )
    parser.add_argument(
        "-rh", "--reconstruct_helper", action="store_true", help="Help deleted Intel raid volume reconstruction"
    )
    parser.add_argument(
        "-H", "--history", action="store_true", help="Show history of Virtual Disk"
    )

    parser.add_argument(
        "-i", "--info", action="store_true", help="Show Virtual Disk Information"
    )

    parser.add_argument("-v", "--verbose", action="store_true")

    parser.add_argument(
        "-r", "--reconstruct", action="store_true", help="Reconstruct Virtual Disk"
    )

    parser.add_argument("--files", action="extend", nargs='+', help="Files for reconstruction")

    parser.add_argument("--output_path", help="Output directory of reconstructed VDisk", type=str)

    args = parser.parse_args()

    if args.help or args.system is None or args.status is None:
        print(args.system)
        parser.print_help()
        print(
            "ex) python3 main.py live \n python3 main.py dead system Intel --help \n python3 main.py dead system AMD -r --files file1.img file2.img \n python3 main.py dead system AMD --history"
        )
        exit(0)
    if args.status == "live":
        live_system_check()
    elif args.status == "dead":
        if args.system == "Intel":
            if args.reconstruct_helper:
                reconstruct_helper(args.files, args.output_path)
            elif args.history:
                print("No history check for Intel")
            elif args.info:
                Intel.print_info(args.files[0], args.verbose)
            elif args.reconstruct:
                Intel.reconstruct(args.files, args.output_path)

        elif args.system == "AMD":
            if args.help:
                AMD.print_help()
            elif args.history:
                AMD.print_history(args.files[0])
            elif args.info:
                AMD.print_info(args.files[0], args.verbose)
            elif args.reconstruct:
                print(args.files)
                print(args.output_path)
                AMD.reconstruct(args.files, args.output_path)

