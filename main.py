import os, sys
from dead import Intel, AMD
import argparse
from live import live_system_check
import helper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AIRR(AMD & Intel RAID Reconstructor)",
        add_help=False,
    )

    parser.add_argument(
        "--mode",
        choices=["dead", "live", "helper"],
        help="Mode selection: dead | live | helper",
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

    parser.add_argument("--helper_args", action="extend", nargs='+', help="Args for helper mode: stripe size, start offset, end offset, raid level", type=int)
    args = parser.parse_args()

    if args.help or args.system is None or args.mode is None:
        print(args.system)
        parser.print_help()
        print(
            """ex)\n 
            Live:
            \tpython3 main.py --mode live 
            Dead: 
            \tpython3 main.py --mode dead --system Intel --help \n
            \tpython3 main.py --mode dead --system AMD -r --files file1.img file2.img \n 
            \tpython3 main.py --mode dead --system AMD --history \n
            Helper:
            \tpython3 main.py --mode helper --system Intel -r --files file1.img file2.img
            \tpython3 main.py --mode helper --system Intel -r --files file1.img file2.img --helper_args 65536 0 118749790208 0"""
        )
        exit(0)
    if args.mode == "live":
        live_system_check()
    elif args.mode == "dead":
        if args.system == "Intel":
            if args.history:
                print("No history check for Intel")
            elif args.info:
                Intel.print_info(args.files[0], args.verbose)
            elif args.reconstruct:
                Intel.reconstruct(args.files, args.output_path)

        elif args.system == "AMD":
            if args.history:
                AMD.print_history(args.files[0])
            elif args.info:
                AMD.print_info(args.files[0], args.verbose)
            elif args.reconstruct:
                print(args.files)
                print(args.output_path)
                AMD.reconstruct(args.files, args.output_path)
                
    elif args.mode == "helper":
        if args.system == "Intel":
            if args.reconstruct and args.files and not args.helper_args:
                helper.reconstruct_helper(args.files, args.output_path)
            elif args.reconstruct and args.files and args.helper_args:
                helper.reconstruct(args.files, args.helper_args[0], args.helper_args[1], args.helper_args[2], args.helper_args[3], args.output_path)
            else:
                print("Please check arguments")
                parser.print_help()
        else:
            print("Helper mode only supports Intel RAID")