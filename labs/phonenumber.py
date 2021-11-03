from django.core.exceptions import ValidationError

__author__ = 'chandanojha'


class PhoneNumber:
	default_country_code = '91'
	_codes = [1, 7, 20, 27, 30, 31, 32, 33, 34, 36, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57,
			  58, 60, 61, 62, 63, 64, 65, 66, 81, 82, 84, 86, 90, 91, 92, 93, 94, 95, 98, 211, 212, 213, 216, 218, 220,
			  221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241,
			  242, 243, 244, 245, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 260, 261, 262, 263, 264, 265,
			  266, 267, 268, 269, 297, 298, 299, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 370, 371, 372, 373,
			  374, 375, 376, 377, 378, 380, 381, 382, 383, 385, 386, 387, 389, 420, 421, 423, 500, 501, 502, 503, 504,
			  505, 506, 507, 509, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 670, 672, 673, 674, 675, 676, 677,
			  678, 679, 680, 682, 685, 687, 689, 840, 850, 852, 853, 855, 856, 880, 886, 960, 961, 962, 963, 964, 965,
			  966, 967, 968, 970, 971, 972, 973, 974, 975, 976, 977, 992, 993, 994, 995, 996, 998]
	
	# _codes = r'^(1|7|20|27|3[0-4,6,9]|4[0-1,3-9]|5[0-8]|6[0-6]|8[1,2,4,6]|9[05,8]|21[1-3,6,8]|(22|23|24|26)[0-9]|25[0-8]|' \
	#          r'284|29[0,1,7-9]|340|345|35[0-9]|37[0-8]|38[0-2,5-9]|420|421|423|441|473|(50|59)[0-9]|649|664|(67|68)[0-9]|' \
	#          r'69[0-2]|721|758|767|784|787|808|85[2-3,5-6,8-9]|870|876|880|886|96[0-8]|97[0-7]|99[2-6,8])$'
	
	def __init__(self, number, country_code=None):
		if country_code:
			self.code = self.validate_country_code(country_code)
		else:
			# no country code provided, try to auto-detect it
			self.code, number = self.detect_country(number)
		
		self.number = self.validate_number_part(number)
	
	@property
	def is_local(self):
		return self.code == self.default_country_code
	
	@property
	def as_international(self):
		return self.code + self.number
	
	@property
	def e164(self):
		return '+{0}{1}'.format(self.code, self.number)
	
	def __str__(self):
		return '{0}-{1}'.format(self.code, self.number)
	
	def __len__(self):
		return len(self.__str__())
	
	def __eq__(self, other):
		try:
			other = PhoneNumber.parse(other)  # see if 'other' is some form of PhoneNumber?
		except ValidationError:
			return NotImplemented
		return self.__str__() == other.__str__()
	
	def __hash__(self):
		return hash(self.__str__())
	
	@classmethod
	def validate_country_code(cls, code):
		""" Validates county code using the lookup """
		try:
			code = int(code)
			if not (1 <= code <= 999):
				raise ValueError()
		except ValueError:
			raise ValidationError("County code '{0}' should be a 1-3 digit positive number"
								  " after stripping leading '+' or zeros".format(code))
		
		if code not in cls._codes:
			raise ValidationError("Invalid or unsupported country code: '{0}'".format(code))
		
		return str(code)
	
	@classmethod
	def validate_number_part(cls, number):
		""" Validates just the number part """
		number = number.strip().replace(' ', '')
		if not number.isdigit():
			raise ValidationError("Phone number '{0}' should only contains digits".format(number))
		if len(number) < 8:
			raise ValidationError("Phone number '{0}' should be minimum of 8 chars".format(number))
		return number
	
	@classmethod
	def detect_country(cls, number):
		"""
		:param number: - phone number string of one the following format

			1. 91-9876543210, +91-9876543210, 0091-9876543210, 91-9876 543 210, 91-9876-543210
			2. +91 9876543210, +919876543210, 0091 9876543210, 00919876543210
			3. 919876543210, 9876543210

		:return: - All of the above will return (91, 9876543210)
		"""
		number = number.strip()
		
		# 1. '-' separated
		if '-' in number:
			country_code, number = number.split('-', maxsplit=1)
			country_code = cls.validate_country_code(country_code)
		
		# 2. starts with '+' or '00'
		elif number.startswith('+') or number.startswith('00'):
			number = number.lstrip('+0')
			country_code = next(str(c) for c in cls._codes if number.startswith(str(c)))
			if country_code:
				number = number[len(country_code):]
		
		# 3. Default to India number
		else:
			country_code = cls.default_country_code  # default to india
			if len(number) >= 12 and number.startswith(country_code):
				number = number[2:]
		
		return country_code, number.strip().replace(' ', '')
	
	@classmethod
	def parse(cls, value):
		return value if isinstance(value, cls) else (value and cls(value))
	
	@classmethod
	def validator(cls):
		def validate(phone_number):
			if not isinstance(phone_number, cls):
				code, number = cls.detect_country(phone_number)
				cls.validate_number_part(number)
		
		return validate
