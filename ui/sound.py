import ctypes
import os
import math
import sound_lib
from sound_lib import output, stream


class Sound:
	def __init__(self):
		self.handle = None
		self.freq = 44100

	def load(self, filename=""):
		if self.is_active:
			self.close()
		try:
			if isinstance(filename, str): # Asume path on disk.
				self.handle = stream.FileStream(file=filename)
			else: # binary data.
				self.handle = stream.FileStream(mem=True, file=filename, length=len(filename))
		except sound_lib.main.BassError:
			return False
		self.freq = self.handle.get_frequency()
		return self.is_active

	def stream(self, data):
		if self.is_active:
			self.close()
		if not data:
			return False
		data = ctypes.create_string_buffer(data)
		self.handle = stream.FileStream(mem=True, file=ctypes.addressof(data), length=len(data))
		return self.is_active

	def url_stream(self, address):
		if self.is_active:
			self.close()
		if not address or not "://" in address:
			return False
		self.handle = stream.URLStream(url=address)
		return self.is_active

	def play(self):
		if not self.is_active:
			return False
		self.handle.looping = False
		return bool(self.handle.play())

	def play_wait(self, callback=None):
		if not self.is_active:
			return False
		self.handle.looping = False
		# We can't block the UI
		result = bool(self.handle.play())
		while self.handle.is_playing:
			if callable(callback):
				callback()
		return result

	def play_looped(self):
		if not self.is_active:
			return False
		self.handle.looping = True
		self.looping = True
		return bool(self.handle.play())

	def stop(self):
		if self.is_active and self.handle.is_playing:
			self.handle.stop()
			self.handle.set_position(0)
			return True

	def get_source_object(self):
		return self.handle

	def pause(self):
		if not self.is_active:
			return
		return bool(self.handle.pause())

	def resume(self):
		if not self.is_active:
			return False
		return bool(self.handle.resume())

	@property
	def volume(self):
		if not self.handle:
			return False
		return round(math.log10(self.handle.volume) * 20)

	@volume.setter
	def volume(self, value):
		"""Volume between 0 (full volume) to -100 silence"""
		if not self.is_active:
			return False
		vol = 10 ** (float(value) / 20)
		if vol > 1.0:
			vol = 1.0
		return bool(self.handle.set_volume(vol))

	@property
	def pitch(self):
		if not self.handle:
			return False
		return (self.handle.get_frequency() / self.freq) * 100

	@pitch.setter
	def pitch(self, value):
		if not self.is_active:
			return False
		return bool(self.handle.set_frequency((float(value) / 100) * self.freq))

	@property
	def pan(self):
		if not self.handle:
			return False
		return self.handle.get_pan() * 100

	@pan.setter
	def pan(self, value):
		if not self.handle:
			return False
		return bool(self.handle.set_pan(float(value) / 100))

	def close(self):
		if self.handle:
			self.handle.free()
			self.__init__()
			return True

	@property
	def is_active(self):
		return bool(self.handle)


o = output.Output()
