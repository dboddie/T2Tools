#! /usr/bin/python

"""
    Name         : T2INF.py (was T2Peg400.py)
    Author       : David Boddie <davidb@mcs.st-and.ac.uk>
    Created      : Mon 28th August 2000
    Last updated : Fri 3rd May 2002
    Purpose      : Convert Slogger T2* files to files on a disc.
    WWW          : http://david.boddie.org.uk/Projects/Emulation/T2Tools

    License :

    This program is freeware. This means that it can be copied as long as it
    remains complete (in the form it was originally distributed) and is not
    charged for. If you want to use it in your own software then contacting
    me may prove beneficial since I may be able to provide a more up-to-date
    version.

    This program, although designed to extract all files from tape images,
    is intended for the extraction of users' own files from such images.

    Using this program to extract software which has been encoded in an
    image may be contravening the conditions of that software's license.

    You use this program entirely at your own risk.

    All copyrights and trademarks acknowledged.
"""

import sys, string, os
import cmdsyntax

def read_block(in_f):

    global eof
    
    # Read the alignment character
    align = in_f.read(1)

    if not align:
        eof = 1
        return ("", 0, 0, "", 0)

    align = ord(align)^90

    if align == 0x2b:
        eof = 1
        return ("", 0, 0, "", 0)

    # Default file attributes
    name = ""
    load = 0
    exec_addr = 0
    
    while 1:
        c = in_f.read(1)
        if not c:
            eof = 1
            return (name, 0, 0, "", 0)

        c = chr(ord(c)^90)

        if ord(c) == 0:
            break

        name = name + c


    load = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)+((ord(in_f.read(1))^90) << 16)+((ord(in_f.read(1))^90) << 24)

    exec_addr = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)+((ord(in_f.read(1))^90) << 16)+((ord(in_f.read(1))^90) << 24)

    block_number = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)

    if verbose == 1:
        if block_number == 0:
            print
            print name,
        print string.upper(hex(block_number)[2:]),

    block_length = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)

    if block_length==0:
        return (name, load, exec_addr, "", block_number)
    
    block_flag = ord(in_f.read(1))

    next_addr = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)

    header_crc = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)

    in_f.seek(2, 1)

    if list_files == 0:
        block = ""
        for i in range(0,block_length):
            byte = ord(in_f.read(1)) ^ 90
            block = block + chr(byte)
    else:
        in_f.seek(block_length, 1)
        block = ""
    
    block_crc = (ord(in_f.read(1))^90)+((ord(in_f.read(1))^90) << 8)
    
    return (name, load, exec_addr, block, block_number)


def get_leafname(path):

    pos = string.rfind(path, os.sep)
    if pos != -1:
        return path[pos+1:]
    else:
        return path


# Main program

version = "0.14c (Fri 3rd May 2002)"
syntax = "(-l [-v] <tape file>) | ([-name <stem>] [-v] <tape file> <destination path>)"

style = cmdsyntax.Style()
style.expand_single = 0
style.allow_single_long = 1

if style.verify() == 0:

    print "Internal problem: syntax style is inconsistent."
    sys.exit()

# Create a syntax object.
syntax_obj = cmdsyntax.Syntax(syntax, style)

matches = syntax_obj.get_args(sys.argv[1:], style = style)

if matches == [] and cmdsyntax.use_GUI() != None:

    form = cmdsyntax.Form("T2UEF", syntax_obj)
    
    matches = [form.get_args()]

# Take the first match.
match = matches[0]

# If there are no macthes then print the help text.
if match == {}:

    print "Syntax: T2INF.py "+syntax
    print
    print "T2INF version "+version
    print
    print "This program attempts to decode a tape file, <tape file>, produced by the"
    print "Slogger T2 series of ROMs for the Acorn Electron microcomputer and save the"
    print "files contained to the directory given by <destination path>."
    print "The load and execution addresses, and the file lengths are written to .inf"
    print "files corresponding to each file extracted." 
    print
    print "The options perform the following functions:"
    print
    print "-l              Lists the names of the files as they are extracted."
    print
    print "-name <stem>    Writes files without names in the format <stem><number>"
    print "                with <number> starting at 1."
    print
    print "-v              Verbose output."
    print
    sys.exit()

