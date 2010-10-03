				  T2Tools

        [ Tape and disc tools for BBC and Electron emulator users ]


Created:        31st October 2000
WWW site:	http://www.boddie.org.uk/Projects/Emulation/T2Tools


Introduction

This package is a collection of tools which convert between various formats of
archive files related to the BBC and Acorn Electron microcomputers. In order to
run them, you need to obtain a Python interpreter for your computer platform.
Look at

  http://www.python.org/

for information regarding installation and usage of Python.

These tools also require the CMDSyntax module. This can be obtained from

  http://www.boddie.org.uk/david/Projects/Python/CMDSyntax


The Tools

There are four tools available:

INF2UEF.py	Takes a directory of files stored on the native
		file system with accompanying .inf files and stores
		them in a UEF file.

T2INF.py 	Converts Slogger T2 files, created by ROMs such as
		T2P3, T2P4, T2Peg400 or similar, to a directory of
		files on the native filesystem with accompanying
		.inf files which describe the files' attributes for
		emulators.

T2UEF.py	Converts Slogger T2 files to UEF files for use with
		ElectrEm (http://electrem.emuunlim.com/).

UEF2INF.py	Converts a UEF file to a directory containing files
		with their associated .inf files.


Contact address

You can contact me (David Boddie) at david@boddie.org.uk
