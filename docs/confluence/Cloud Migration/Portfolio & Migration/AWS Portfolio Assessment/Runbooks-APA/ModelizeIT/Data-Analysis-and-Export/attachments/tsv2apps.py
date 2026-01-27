#!/usr/bin/python
#
# Copyright (C) 2021 modelizeIT Inc
#

import string
import sys
import re

APPS = {}
ENVS = {}

for line in sys.stdin:
	line = line[:-1]
	# TAB-delimited
	w = re.match("^([^\t]*)\t([^\t]*)\t([^\t]*)$", line)
	if not w:
		print >> sys.stderr, "error: line: "+line
		#sys.exit(-1)
	#
	srv_name = w.group(1).lower()
	srv_name = re.sub("_", "-", srv_name)
	if srv_name == "":
		print >> sys.stderr, "warning: missing server name: " + line
		#sys.exit(-1)
	app_names = w.group(2)
	if app_names == "":
		print >> sys.stderr, "error: missing app name: " + line
		continue
	app_names = re.sub("&", "and", app_names)
	app_names = re.sub("/", "", app_names)
	app_names = re.sub(" \s*", " ", app_names)
	#
	try:
		app_prodtd = w.group(3) + ""
		app_prodtd = re.sub("[/\r]", "", app_prodtd)
	except:
		app_prodtd = ""
	#
	app_names = re.sub("\"", "", app_names)
	app_namesS = app_names.split(',')
	for app_name in app_namesS:
		if app_prodtd != "":
			app_name = app_name + " [" + app_prodtd[:1] + "]"
		ENVS[app_name] = app_prodtd
		app_name = re.sub("^\s*", "", app_name)
		app_name = re.sub("\s*$", "", app_name)
		if app_name in APPS.keys():
			APPS[app_name][srv_name] = 1
		else:
			APPS[app_name] = {srv_name:1}

app_id = 0
print '"META","NODE_ID","DISCOVERY_ID","HOSTNAME","DETAILS","SCRIPT_TYPE","SCRIPT_VER","PARSER_VER","USER","RUN_TIMESTAMP","DURATION","SAMPLES","LSOF"'
print '"META","0","0","DS/CSV","yes","DS/CSV","1.0","1.0","root","191119093554","","",""'
print '"APPLICATION","NODE_ID","DISCOVERY_ID","HOSTNAME","DETAILS","OID","Parent_Ref","RH","DisplayName:31 characters max","Name","Environment","Description","Contains: A comma-delimited list"'
for app_name in APPS:
	app_env = ENVS[app_name]
	line = '"APPLICATION","0","0","","yes","'+str(app_id)+'","","","'+app_name[:31]+'","'+app_name+'","'+app_env+'","","'
	comma = ""
	for srv_name in APPS[app_name]:
		line = line + comma + srv_name
		comma = ","
	line  = line + "\""
	print line
	app_id = app_id + 1

