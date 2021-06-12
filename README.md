# EDItool

Tool for talking to ENE ECs (e.g. KB9022) via the ENE Debug Interface (EDI).

## Example usage

Read some data

~~~
$ ./edi.py ftdi://ftdi:4232/2 0xff24
ff24: 07
~~~

Write some data

~~~
$ ./edi.py ftdi://ftdi:4232/2 0xffab 0x00
~~~

... or in some python shell:

~~~
import edi
> e = edi.EDI("ftdi://ftdi:4232:FT61I7D6/2")
> e.dump(0, 0x40)
0000: 00 00 00 00  00 00 00 00  c0 0c 00 00  c0 00 00 00
0010: 00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0020: 00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0030: df ff ff ff  f7 ff ff ff  3f f3 ff f5  ff ff ff ff
~~~

## License

Copyright (c) 2021 Michael Niewöhner

This is open source software, licensed under GPLv2. See LICENSE file for details.
