#! /usr/bin/python
"""
	Name		: T2UEF.py
	Author		: David Boddie
	Created		: Wed 04th October 2000
	Last updated	: Mon 23rd July 2001
	Purpose		: Convert Slogger T2 files to UEF format archives.
	WWW		: http://www.david.boddie.net/Software/Tape2Disc/
"""

def number(size, n):

	# Little endian writing

	s = ""

	while size > 0:
		i = n % 256
		s = s + chr(i)
#		n = n / 256
		n = n >> 8
		size = size - 1

	return s


def chunk(f, n, data):

	# Chunk ID
	f.write(number(2, n))
	# Chunk length
	f.write(number(4, len(data)))
	# Data
	f.write(data)


def decode(s):

	new = ""

	for i in s:
		new = new + chr(ord(i)^90)

	return new


def read_block(in_f):

	block = ""
	gap = 0

	# Read the alignment character
	align = in_f.read(1)

	if not align:
		return "", 0

	block = block + chr(ord(align)^90)

	# Read the name

	while 1:
		c = in_f.read(1)
		if not c:
			return block, 0

		c = chr(ord(c)^90)

		block = block + c

		if ord(c) == 0:
			break


	# Load address
	block = block + decode(in_f.read(4))

	# Execution address
	block = block + decode(in_f.read(4))

	# Block number
	block = block + decode(in_f.read(2))

	block_number = ord(block[-2])+(ord(block[-1]) << 8)
	if block_number == 0:
		gap = 1

	# Block length
	block = block + decode(in_f.read(2))

	block_length = ord(block[-2])+(ord(block[-1]) << 8)

	# Block flag
	block = block + decode(in_f.read(1))

	# Next address
	block = block + decode(in_f.read(2))

	block = block + decode(in_f.read(2))

	# Header CRC
	block = block + decode(in_f.read(2))

	if block_length==0:
		return block, 0
	
	block = block + decode(in_f.read(block_length))

	# Block CRC
	block = block + decode(in_f.read(2))

	return block, gap


import gzip, os, string, sys

syntax = "Syntax: T2UEF.py [-c] <T2* file> <UEF file>"
version = "0.14 (Mon 23rd July 2001)"

if len(sys.argv) < 3:

	print syntax
	print
	print "T2UEF version "+version
	print
	print "Take the files stored in the T2* file given and store them in the UEF file"
	print "specified as tape files."
	print
	print "If the -c flag is specified then the UEF file will be compressed in the form"
	print "understood by gzip."
	print
	sys.exit()

# Determine whether the file needs to be compressed

if sys.argv[1] == "-c":
	if len(sys.argv) < 4:
		print syntax
		print
		sys.exit()
	else:
		compress = 1
		t2_file = sys.argv[2]
		uef_file = sys.argv[3]
else:
	compress = 0
	t2_file = sys.argv[1]
	uef_file = sys.argv[2]

try:
	t2 = open(t2_file, "rb")
except:
	print "Couldn't open the T2* file, %s" % t2_file
	print
	sys.exit()

# Create the UEF file

try:
	if compress == 1:
		uef = gzip.open(uef_file, "wb")
	else:
		uef = open(uef_file, "wb")
except:
	print "Couldn't open the UEF file, %s" % uef_file
	print
	sys.exit()

# Write the UEF file header

uef.write("UEF File!\000")

# Minor and major version numbers

uef.write(number(1, 6) + number(1, 0))

# Begin writing chunks

# Creator chunk

we_are = "T2UEF "+version+"\000"
if (len(we_are) % 4) != 0:
	we_are = we_are + ("\000"*(4-(len(we_are) % 4)))

# Write this program's details
chunk(uef, 0, we_are)


# Platform chunk

chunk(uef, 5, number(1, 1))	# Electron with any keyboard layout


# Specify tape chunks

chunk(uef, 0x110, number(2,0x05dc))
chunk(uef, 0x100, number(1,0xdc))


# Decode the T2* file
t2.seek(5, 1)		# Move to byte 5 in the file

# chunk(uef, 0x110, number(2,0x05dc))

while 1:
	# Read block details
	block, gap = read_block(t2)

	if block == "":
		break

	# If this is the first block in a file then put in a long gap before it
	# - the preceding program may need time to complete running before it
	# attempts to load the next one

	if gap == 1:
		chunk(uef, 0x110, number(2,0x05dc))
	else:
		chunk(uef, 0x110, number(2,0x0258))

	# Write the block to the UEF file
	chunk(uef, 0x100, block)


# Write some finishing bytes to the file
chunk(uef, 0x110, number(2,0x0258))
chunk(uef, 0x112, number(2,0x0258))


# Close the T2* and UEF files
t2.close()
uef.close()

# Exit
sys.exit()
