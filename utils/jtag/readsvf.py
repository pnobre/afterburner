#!/usr/bin/env python3
# Writes the .svf file that reads all the rows of the fuse array of an ATF150X device,
# used by the read operation of Afterburner. The SVF is then converted to XSVF:
#
#   python3 readsvf.py -d ATF1504AS read_ATF1504AS.svf
#   python3 svf2xsvf.py read_ATF1504AS.svf read_ATF1504AS.xsvf
#
# The sequence is the one fuseconv.py emits to verify a row (ISC_READ), but the mask is
# empty, so nothing is compared: the MCU sends the TDO data of each scan to the PC.

import argparse
import sys

from device import ATF15xxInstr, ATF1502ASDevice, ATF1504ASDevice

devices = {
    'ATF1502AS': ATF1502ASDevice,
    'ATF1504AS': ATF1504ASDevice,
}


def sir(file, instr):
    file.write("SIR 10 TDI ({:03x});\n".format(instr))


def write_svf(file, device):
    file.write("// read all rows of the fuse array\n")
    file.write("TRST ABSENT;\n")
    file.write("ENDIR IDLE;\n")
    file.write("ENDDR IDLE;\n")
    file.write("HDR 0;\n")
    file.write("HIR 0;\n")
    file.write("TDR 0;\n")
    file.write("TIR 0;\n")
    file.write("STATE RESET;\n")

    file.write("// check IDCODE\n")
    sir(file, ATF15xxInstr.IDCODE)
    file.write("SDR 32 TDI (fffeefff)\n\tTDO ({:08x})\n\tMASK (fffeefff);\n".format(device.idcode))

    file.write("// ISC enable\n")
    sir(file, ATF15xxInstr.ISC_CONFIG)
    file.write("SDR 10 TDI (1b9);\n")
    file.write("STATE IDLE;\n")

    for rows, cols in device.data_width.items():
        for row in rows:
            width = len(cols)
            zeros = '0' * ((width + 3) // 4)
            file.write("// ISC read row {}\n".format(row))
            sir(file, ATF15xxInstr.ISC_ADDRESS)
            file.write("SDR 11 TDI ({:03x});\n".format(row))
            sir(file, ATF15xxInstr.ISC_READ)
            file.write("RUNTEST IDLE 20E-3 SEC;\n")
            sir(file, ATF15xxInstr.ISC_DATA | (row >> 8))
            file.write("SDR {} TDI ({})\n\tTDO ({})\n\tMASK ({});\n".format(width, zeros, zeros, zeros))

    file.write("// ISC disable\n")
    sir(file, ATF15xxInstr.ISC_CONFIG)
    file.write("SDR 10 TDI (000);\n")
    file.write("STATE IDLE;\n")


def main():
    parser = argparse.ArgumentParser(description="Write the SVF file that reads the fuse array of an ATF150X.")
    parser.add_argument('-d', '--device', metavar='DEVICE', choices=sorted(devices), required=True,
                        help='Device: ' + ', '.join(sorted(devices)))
    parser.add_argument('output', type=argparse.FileType('w'), help='SVF file')
    args = parser.parse_args()
    write_svf(args.output, devices[args.device])


if __name__ == '__main__':
    main()
