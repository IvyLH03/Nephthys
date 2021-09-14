import datetime
from typing import List

class Post(object):
	def __init__(self, pid, reply_time, content, nickname, username, floor_no, is_lzl):
		self.pid = int(pid)
		self.reply_time = int(reply_time)
		# self.content = content
		self.nickname = nickname
		self.username = username
		self.floor_no = int(floor_no)
		self.is_lzl = bool(is_lzl)

		if username == "":
			self.username = nickname


		s = ""
		for i in content:
			if i['type'] == '2':
				s += "#(" + i['c'] + ")"
			elif i['type'] == '3':
				s += "[图片]"
			else:
				s += i['text']
		self.content = s

	def __str__(self):
		return "pid:"+str(self.pid)+"\nreply_time:"+str(self.reply_time)+"\ncontent:"+str(self.content)+"\nnickname:"+str(self.nickname)+"\nusername:"+str(self.username)+"\nfloor_no:"+str(self.floor_no)+"\nis_lzl:"+str(self.is_lzl)

class Thread(object):
	def __init__(self, tid, title, post_time, reply_time, reply_num, username, nickname):
		self.tid = int(tid)
		self.title = title
		self.post_time = int(post_time)
		self.reply_time = int(reply_time)
		self.reply_num = int(reply_num)
		self.username = username
		self.nickname = nickname

		if username == "":
			self.username = nickname
		if title == "":
			self.title = "无标题"

	def __str__(self):
		return "tid:"+str(self.tid)+"\ntitle:"+str(self.title)+"\npost_time"+str(self.post_time)+"\nreply_time"+str(self.reply_time)+"\nreply_num"+str(self.reply_num)+"\nusername"+str(self.username)+"\nnickname:"+str(self.nickname)

class DiggedThread(Thread):
	def __init__(self, last_dig_time, diggings: List[Post] , *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.last_dig_time = last_dig_time
		self.diggings = diggings
		self.tapi = tapi

class User(object):
	def __init__(self, username, nickname, user_id, portrait, *args, **kwargs):
		self.username = username
		self.nickname = nickname
		self.user_id = user_id
		self.portrait = portrait

