#! /usr/bin/python
"""
	Name		: File2UEF.py
	Author		: David Boddie
	Created		: Fri 27th October 2000
	Last updated	: Mon 23rd July 2001
	Purpose		: Convert ADFS files to UEF format using an index.
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


def rol(n, c):

	n = n << 1

	if (n & 256) != 0:
		carry = 1
		n = n & 255
	else:
		carry = 0

	n = n | c

	return n, carry


def crc(s):

	high = 0
	low = 0

	for i in s:

		high = high ^ ord(i)

		for j in range(0,8):

			a, carry = rol(high, 0)

			if carry == 1:
				high = high ^ 8
				low = low ^ 16

			low, carry = rol(low, carry)
			high, carry = rol(high, carry)

	return high | (low << 8)


def read_block(f, name, load, exe, length, n):

	block = f.read(256)

	# Write the alignment character
	out = "*"+name[:10]+"\000"

	# Load address
	out = out + number(4, load)

	# Execution address
	out = out + number(4, exe)

	# Block number
	out = out + number(2, n)

	# Block length
	out = out + number(2, len(block))

	# Block flag (last block)
	if f.tell() == length:
		out = out + number(1, 128)
		last = 1
	else:
		if len(block) == 256:
			out = out + number(1, 0)
			last = 0
		else:
			out = out + number(1, 128) # shouldn't be needed
			last = 1 

	# Next address
	out = out + number(2, 0)

	# Unknown
	out = out + number(2, 0)

	# Header CRC
	out = out + number(2, crc(out[1:]))

	out = out + block

	# Block CRC
	out = out + number(2, crc(block))

	return out, last


import gzip, os, string, sys, swi

syntax = "Syntax: File2UEF.py [-c] <Directory> <UEF file>"
version = "0.12 (Mon 23rd July 2001)"

if len(sys.argv) < 3:

	print syntax
	print
	print "File2UEF version "+version
	print
	print "Take the files indexed in the directory given using the index.txt file and store"
	print "them in the UEF file specified as tape files."
	print
	print "If the -c flag is specified then the UEF file will be compressed in the form"
	print "understood by gzip."
	print
	sys.exit()

if sys.platform == "RISCOS":
	suffix = "/"
elif sys.platform == "DOS":
	suffix = "."
else:
	suffix = "."

# Determine whether the file needs to be compressed

if sys.argv[1] == "-c":
	if len(sys.argv) < 4:
		print syntax
		print
		sys.exit()
	else:
		compress = 1
		in_dir = sys.argv[2]
		uef_file = sys.argv[3]
else:
	compress = 0
	in_dir = sys.argv[1]
	uef_file = sys.argv[2]

index_file = in_dir + os.sep + "index" + suffix + "txt"

try:
	index = open(index_file)
except:
	print "Couldn't open the Index file, %s" % index_file
	print
	sys.exit()

# Create the UEF file

try:
	if compress == 1:
		uef = gzip.open(uef_file, "w")
	else:
		uef = open(uef_file, "w")
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

we_are = "File2UEF "+version+"\000"
if (len(we_are) % 4) != 0:
	we_are = we_are + ("\000"*(4-(len(we_are) % 4)))

# Write this program's details
chunk(uef, 0, we_are)


# Platform chunk

chunk(uef, 5, number(1, 1))	# Electron with any keyboard layout


# Specify tape chunks

chunk(uef, 0x110, number(2,0x05dc))
chunk(uef, 0x100, number(1,0xdc))


# Decode the Index file

while 1:

	try:
		file_name = string.strip(index.readline())
	except IOError:
		break

	if not file_name:
		break

	try:
		in_file = open(in_dir + os.sep + file_name, "r")

		load, exe, length = swi.swi("OS_File", "is;..iii", 17, in_dir + os.sep + file_name)

		# Reset the block number to zero
		n = 0

		# Long gap
		gap = 1
	
		# Write block details
		while 1:
			block, last = read_block(in_file, file_name, load, exe, length, n)
	
			if gap == 1:
				chunk(uef, 0x110, number(2,0x05dc))
				gap = 0
			else:
				chunk(uef, 0x110, number(2,0x0258))

			# Write the block to the UEF file
			chunk(uef, 0x100, block)

			if last == 1:
				break

			# Increment the block number
			n = n + 1

		# Close the file
		in_file.close()

	except IOError:
		print "Couldn't find file,", file_name



# Write some finishing bytes to the file
chunk(uef, 0x110, number(2,0x0258))
chunk(uef, 0x112, number(2,0x0258))


# Close the Index and UEF files
index.close()
uef.close()

# Exit
sys.exit()
