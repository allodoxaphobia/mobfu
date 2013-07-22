#!/usr/bin/env python

import serial
import time
import random
import optparse

#global constants
PROGNAME="mobfu.py"
PROGVERSION="1.0"
COUNTRYCODE="32"

#global vars, to be set by option parser
DEVICE=""
PIN =""
BRUTEFILE = ""
SMSSERVER = ""
SMSCOUNT = 0
SMSID=""

def getCommandResponse(_dev,_cmd, _addLineFeed=True):
	response = ''
	char =''
	_dev.open()
	if _dev.isOpen():
		_dev.flushInput()
		_dev.flushOutput()
		_dev.write(_cmd + "\r\n")
		while True:
			#todo, add timeout
			char = _dev.read(1)
			response += char
			if char=='>':
				#"expecting morevinput, e.g.: SMS body"
				break
			elif char in '\r\n' and response.strip() != '':
				break
		_dev.close()
	#print _cmd #for debugging
	return response.strip()


def initSerial(_dev,_pin):
	serialDev = serial.Serial(_dev,baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
	isPinOk = getCommandResponse(serialDev,"AT+CPIN?")
	if not 'READY' in isPinOk:
		print "Setting SIM PIN."
		isPinOk = getCommandResponse(serialDev,"AT+CPIN="+_pin)
		#todo, recheck wether this actually set pin state to ok	
	if SMSSERVER != "":
		if "ERROR" in getCommandResponse(serialDev,'AT+CSCA="'+SMSSERVER+'"'):
			print "Failed to set Message Service Center"
	print "MSISDN		 = " + getCommandResponse(serialDev,"AT+CNUM?")
	print "IMSI 		 = " + getCommandResponse(serialDev,"AT+CIMI?")
	print "SMS Service # 	 = " + getCommandResponse(serialDev,"AT+CSCA?")
	return serialDev

def delMSG(_dev):
	while not "ERROR" in getCommandResponse(_dev,"AT+CMGD=1"):
		print "DeletedMessage"

def sendSMS(_dev, _recipient, _msg, _autonum=True): #autonum: prepend every SMS with a tracking number
	global SMSCOUNT
	global SMSID
	#generate SMS identifier
	SMSCOUNT = SMSCOUNT + 1
	msg = _msg
	result = ''
	#check wether SMS identifier needs to be added to SMS
	if _autonum == True:
		msg =  SMSID + "-" + str(SMSCOUNT) + ":" + msg
		#todo: random doesn't guarantee uniqueness, after initial seed, use increment)
	if len(msg)>140:
		print "SMS Length is too long, maximum 140 characters allowed"
		#todo, automatic switch to multiparts
	else:
		getCommandResponse(_dev,"AT+CMGF=1") # short message mode
		result = getCommandResponse(_dev,'AT+CMGS="'+_recipient + '"')
		if not "ERROR" in result:
			result = getCommandResponse(_dev, msg + chr(26),False) #end message with \x1a = CTRL-Z
			if not "ERROR" in result:
				print _recipient + ": " + msg
			else:
				print "Error sending SMS to "+ _recipient  + ": " + result
		else:
			print "ERROR: unable to set resipient "+ _recipient + ": " + result
			exit(-1)
	#print result

def setValdNr(nr):
	tmp = nr
	if len(tmp)< 4:
		print "ERROR: Invalid phone number:" + nr
		exit(-1)
	else:
		if tmp[0:1] == "0":
			tmp = "+"+COUNTRYCODE+ tmp[1:]
		elif tmp[0:2]==COUNTRYCODE and len(tmp)>4:
			tmp = "+" + tmp
		elif tmp[0:1] !="+":
			print "ERROR: Invalid phone number: " + nr + " only international (+XX) , numbers starting with 0 and 4 digit numbers are allowed."
			exit(-1)
	return tmp

def setoptions():
	global DEVICE
	global PIN
	global SMSSERVER
	global TARGET
	global BRUTEFILE
	global SMSCOUNT
	global SMSID
    	parser = optparse.OptionParser(usage=(PROGNAME + '-d SerialDevice -p PIN'+'\n       type ' + PROGNAME + ' -h for options'), version=(PROGVERSION))
	parser.add_option("-d",dest="DEVICE", default=None,help="Serial device to use. eg: /dev/ttyUSB0")
	parser.add_option("-p",dest="PIN", default=None,help="SIM PIN")
	parser.add_option("-s",dest="SMSSERVER", default="",help="Message Center, leave blank for default")
	parser.add_option("-f",dest="FILE", default=None,help="File with fuzzing values, don't specify for manual SMS, requiers -t to be set")
	parser.add_option("-t",dest="TARGET", default=None,help="Number to send SMS to.")
		
	(opts, args) = parser.parse_args()
	if opts.DEVICE is None or opts.PIN is None:
		parser.print_help()
		exit(-1)
	else:
		DEVICE = opts.DEVICE
		PIN = opts.PIN
		if opts.SMSSERVER != "":
			SMSSERVER = setValdNr(opts.SMSSERVER)
	if opts.FILE is not None and opts.TARGET is None:
		print "ERROR: When a file is specified, you also need to specify a target."
		exit(-1)
	else:
		try:
			f = open(opts.FILE)
			f.close()
			BRUTEFILE = opts.FILE #will only get hear on succesfull file access
		except IOError:
			print "ERROR: the specified file " + opts.FILE + " does not exist."
			exit(-1)
		if opts.TARGET is not None:
			TARGET = setValdNr(opts.TARGET)
			print "Target		 = " + TARGET
	if SMSCOUNT == 0 :
		SMSID = str(random.randint(100000,999999))
		print "RUN ID 		 = " + SMSID
if __name__ == "__main__":
	setoptions()
	dev = initSerial(DEVICE,PIN)
	if dev != None:
		print "Serial Modem initialized"
		#delMSG(dev)
		if BRUTEFILE !="":
			for line in open(BRUTEFILE,"r"):
				data = line.strip()
				sendSMS(dev,TARGET,data,True)
		else:
			cmd ="x"
			while True:
				cmd = raw_input("SMS:")
				if cmd == "": break
				sms = cmd.split(" ",1)
				sendSMS(dev,sms[0],sms[1],False)
	else:
		print "ERROR: Error initializing serial modem, aborting."

