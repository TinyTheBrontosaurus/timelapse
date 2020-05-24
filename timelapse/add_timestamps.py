import argparse
import sys
import pathlib


def main(argv):

    parser = argparse.ArgumentParser(description="Create timestamp labels on a time lapse video clip")

    parser.add_argument("input_filename", type=pathlib.Path, help="Path to input video (read-only)")
    parser.add_argument("-o", dest="output_filename", type=pathlib.Path, help="Path to output file")
    parser.add_argument("-f", action="store_true", help="Force overwrite of output file")

    args = parser.parse_args(argv)

    input_filename = args.input_filename
    output_filename = args.output_fiename
    overwrite_output = args.force



if __name__ == "__main__":
    main(sys.argv[1:])