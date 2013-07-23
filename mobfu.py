#!/usr/bin/env python
#Requires SMSPDU https://pypi.python.org/pypi/smspdu

import serial
import time
import random
import optparse
from smspdu import SMS_SUBMIT

#global constants
PROGNAME="mobfu.py"
PROGVERSION="1.0"
COUNTRYCODE="32"

#global vars, to be set by option parser
DEVICENAME=""
PIN =""
BRUTEFILE = ""
SMSSERVER = ""
SMSCOUNT = 0
SMSID=""
DEVICE = None
LOGFILE=""

def log(msg):
	if LOGFILE !="":
		try:
			f = open(LOGFILE,"a")
			f.write(msg + "\n")
			f.close()
		except:
			print "Error writing to logfile " + LOGFILE + ", aborting."
			exit(-1)
	print msg

def cleanError(err):
	parts = err.split( )
	return parts[len(parts)-1].strip()

def getCommandResponse(_cmd, _addLineFeed=True):
	response = ''
	char =''
	if DEVICE.isOpen():
		DEVICE.write(_cmd + "\r\n")
		lc=0
		while True:
			#todo, add timeout
			char = DEVICE.read(1)
			response += char
			if char=='>':
				#"expecting morevinput, e.g.: SMS body"
				break
			elif char in '\r\n' and response.strip() != '':
				DEVICE.flushInput()#we're only interested in the first line
				break

	else:
		log("ERROR: can't write command, Serial Device state is not 'Open'.")
	#print _cmd #for debugging
	time.sleep(0.5) #you can try to move this, but had device choke when removed
	return response.strip()


def initSerial(_devname,_pin):
	global DEVICE
	DEVICE = serial.Serial(_devname,baudrate=115200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
	if not DEVICE.isOpen(): DEVICE.open()
	DEVICE.flushInput()
	DEVICE.flushOutput()
	time.sleep(1)
	isPinOk = getCommandResponse("AT+CPIN?")
	if not 'READY' in isPinOk:
		log("# Setting SIM PIN.")
		isPinOk = getCommandResponse("AT+CPIN="+_pin)
		#todo, recheck wether this actually set pin state to ok	
	if SMSSERVER != "":
		if "ERROR" in getCommandResponse('AT+CSCA="'+SMSSERVER+'"'):
			log("ERROR: Failed to set Message Service Center")
	log("# PIN STATUS	 = " + getCommandResponse("AT+CPIN?"))
	log("#SMS Service # 	 = " + getCommandResponse("AT+CSCA?"))

def delMSG():
	while not "ERROR" in getCommandResponse(DEVICE,"AT+CMGD=1"):
		print "DeletedMessage"

def sendSMS(_recipient, _msg, _autonum=True): #autonum: prepend every SMS with a tracking number
	global SMSCOUNT
	global SMSID
	#generate SMS identifier
	SMSCOUNT = SMSCOUNT + 1
	msg = _msg
	result = ''
	#check wether SMS identifier needs to be added to SMS
	if _autonum == True:
		msg =  SMSID + "-" + str(SMSCOUNT) + ":" + msg
	if len(msg)>140:
		log("# ERROR: SMS Length is too long, maximum 140 characters allowed")
		#todo, automatic switch to multiparts
	else:
		getCommandResponse("AT+CMGF=1") # short message mode
		result = getCommandResponse('AT+CMGS="'+_recipient + '"')
		if not "ERROR" in result:
			result = getCommandResponse(msg + chr(26),False) #end message with \x1a = CTRL-Z
			if not "ERROR" in result:
				log( "SEND_OK: " + _recipient + ": " + msg)
			else:
				log( "SEND_ERROR_" + cleanError(result) +":" + _recipient + ": " + msg)
		else:
			log("# ERROR: unable to set resipient "+ _recipient + ": " + result)
			exit(-1)
	#print result

def setValdNr(nr):
	tmp = nr
	if len(tmp)< 4:
		log("# ERROR: Invalid phone number:" + nr)
		exit(-1)
	else:
		if tmp[0:1] == "0":
			tmp = "+"+COUNTRYCODE+ tmp[1:]
		elif tmp[0:2]==COUNTRYCODE and len(tmp)>4:
			tmp = "+" + tmp
		elif tmp[0:1] !="+":
			log("# ERROR: Invalid phone number: " + nr + " only international (+XX) , numbers starting with 0 and 4 digit numbers are allowed.")
			exit(-1)
	return tmp

def setoptions():
	global DEVICENAME
	global PIN
	global SMSSERVER
	global TARGET
	global BRUTEFILE
	global SMSCOUNT
	global SMSID
	global LOGFILE
    	parser = optparse.OptionParser(usage=(PROGNAME + '-d SerialDevice -p PIN'+'\n       type ' + PROGNAME + ' -h for options'), version=(PROGVERSION))
	parser.add_option("-d",dest="DEVICE", default=None,help="Serial device to use. eg: /dev/ttyUSB0")
	parser.add_option("-p",dest="PIN", default=None,help="SIM PIN")
	parser.add_option("-s",dest="SMSSERVER", default="",help="Message Center, leave blank for default")
	parser.add_option("-f",dest="FILE", default=None,help="File with fuzzing values, don't specify for manual SMS, requiers -t to be set")
	parser.add_option("-t",dest="TARGET", default=None,help="Number to send SMS to.")
	parser.add_option("-l",dest="LOGFILE", default="",help="Optional, file to log output to")
		
	(opts, args) = parser.parse_args()
	LOGFILE=opts.LOGFILE
	if opts.DEVICE is None or opts.PIN is None:
		parser.print_help()
		exit(-1)
	else:
		DEVICENAME = opts.DEVICE
		PIN = opts.PIN
		if opts.SMSSERVER != "":
			SMSSERVER = setValdNr(opts.SMSSERVER)
	if opts.FILE is not None and opts.TARGET is None:
		log("# ERROR: When a file is specified, you also need to specify a target.")
		exit(-1)
	else:
		try:
			if opts.FILE is not None:
				f = open(opts.FILE)
				f.close()
				BRUTEFILE = opts.FILE #will only get hear on succesfull file access
		except IOError:
			log("# sERROR: the specified file " + opts.FILE + " does not exist.")
			exit(-1)
		if opts.TARGET is not None:
			TARGET = setValdNr(opts.TARGET)
			log("# Target		 = " + TARGET)
	if SMSCOUNT == 0 :
		SMSID = str(random.randint(100000,999999))
		log("# RUN ID 		 = " + SMSID)

if __name__ == "__main__":
	setoptions()
	initSerial(DEVICENAME,PIN)
	if DEVICE != None:
		log ("# Serial Modem initialized")
		#delMSG()
		if BRUTEFILE !="":
			for line in open(BRUTEFILE,"r"):
				data = line.strip()
				sendSMS(TARGET,data,True)
		else:
			while True:
				cmd = raw_input("SMS:")
				if cmd == "": break #end this madness
				sms = cmd.split(" ",1)
				sendSMS(sms[0],sms[1],False)
		#todo, switch to global error handler and make sure close is done nicely
		if DEVICE.isOpen():DEVICE.close()
	else:
		log("#ERROR: Error initializing serial modem, aborting.")


