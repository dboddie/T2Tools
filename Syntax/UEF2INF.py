#! /usr/bin/python

"""
    Name            : UEF2INF.py
    Author          : David Boddie <davidb@mcs.st-and.ac.uk>
    Created         : Tue 21st November 2000
    Last updated    : Fri 3rd May 2002
    Purpose         : Convert UEF archives to files on a disc.
    WWW             : http://www.david.boddie.net/Software/Tape2Disc/
"""

import cmdsyntax, sys, string, os, gzip

def str2num(size, s):

    i = 0
    n = 0
    while i < size:

        n = n | (ord(s[i]) << (i*8))
        i = i + 1

    return n

            
def read_block(in_f):

    global eof

    while eof == 0:

        # Read chunk ID
        chunk_id = in_f.read(2)
        if not chunk_id:
            eof = 1
            break

        chunk_id = str2num(2, chunk_id)

        if chunk_id == 0x100 or chunk_id == 0x102:

            length = str2num(4, in_f.read(4))
            if (length > 1):
                # Read block
                data = in_f.read(length)
                break
            else:
                in_f.read(length)

        else:
            # Skip chunk
            length = str2num(4, in_f.read(4))
            in_f.read(length)

    if eof == 1:
        return ("", 0, 0, "", 0)

    # For the implicit tape data chunk, just read the block as a series
    # of bytes, as before
    if chunk_id == 0x100:

        block = data

    else:    # 0x102

        if UEF_major == 0 and UEF_minor < 9:

            # For UEF file versions earlier than 0.9, the number of
            # excess bits to be ignored at the end of the stream is
            # set to zero implicitly
            ignore = 0
            bit_ptr = 0
        else:
            # For later versions, the number of excess bits is
            # specified in the first byte of the stream
            ignore = data[0]
            bit_ptr = 8

        # Convert the data to the implicit format
        block = []
        write_ptr = 0

        after_end = (len(data)*8) - ignore
        while bit_ptr < after_end:

            # Skip start bit
            bit_ptr = bit_ptr + 1

            # Read eight bits of data
            bit_offset = bit_ptr % 8
            if bit_offset == 0:
                # Write the byte to the block
                block[write_ptr] = data[bit_ptr >> 3]
            else:
                # Read the byte containing the first bits
                b1 = data[bit_ptr >> 3]
                # Read the byte containing the rest
                b2 = data[(bit_ptr >> 3) + 1]

                # Construct a byte of data
                # Shift the first byte right by the bit offset
                # in that byte
                b1 = b1 >> bit_offset

                # Shift the rest of the bits from the second
                # byte to the left and ensure that the result
                # fits in a byte
                b2 = (b2 << (8 - bit_offset)) & 0xff

                # OR the two bytes together and write it to
                # the block
                block[write_ptr] = b1 | b2

            # Increment the block pointer
            write_ptr = write_ptr + 1

            # Move the data pointer on eight bits and skip the
            # stop bit
            bit_ptr = bit_ptr + 9

    # Read the block
    name = ""
    a = 1
    while 1:
        c = block[a]
        if ord(c) != 0: # was > 32:
            name = name + c
        a = a + 1
        if ord(c) == 0:
            break

    load = str2num(4, block[a:a+4])
    exec_addr = str2num(4, block[a+4:a+8])
    block_number = str2num(2, block[a+8:a+10])

    if verbose == 1:
        if block_number == 0:
            print
            print name,
        print string.upper(hex(block_number)[2:]),

    return (name, load, exec_addr, block[a+19:-2], block_number)


def get_leafname(path):

    pos = string.rfind(path, os.sep)
    if pos != -1:
        return path[pos+1:]
    else:
        return path


# Main program

version = '0.12c (Fri 3rd May 2002)'

style = cmdsyntax.Style()

style.allow_single_long = 1
style.expand_single = 0

if style.verify() == 0:

    print "Internal problem: syntax style is inconsistent."
    sys.exit()

syntax = "(-l [-v] <UEF file>) | ([-name <stem>] [-v] <UEF file> <destination path>)"

# Create a syntax object.
syntax_obj = cmdsyntax.Syntax(syntax, style)

matches = syntax_obj.get_args(sys.argv[1:], style = style)

if matches == [] and cmdsyntax.use_GUI() != None:

    form = cmdsyntax.Form("UEF2INF", syntax_obj)
    
    matches = [form.get_args()]

# Take the first match.
match = matches[0]

# If there are no macthes then print the help text.
if match == {}:

    print "Syntax: UEF2INF.py "+syntax
    print
    print "UEF2INF version "+version
    print
    print "This program attempts to decode UEF files and save the files contained to"
    print "the directory given by <destination path>."
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
list_files = match.has_key('l')

# Verbose output
verbose = match.has_key('v')

# Stem for unknown filenames
if match.has_key('name'):

    stem = match['stem']
else:
    stem = 'noname'


# Open the input file
try:
    in_f = open(match['UEF file'], "rb")
except IOError:
    print "The input file, "+match['UEF file']+" could not be found."
    sys.exit()

# Is it gzipped?
if in_f.read(10) != "UEF File!\000":

    in_f.close()
    in_f = gzip.open(match['UEF file'], "rb")

    try:
        if in_f.read(10) != "UEF File!\000":
            print "The input file, "+match['UEF file']+" is not a UEF file."
            sys.exit()
    except:
        print "The input file, "+match['UEF file']+" could not be read."
        sys.exit()

# Read version number of the file format
UEF_minor = str2num(1, in_f.read(1))
UEF_major = str2num(1, in_f.read(1))

if list_files == 0:

    # Get the leafname of the output path
    leafname = get_leafname(match['destination path'])

    # See if the output directory exists
    try:
        os.listdir(match['destination path'])
    except:
        try:
            os.mkdir(match['destination path'])
            print "Created directory "+match['destination path']
        except:
            print "Directory "+leafname+" already exists."
            sys.exit()

eof = 0            # End of file flag
out_file = ""        # Currently open file as specified in the block
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
                out = open(match['destination path']+sep+write_file, "wb")
            except IOError:
                # Couldn't open the file
                write_file = stem+str(n)
                n = n + 1
                try:
                    out = open(match['destination path']+sep+write_file, "wb")
                except IOError:
                    print "Couldn't open the file %s." % match['destination path']+sep+write_file
                    sys.exit()
    
            # Add file to the list of created files
            created.append(write_file)
    
            try:
                inf = open(match['destination path']+sep+write_file+suffix+"inf", "w")    # Open information file
            except IOError:
                print "Couldn't open the information file %s." % match['destination path']+sep+write_file+suffix+"inf"
                sys.exit()
    
            # Write the load and execution information to the relevant file
            inf.write("$."+write_file+"\t"+string.upper(hex(load)[2:])+"\t"+string.upper(hex(exec_addr)[2:])+"\t")
    

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
