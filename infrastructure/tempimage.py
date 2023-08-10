# import the necessary packages
import uuid
import os
import datetime

class TempImage:
	def __init__(self, basePath="./", ext=".jpg"):
		self.path = f"{str(datetime.datetime.now())} {str(uuid.uuid4())}{ext}"

	def cleanup(self):
		os.remove(self.path)