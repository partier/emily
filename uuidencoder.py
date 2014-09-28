# coding: latin-1

import json
import uuid

class UUIDCapableEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, uuid.UUID):
			return str(obj)
		else:
			json.JSONEncoder.default(self, obj)