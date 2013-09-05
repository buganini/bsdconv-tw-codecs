import re
import sys
import bsdconv

c=bsdconv.Bsdconv("bsdconv:unicode:bsdconv")

def zpad(s):
	s=s.lstrip("0")
	if len(s) & 1:
		return '0'+s
	return s

res=re.findall(r"[A-Fa-f0-9]{4}\s+([A-Fa-f0-9]{4})[^A-Fa-f0-9]+([0-9])-([A-Fa-f0-9]{4})", open(sys.argv[1]).read(), re.S)
for rec in res:
	u=c.conv("02"+zpad(rec[1])+zpad(rec[2]))
	print "01%s\t%s" % (zpad(rec[0]), u)
