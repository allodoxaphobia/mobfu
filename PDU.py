# -*- coding: utf8 -*- 
class pduSUBMIT(object): #object needed for property setters
	parts = {}
	_orignalMSG = ""
	_originalRECIP = ""
	_originalSMSC = ""
	data_encodings = {"7BIT":"00","8BIT":"04","16BIT":"08"}
	
	def __init__(self,_recipient,_msg,_smsc=""):
		#build barebone
		#note that any field with value None will be excluded during pdu generation
		self.parts= {}
		self.parts["SMSC_LEN"] 	= "00" 			# SMSC Number Length
		self.parts["SMSC_TYPE"]	=None			# SMSC Number Type 91 for International
		self.parts["SMSC"]	=None			# SMSC Number
		self.parts["PDU_TYPE"]	=self._setPDUType()		# pdu type
		self.parts["SMS_ID"]	="00"			# unique id, set to 0 to let phone decide
		self.parts["RECIP_LEN"]	=None			# Recipient number length
		self.parts["RECIP_TYPE"]=None			# Recipient number Type
		self.parts["RECIP_NR"]	=None			# Recipient number 
		self.parts["PROTO"]	="00"			# Protocol
		self.parts["DATA_ENC"]	=self.data_encodings["7BIT"]
		self.parts["VALIDITY"]	=None
		self.parts["DATA_LEN"]	="00"			# Length of data field, calculated later
		self.parts["DATA"]	= None			# teh message itself, posssibly with headers
		#calculate needed vals
		self.recipient =_recipient
		self.smsc = _smsc
		self.data = _msg
	#end init
	
	@property 
	def recipient(self): return self._originalRECIP
	@recipient.setter
	def recipient(self,value):
		#besides setting the recipient number, also calcs the length and guestimates the type
		tmp = value
		self._originalRECIP=value
		if value[:1]=="+":
			self.parts["RECIP_TYPE"]="91"	#international
			tmp = tmp[1:]			#remove +
		else:
			self.parts["RECIP_TYPE"]="92"		
		self.parts["RECIP_LEN"] = self._intToHex(len(tmp))
		self.parts["RECIP_NR"] = self._calcNumber(tmp)
	
	@property
	def smsc(self): return self._originalSMSC
	@smsc.setter
	def smsc(self,value):
		#besides setting the SMSC number, also calcs the length and guestimates the type
		#clears needed fields when none is set
		tmp = value
		if value == "":
			self.parts["SMSC_LEN"] 	= "00"
			self.parts["SMSC_TYPE"]	=None		
			self.parts["SMSC"]	=None
		else:
			if value[:1]=="+":
				self.parts["SMSC_TYPE"]	="91"
				tmp = tmp[1:]
			else:
				self.parts["SMSC_TYPE"]	="92"
			self.parts["SMSC"]=self._calcNumber(tmp)
			self.parts["SMSC_LEN"] 	= self._intToHex(len(self.parts["SMSC"])/2+1)
	
	@property
	def encoding(self):return self.parts["DATA_ENC"]
	@encoding.setter
	def encoding(self,value):
		#TODO, update data and datalength fields
		self.parts["DATA_ENC"]=value
		if value =="00":
			self.data = self._originalMMSG
			
	
	@property
	def data(self): return self._orignalMSG
	@data.setter
	def data(self,value):
		self._originalMSG = value
		if self.parts["DATA_ENC"]=="00":
			self.parts["DATA"]=self._enc7bit(self._originalMSG)
		#todo add UDHeader, and other encodings
		self.parts["DATA_LEN"] = self._intToHex(len(self.parts["DATA"]))
	
	def printpdu(self):
		result = ""
		result += self.parts["SMSC_LEN"]
		if self.parts["SMSC_LEN"] != "00":
			result += self.parts["SMSC_TYPE"]
			result += self.parts["SMSC"]
		result += self.parts["PDU_TYPE"]
		result += self.parts["SMS_ID"]
		result += self.parts["RECIP_LEN"]
		result += self.parts["RECIP_TYPE"]
		result += self.parts["RECIP_NR"]
		result += self.parts["PROTO"]
		result += self.parts["DATA_ENC"]
		if self.parts["VALIDITY"]!=None:
			result += self.parts["VALIDITY"]
		result += self.parts["DATA_LEN"]
		result += self.parts["DATA"]
		return result
	
	def pdulen(self):
		#todo add header length + smsc length
		tmp = len(self.parts["DATA"])
		return tmp
		
	def _enc7bit(self,value):
		result = ""
		tmp = []
		gsm = (u"@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>"
       			u"?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
		for char in value:
			idx = gsm.find(char)
			if idx !=-1:
				tmp.append('{0:07b}'.format(idx))#store 7bit variant
		result = self._pack7in8bits(tmp)
		return result
	
	def _pack7in8bits(self,value):
		result = ""
		length = len(value)
		i=0
		take = 1
		while i<length:
			if value[i]!="":
				if i < length-1:
					value[i] =  value[i+1][7-take:]+value[i]
					value[i+1] = value[i+1][:7-take]
				else: #last byte
					while len(value[i])<8:value[i] ="0"+value[i]
				result += self._intToHex(int(value[i],2))
			take = take+1
			if take == 9: take = 1
			i=i+1
			#add last one too
			
		return result
	def _setPDUType(self):
		return "05"
	
	def _intToHex(self,_val):
		return "%0.2X" % _val
	
	def _calcNumber(self,value):
		tmp = value
		result = ""
		if len(tmp)%2!=0: tmp = tmp+"F" #padding
		while len(tmp)>0:
			result += tmp[1] + tmp[0] 	# flip the pair
			tmp = tmp[2:]			# on with the next
		return result
			
