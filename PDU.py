
class PDU():
	SMC_LEN = 0
	DATA_LEN = 0
	def strToHex(self,_val):
		val = str(_val)
		return val.encode("hex")
	
	def intToHex(self,_val):
		return "%0.2X" % _val
	
	def convNumber(self,_val):
		result=""
		if "+" in _val:
			tmp = _val.replace("+","")
			isInternational=1
		else:
			tmp = _val
			isInternational=0
		if len(tmp)%2!= 0: tmp = tmp+"F"
		while len(tmp)>2:
			result += tmp[1]+tmp[0] #flipping
			tmp = tmp[2:]
		#if tmp[1]=="0" : tmp[1]="F"
		result += tmp[1]+tmp[0] #flipping
		if isInternational == 1:
			result = "91"+result
		else:
			result = "92"+result
		return result
	
	def buildSMSInfo(self):
		return "11"
	
	def genData(self,_msg):
		#7bit encoding stuffs
		return self.strToHex(_msg)
	
	def genpdu(self,_smsc,_recipient,_msg):
		if _smsc=="":
			#use the one on the phone
			smsc_number = ""
			smsc_len="00"
			self.SMC_LEN=0
		else:
			smsc_number = self.convNumber(_smsc) #number format + number
			smsc_len=self.intToHex(len(smsc_number)/2)
			self.SMC_LEN=len(smsc_number)/2
		sms_info = self.buildSMSInfo()
		sms_id = "00" #will let phone set ref number itself
		receiver_number = self.convNumber(_recipient)
		if _recipient[:1]== "+":
			receiver_len=self.intToHex(len(_recipient)-1)
		else:
			receiver_len=self.intToHex(len(_recipient))
		proto_identifier = self.intToHex(0)
		data_encoding= self.intToHex(4) #0 for 7bit, 4 for 8 bit
		validity="AA" #optional see sms_info
		userdata_len=self.intToHex(len(_msg))
		self.DATA_LEN = len(_msg)
		userdata = self.genData(_msg)
		pdu = smsc_len +smsc_number + sms_info + sms_id+ receiver_len + receiver_number + proto_identifier
		pdu += data_encoding  + validity + userdata_len +userdata
		return pdu
	def getPDUlen(self):
		#length of receiver number + len of TB data
		return self.SMC_LEN + self.DATA_LEN
#end class

