                        T2Tools - enhanced release

        [ Tape and disc tools for BBC and Electron emulator users ]


Created:        31st October 2000
Updated:        3rd May 2002
WWW site:       http://david.boddie.org.uk/Projects/Emulation/T2Tools


Introduction

This package is a collection of Python scripts which convert between
various formats of archive files related to the BBC and Acorn Electron
microcomputers. In order to run them, you need to obtain a Python
interpreter for your computer platform. Look at

http://www.python.org/

for information regarding installation and usage of Python.

Each tool has now been modified to use the CMDSyntax library, which is
included with this package. One consequence of this is that a graphical
user interface will be presented to users who want to avoid running the
scripts from the command line.


The Tools

There are six scripts available:

ADF2INF.py      Extracts files from ADFS disc images and stores
                them in directories on the native filesystem with
                suitable .inf files. Disc images are usually files
                with the suffix .adf or similar.
                Should be able to deal with 160K, 320K (F format),
                640K (L format), 800K (D and E format) and 1600K
                (E format) disc images.

INF2UEF.py      Takes a directory of files stored on the native
                file system with accompanying .inf files and stores
                them in a UEF file.

T2INF.py        Converts Slogger T2 files, created by ROMs such as
                T2P3, T2P4, T2Peg400 or similar, to a directory of
                files on the native filesystem with accompanying
                .inf files which describe the files' attributes for
                emulators.

T2UEF.py        Converts Slogger T2 files to UEF files for use with
                ElectrEm (http://electrem.emuunlim.com/).

UEF2INF.py      Converts a UEF file to a directory containing files
                with their associated .inf files.

UEFtrans.py     A utility for manipulating UEF files.


Contact address

You can contact me (David Boddie) at david@boddie.net