# Determine the platform on which the program is running

sep = os.sep

if sys.platform == "RISCOS":
    suffix = "/"
elif sys.platform == "DOS":
    suffix = "."
else:
    suffix = "."

# List files
if match.has_key("l"):
    list_files = 1
else:
    list_files = 0
    out_path = match["destination path"]

# Verbose output
if match.has_key("v"):
    verbose = 1
else:
    verbose = 0

# Stem for unknown filenames
if match.has_key("name"):

    stem = match["stem"]
else:
    stem = "noname"

# Read the input file name.
in_file = match["tape file"]


# Open the input file
try:
    in_f = open(in_file, "rb")
except IOError:
    print "The input file, "+in_file+" could not be found."
    sys.exit()

if list_files == 0:

    # Get the leafname of the output path
    leafname = get_leafname(out_path)

    # See if the output directory exists
    try:
        os.listdir(out_path)
    except:
        try:
            os.mkdir(out_path)
            print "Created directory "+out_path
        except:
            print "Directory "+leafname+" already exists."
            sys.exit()

in_f.seek(5, 1)        # Move to byte 5 in the T2 file

eof = 0                # End of file flag
out_file = ""          # Currently open file as specified in the block
write_file = ""        # Write the file using this name
file_length = 0        # File length
first_file = 1

# List of files already created
created = []

# Unnamed file counter
n = 1

while 1:
    # Read block details
    try:
        name, load, exec_addr, block, block_number = read_block(in_f)
    except IOError:
        print "Unexpected end of file"
        sys.exit()

    if list_files == 0:
        # Not listing the filenames

        if eof == 1:
            # Close the current output file
            out.close()
    
            # Write the file length information to the relevant file
            inf.write(string.upper(hex(file_length)[2:]+"\n"))
            inf.close()
            break
    
    #    # Either force new file or name in block is not the current name used
    #    if (write_file=="") | (name != out_file):
    #
    #        # New file, so close the last one (if there was one)
    #        if write_file != "":
    #            # Close the current output file
    #            out.close()
    #
    #            # Write the file length information to the relevant file
    #            inf.write(string.upper(hex(file_length)[2:]+"\n"))
    #            inf.close()
    
        # New file (block number is zero) or no previous file
        if (block_number == 0) | (first_file == 1):
    
            # Set the new name of the file
            out_file = name
            write_file = name
    
            # Open the new file with the new name
    
            if (write_file in created):
                write_file = write_file+"-"+str(n)
                n = n + 1
    
            if (write_file == ""):
                write_file = stem+str(n)
                n = n + 1
    
            # New file, so close the last one (if there was one)
            if first_file == 0:
                # Close the previous output file
                out.close()
    
                # Write the file length information and the NEXT parameter
                # to the previous .inf file
                inf.write(string.upper(hex(file_length)[2:]+"\tNEXT $."+write_file+"\n"))
                inf.close()
            else:
                first_file = 0

            # Reset the file length
            file_length = 0

            try:
                out = open(out_path + sep + write_file, "wb")
            except IOError:
                # Couldn't open the file
                write_file = stem+str(n)
                n = n + 1
                try:
                    out = open(out_path + sep + write_file, "wb")
                except IOError:
                    print "Couldn't open the file %s." % \
                            out_path + sep + write_file
                    sys.exit()
    
            # Add file to the list of created files
            created.append(write_file)
    
            try:
                # Open information file
                inf = open(out_path + sep + write_file + suffix + "inf", "w")
            except IOError:
                print "Couldn't open the information file %s." % \
                        out_path + sep + write_file + suffix + "inf"
                sys.exit()
    
            # Write the load and execution information to the relevant file
            inf.write( "$." + write_file + "\t" + string.upper(hex(load)[2:])+\
                       "\t" + string.upper(hex(exec_addr)[2:]) + "\t" )
    

        if block != "":
    
            # Write the block to the relevant file
            out.write(block)
    
            file_length = file_length + len(block)
    else:
        # Listing the filenames
        if eof == 1:
            break

        if (verbose == 0) & (block_number == 0):
            print name



# Close the input file
in_f.close()

# Exit
sys.exit()
