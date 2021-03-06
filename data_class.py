import datetime
from typing import List

class Post(object):
	def __init__(self, pid, reply_time, content, nickname, username, floor_no, is_lzl, portrait, level):
		self.pid = int(pid)
		self.reply_time = int(reply_time)
		# self.content = content
		self.nickname = nickname
		self.username = username
		self.portrait = portrait
		self.floor_no = int(floor_no)
		self.is_lzl = bool(is_lzl)
		self.text_content = ""
		self.level = level

		if username == "":
			self.username = nickname


		s = ""
		for i in content:
			if i.__contains__('type'):
				if i['type'] == '2':
					s += "#(" + i['c'] + ")"
				elif i['type'] == '3':
					s += "[图片]"
				elif i.__contains__('text'):
					s += i['text']
				if i['type'] == '0':
					self.text_content += i['text']
		self.content = s

	def __str__(self):
		return "pid:"+str(self.pid)+"\nreply_time:"+str(self.reply_time)+"\ncontent:"+str(self.content)+"\nnickname:"+str(self.nickname)+"\nusername:"+str(self.username)+"\nfloor_no:"+str(self.floor_no)+"\nis_lzl:"+str(self.is_lzl)

class Thread(object):
	def __init__(self, tid, title, content, post_time, reply_time, reply_num, username, nickname, portrait):
		self.tid = int(tid)
		self.title = title
		self.post_time = int(post_time)
		self.reply_time = int(reply_time)
		self.reply_num = int(reply_num)
		self.username = username
		self.nickname = nickname
		self.portrait = portrait

		s = ""
		for i in content:
			if i.__contains__('type'):
				if i['type'] == '2':
					s += "#(" + i['c'] + ")"
				elif i['type'] == '3':
					s += "[图片]"
				else:
					s += i['text']
		self.content = s

		if username == "":
			self.username = nickname
		if title == "":
			self.title = self.content

	def __str__(self):
		return "tid:"+str(self.tid)+"\ntitle:"+str(self.title)+"\npost_time:"+str(self.post_time)+"\nreply_time:"+str(self.reply_time)+"\nreply_num:"+str(self.reply_num)+"\nusername:"+str(self.username)+"\nnickname:"+str(self.nickname)+"\ncontent:"+str(self.content)


