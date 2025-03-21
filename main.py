import os, sys
from dead import Intel, AMD
import argparse
from live import live_system_check
import helper


ASCII_LOGO = '''
██╗    ██╗                
 ██╗  ██╔╝                               ███╗
  ██╗██╔╝                          ██╗   ╚═██╗
   ███╔╝         ██╔███╗  ██████   ╚═╝ ██████║
  ██╔██╗  █████╗ ████╔██╗██╔══██╗  ██╗██╔══██║
 ██╔╝ ██╗ ╚════╝ ██╔═╝╚═╝██║  ███╗ ██║██║  ██║
██╔╝   ██╗       ██║      █████╔██╗██║ ██████║
╚═╝    ╚═╝       ╚═╝       ╚═══╝╚═╝╚═╝  ╚════╝
'''

if __name__ == "__main__":

    print(ASCII_LOGO)
    print("X-raid (RAID Scanning, Reconstruction, and Recovery on Intel & AMD RAID Systems)\n")

    parser = argparse.ArgumentParser(
        description="",
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
        "--scan",
        choices=["quick", "deep"],
        help="Type of scan: quick | deep",
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

    parser.add_argument("-v", "--verbose", action="store_true", help="AIRR will try to provide detailed and extensive info. Default value is True")

    parser.add_argument(
        "-r", "--reconstruct", action="store_true", help="Reconstruct Virtual Disk"
    )

    parser.add_argument("--files", action="extend", nargs='+', help="Files for reconstruction")
        
    parser.add_argument("--index", help="Index number of history (AMD RAID only)", default=-1, type=int)

    parser.add_argument("--output_path", help="Output directory of reconstructed VDisk", type=str)

    parser.add_argument("--helper_args", action="extend", nargs='+', help="Args for helper mode: stripe size, start offset, vdisk size, raid level", type=int)
    args = parser.parse_args()

    if args.system is None and args.mode == "live":
        live_system_check()
        exit(0)
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
                AMD.print_info(args.files[0], args.verbose, args.index)
            elif args.reconstruct:
                print(args.files)
                print(args.output_path)
                AMD.reconstruct(args.files, args.output_path, args.index)
        else :
            pass

        if args.scan == "quick":
            print("Quick scan mode start")

            if args.files:
                print(len(args.files),"file(s) detected")
                file_count = 0
                for file in args.files:
                    file_count = file_count+1
                    print("\n[%s]"%file_count, file)
                    Intel.quick_scan(file)
                    AMD.quick_scan(file)
            else:
                print("\033[31mError\033[0m: At least one input file is required. Please provide one or more files.")
            exit(0)

        elif args.scan == "deep":
            continue_yn = input("\033[31mWarning\033[0m: Deep scan mode may take a long time. Do you want to \033[32mcontinue\033[0m? (y/n) ")
            if continue_yn in ["y", "Y"]:
                system_select = input("Please specify the RAID system you want to deep scan. (\033[34mIntel\033[0m/\033[38;5;214mAMD\033[0m) ")
                if system_select in ["intel", "Intel"]:
                    print("\nDeep scan mode start - \033[34mIntel\033[0m")
                    if args.files:
                        print(len(args.files), "file(s) detected")
                        file_count = 0
                        for file in args.files:
                            file_count = file_count + 1
                            print("\n[%s]" % file_count, file)
                            Intel.deep_scan(file)
                    else:
                        print(
                            "\033[31mError\033[0m: At least one input file is required. Please provide one or more files.")
                        exit(0)
                    exit(0)

                elif system_select in ["AMD", "amd"]:
                    print("\nDeep scan mode start - \033[38;5;214mAMD\033[0m")
                    if args.files:
                        print(len(args.files), "file(s) detected")
                        file_count = 0
                        for file in args.files:
                            file_count = file_count + 1
                            print("\n[%s]" % file_count, file)
                            AMD.deep_scan(file)
                    else:
                        print(
                            "\033[31mError\033[0m: At least one input file is required. Please provide one or more files.")
                        exit(0)
                    exit(0)
                else:
                    print(
                        "\033[31mError\033[0m: Please input Intel(intel) or AMD(amd)")
                    exit(0)

            elif continue_yn == "n" or continue_yn == "N":
                print("\nDeep scan mode suspended")
                exit(0)

            else:
                print("\n\033[31mError\033[0m: Please input Y(y) or N(n)")
                exit(0)

    elif args.mode == "helper":
        if args.system == "Intel":
            if args.reconstruct and args.files and not args.helper_args:
                helper.reconstruct_helper(args.files, args.output_path)
            elif args.reconstruct and args.files and args.helper_args:
                helper.reconstruct(args.files, args.helper_args[0], args.helper_args[1], args.helper_args[2],
                                   args.helper_args[3], args.output_path)
            else:
                print("Please check arguments")
                parser.print_help()
        else:
            print("Helper mode only supports Intel RAID")

    if args.help:
        parser.print_help()
        exit(0)

    elif args.system is None or args.mode is None:
        print("Please check argument!!")
        print(
            """ex)\n 
            Live:
            \tpython3 main.py --mode live 
            Dead:
            \tpython3 main.py --mode dead --scan [quick or deep] --files file1.img file2.img
            \tpython3 main.py --mode dead --system Intel --help 
            \tpython3 main.py --mode dead --system Intel -r --files file1.img file2.img --output_path . 
            \tpython3 main.py --mode dead --system AMD -r --files file1.img file2.img --index 10 --output_path . 
            \tpython3 main.py --mode dead --system AMD -i
            \tpython3 main.py --mode dead --system AMD -i --index 4
            \tpython3 main.py --mode dead --system AMD --history    
            Helper:
            \tpython3 main.py --mode helper --system Intel -r --files file1.img file2.img
            \tpython3 main.py --mode helper --system Intel -r --files file1.img file2.img --helper_args 65536 0 118749790208 0"""
        )
        exit(0)
