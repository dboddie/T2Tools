#! /usr/bin/python

"""
	Name		: INF2File.py
	Author		: David Boddie <davidb@mcs.st-and.ac.uk>
	Created		: Sat 21st October 2000
	Purpose		: Convert INF format files to files with ADFS attributes.
	WWW		: http://www.david.boddie.net/Software/Tape2Disc/

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

import sys, string, os, swi

def get_leafname(path):

	pos = string.rfind(path, os.sep)
	if pos != -1:
		return path[pos+1:]
	else:
		return path


def hex2num(s):

	n = 0

	for i in range(0,len(s)):

		a = ord(s[len(s)-i-1])
		if (a >= 48) & (a <= 57):
			n = n | ((a-48) << (i*4))
		elif (a >= 65) & (a <= 70):
			n = n | ((a-65+10) << (i*4))
		elif (a >= 97) & (a <= 102):
			n = n | ((a-97+10) << (i*4))
		else:
			print "Bad hex", s
			print
			sys.exit()

	return n


syntax = "Syntax: INF2File.py <source path> <destination path>"
version = "0.10 (Sat 21st October 2000)"

if len(sys.argv) < 3:

	print syntax
	print
	print "INF2File version "+version
	print
	print "Take the files stored in the directory given and store them as files with"
	print "ADFS attributes."
	print
	sys.exit()

in_path = sys.argv[1]
out_path = sys.argv[2]

# See if the output directory exists
try:
	os.listdir(out_path)
except:
	try:
		os.mkdir(out_path)
		print "Created directory "+out_path
	except:
		print "Directory "+get_leafname(out_path)+" already exists."
		sys.exit()

files = os.listdir(in_path)

for j in files:

        if string.lower(j[-4:]) == "/inf":

		i = j[:-4]

		# Copy file
		open(out_path + os.sep + i, "w").write(open(in_path + os.sep + i, "r").read())

		# Read the .inf file
		try:
			details = string.split(open(in_path + os.sep + i + "/inf", "r").read())
		except IOError:
			try:
				details = string.split(open(in_path + os.sep + i + "/INF", "r").read())
			except IOError:
				print "Couldn't open "+in_path + os.sep + i + "/inf"
				print
				sys.exit()

		if string.find(details[0], ".") != -1:
			load = hex2num(details[1])
			exe = hex2num(details[2])
		else:
			load = hex2num(details[0])
			exe = hex2num(details[1])

#		if (details[0] == i) | (details[0] == "$."+i):
#			load = hex2num(details[1])
#			exe = hex2num(details[2])
#		else:
#			load = hex2num(details[0])
#			exe = hex2num(details[1])

		# Provide attributes
		swi.swi("OS_File", "isi", 2, out_path + os.sep + i, load)
		swi.swi("OS_File", "is.i", 3, out_path + os.sep + i, exe)

		if details[0][:2] == "$.":
			# Rename file
			os.rename(out_path + os.sep + i, out_path + os.sep + details[0][2:])


sys.exit()
