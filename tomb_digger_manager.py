from data_class import *
from typing import List, Dict
import os
import functools
import time
from operator import attrgetter
import json
class TombDiggerManager(object):
    def __init__(self):
        self._load_records()
        self.sealing_keywords = ["坟"]
    def _load_records(self):
        """
        加载白名单/处理记录/吧务名单
        """
        self.permanent_whitelist = []
        with open("permanent_whitelist.txt","+a",encoding="utf-8") as f:
            while True:
                line = f.readline()
                if line:
                    if int(line[line.find(" ")+1:]) in self.permanent_whitelist:
                        continue
                    else:
                        self.permanent_whitelist.append(int(line))
                else:
                    break
        # 12345(1)12312312312:123123123123
        self.dig_record = {}
        with open("dig_record.txt","+a",encoding="utf-8") as f:
            while True:
                line = f.readline()
                if line:
                    tid = int(line[:line.find("(")])
                    is_tomb = bool(int(line[line.find("(")+1:line.find(")")]))
                    last_reply_time = int(line[line.find(")")+1:line.find(":")])
                    last_solve_time = int(line[line.find(":")+1:])
                    self.dig_record[tid] = [is_tomb, last_reply_time, last_solve_time]
                else:
                    break

        with open("config.json","r",encoding="utf-8") as f:
            config = json.load(f)
        self.managers = config["Managers"]

    def save_records(self):
        """
        保存处理记录。
        """
        with open("permanent_whitelist.txt","w",encoding="utf-8") as f:
            for line in self.permanent_whitelist:
                f.write(str(line)+"\n")
        with open("dig_record.txt","w",encoding="utf-8") as f:
            for i in self.dig_record:
                s = str(i) + "("
                if self.dig_record[i][0] == False:
                    s += "0)"
                else:
                    s += "1)"
                s += str(self.dig_record[i][1])+":"+str(self.dig_record[i][2])+"\n"
                f.write(s)

    def _is_sealing(self, post: Post):
        """
        检查某回复是否为封坟线。
        """
        if post.username in self.managers:
            for keyword in self.sealing_keywords:
                if str(post.content).count(keyword) != 0:
                    return True
        return False

    def _is_reporting(self, post:Post):
        """
        检查某回复是否为举报挖坟。
        """
        return False

    def judge_tomb_digging(self,thread: Thread, post_list: List[Post]):
        """
        检查一个帖子中是否有待处理的挖坟情况。
        参数: 
            thread ： 帖子信息
            post_list: 包含帖子所有回复信息的列表。
        return:
            list[Post]：挖坟的回复
        """
        if thread.tid in self.permanent_whitelist:
            return []

        if self.dig_record.__contains__(thread.tid):
            if int(time.time()) - thread.reply_time > 2670400:
                self.dig_record[thread.tid][0] = True
                self.dig_record[thread.tid][1] = thread.reply_time
                return ["疑似挖坟秒删"]
            if self.dig_record[thread.tid][0] == True:
                if thread.reply_time < self.dig_record[thread.tid][1]:
                    self.dig_record[thread.tid][1] = thread.reply_time
                    return ["疑似挖坟秒删"]
                if thread.reply_time == self.dig_record[thread.tid][2]:
                    return []
            else:
                if thread.reply_time - self.dig_record[thread.tid][1] < 2678400:
                    self.dig_record[thread.tid][1] = thread.reply_time
                    return []
        else:
            self.dig_record[thread.tid] = [False, 0, 0]
        post_list = sorted(post_list, key=attrgetter('reply_time'), reverse=True) # 从最晚回复到最早回复排序
        digged = False
        dig_list = []
        for i in range(len(post_list)-1):
            if (not self._is_sealing(post_list[i])) and (not self._is_reporting(post_list[i])) and post_list[i].reply_time > self.dig_record[thread.tid][2]:
                dig_list.append(post_list[i])
            if self._is_sealing(post_list[i]):
                self.dig_record[thread.tid][2] = post_list[i].reply_time
            if post_list[i].reply_time - post_list[i+1].reply_time > 2678400:
                print("查找到挖坟")
                digged = True
                break

        if digged:
            self.dig_record[thread.tid][0] = True
            self.dig_record[thread.tid][1] = thread.reply_time
            return dig_list
        else:
            self.dig_record[thread.tid][1] = thread.reply_time
            return []


    def _post_cmp(self, x: Post, y: Post):
        if x.reply_time < y.reply_time:
            return 1
        if x.reply_time > y.reply_time:
            return -1
        return 0


