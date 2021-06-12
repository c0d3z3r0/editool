#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

__title__       = "EDItool"
__description__ = "Tool for talking to ENE ECs via the ENE Debug Interface (EDI)"
__author__      = "Michael Niewöhner"
__email__       = "foss@mniewoehner.de"
__license__     = 'GPL-2.0-or-later'
__copyright__   = 'Copyright (c) 2021 Michael Niewöhner'

from argparse import ArgumentParser
from pyftdi.spi import SpiController

class CMD:
    READ  = 0x30
    WRITE = 0x40

class ADDR:
    EFA0  = 0xfea8
    EFA1  = 0xfea9
    EFA2  = 0xfeaa
    EFDAT = 0xfeab
    EFCMD = 0xfeac
    EFCFG = 0xfead

class EFCMD:
    READ  = 0x03

class EFCFG:
    ENABLE = 1 << 3
    BUSY   = 1 << 1

class EDI:

    def __init__(self, dev):
        self._ctrl = SpiController(cs_count=1)
        self._ctrl.configure(dev, turbo=True)
        self._ctrl.ftdi.set_latency_timer(1)
        self._spi = self._ctrl.get_port(cs=0)
        self._flash_enabled = False

        # EDI enables when it detects a frequency between 1-8 MHz.
        # Issue a 32 byte read at 4 MHz to trigger this.
        self._spi.set_frequency(4e6)
        self._spi.read(32)

        # Now switch to 16 MHz
        self._spi.set_frequency(16e6)

    def close(self):
        self._ctrl.terminate()

    def read(self, addr):
        rlen = 4
        cmd = [CMD.READ]
        cmd.extend(list(addr.to_bytes(3, 'big')))

        while True:
            data = self._spi.exchange(cmd, rlen)
            try:
                idx_data = data.index(0x50) + 1
                return data[idx_data]
            except (ValueError, IndexError):
                if rlen >= 30:
                    raise(Exception("Read timeout."))
                rlen += 2

    def write(self, addr, data):
        cmd = [CMD.WRITE]
        cmd.extend(list(addr.to_bytes(3, 'big')))
        cmd.append(data)
        self._spi.exchange(cmd)

    def enable_flash(self):
        if not self._flash_enabled:
            self.write(ADDR.EFCFG, EFCFG.ENABLE)
            self._flash_enabled = True

    def read_flash(self, addr):
        self.enable_flash()

        self.write(ADDR.EFA2,  addr >> 16 & 0xff)
        self.write(ADDR.EFA1,  addr >> 8  & 0xff)
        self.write(ADDR.EFA0,  addr       & 0xff)
        self.write(ADDR.EFCMD, EFCMD.READ)

        while self.read(ADDR.EFCFG) & EFCFG.BUSY:
            time.sleep(0.001)

        return self.read(ADDR.EFDAT)

    def _dump(self, read_func, start, end):
        # round start down to 16 byte boundary
        start -= start % 0x10
        alen = 4 if end <= 0x10000 else 8

        # read 16 byte per line
        for yaddr in range(start, end, 0x10):
            data = [read_func(addr) for addr in range(yaddr, yaddr + 0x10)]

            # cut in chunks of 4 byte each
            zip_data = zip(*[iter(data)]*4)
            # format data: ff ff ff ff  ff ff ff ff  ff ff ff ff  ff ff ff ff
            hex_data = '  '.join((map(lambda x: ' '.join(map("{:02x}".format, x)), zip_data)))

            print(f'{yaddr:0{alen}x}: {hex_data}')

    def dump(self, start, end):
        self._dump(self.read, start, end)

    def dump_flash(self, start, end):
        self._dump(self.read_flash, start, end)


def main():
        argp = ArgumentParser("EDItool", description=__description__)

        argp.add_argument('device', type=str,         help='serial port device name')
        argp.add_argument('-d',  action='store_true', help='dump all XDATA')
        argp.add_argument('-df', action='store_true', help='dump flash')
        rw = argp.add_argument_group()
        rw.add_argument('addr', nargs='?',            help='XDATA address')
        rw.add_argument('data', nargs='?',            help='XDATA data to be written')
        args = argp.parse_args()

        if not (args.d or args.addr):
            argp.error('Need either -d or addr')
        if not args.device:
            argp.error('Ftdi device not specified')

        edi = EDI(args.device)

        if args.d:
            edi.dump(0, 0x10000)

        elif args.df:
            edi.dump_flash(0, 128*1024)

        elif args.addr:
            addr = int(args.addr, 0)

            if args.data:
                data = int(args.data, 0)
                edi.write(addr, data)

            else:
                data = edi.read(addr)
                print(f'{addr:04x}: {data:02x}')

        edi.close()


if __name__ == '__main__':
    main()
