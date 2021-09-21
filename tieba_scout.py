from data_class import *
from TiebaApi import *
from typing import List, Dict
import json
from operator import attrgetter
import time
import os
import functools

class TiebaScout(object):
    def __init__(self, BDUSS, STOKEN, tieba_name, *args, **kwargs):
        self.tapi = TiebaApi(BDUSS,STOKEN,tieba_name)
        self._load_records()
        self.illegal_words = []
        self.unsolved_digger = {}

    def _load_records(self):
        """
        加载白名单/处理记录/吧务名单/封坟关键字
        """
        self.permanent_whitelist = []
        with open("permanent_whitelist.txt","r",encoding="utf-8") as f:
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
        with open("dig_record.txt","r",encoding="utf-8") as f:
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
        self.sealing_keywords = ["坟"]

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

    def get_tomb_status(self,tid:int):
        """
        查找记录中的坟帖状态。
        如果无记录，返回False。
        """
        if self.dig_record.__contains__(tid):
            return self.dig_record[tid][0]
        else:
            return False

    def judge_tomb_digging(self,thread: Thread, post_list: List[Post], last_reply_time: int = 0):
        """
        检查一个帖子中是否有待处理的挖坟情况。
        参数: 
            thread ： 帖子信息
            post_list: 包含帖子所有回复信息的列表。
        return:
            list[Post]：挖坟的回复
        """
        if thread.tid in self.permanent_whitelist:
            self.dig_record[thread.tid][0]=False
            self.dig_record[thread.tid][1]=thread.reply_time
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
        digged = False
        dig_list = []
        for i in range(len(post_list)-1):
            if (not self._is_sealing(post_list[i])) and (not self._is_reporting(post_list[i])) and post_list[i].reply_time > self.dig_record[thread.tid][1] and int(time.time()) - post_list[i].reply_time < 86400:
                dig_list.append(post_list[i])
            if self._is_sealing(post_list[i]):
                self.dig_record[thread.tid][2] = post_list[i].reply_time
            if post_list[i].reply_time - post_list[i+1].reply_time > 2678400:
                digged = True
                break

        if digged:
            self.dig_record[thread.tid][0] = True
            self.dig_record[thread.tid][1] = thread.reply_time
            return dig_list
        else:
            self.dig_record[thread.tid][1] = thread.reply_time
            return []




    def regular_checking(self,first_check = False):
        """
        first_check: 为True时多查几页
        """
        if first_check:
            thread_list = self.tapi.get_threads()+self.tapi.get_threads(2)+self.tapi.get_threads(3)
        else:
            thread_list =  self.tapi.get_threads()

        dig_list =  []
        anti_attack_list = []
        auto_solved_dig_list = []
        at_del_list = []
        
        for thread in thread_list:
            last_round_reply_time = 0
            if self.dig_record.__contains__(thread.tid):
                # 如果并没有新回复，跳过本帖
                if thread.reply_time == self.dig_record[thread.tid][1]:
                    continue
                last_round_reply_time = self.dig_record[thread.tid][1]


            post_list = self.tapi.get_posts(thread.tid)
            post_list = sorted(post_list, key=attrgetter('reply_time'), reverse=True) # 从最晚回复到最早回复排序

            
            # 处理吧务删帖申请
            """
            at_del_list = []
            at_list = self.tapi.get_at()
            for i in at_list:
                if i[0] in self.tdm.managers and i[3].count("删除") > 0:
                    self.tapi.del_thread(int(i[2]))
                    at_del_list.append([i[0], i[2]])
            """
            for i in post_list:
                if i.reply_time <= last_round_reply_time:
                    break
                if (i.username in self.managers):
                    if i.content == ".删除":
                        self.tapi.del_thread(thread.tid)
                        at_del_list.append((i.username, thread.tid, "删除"))
                    elif i.content == ".屏蔽":
                        self.tapi.block_thread(thread.tid)
                        self.tapi.del_post(thread.tid, i.pid)
                        at_del_list.append((i.username, thread.tid, "屏蔽"))

            # 处理坟帖
            # 判断记录中的坟帖状态
            was_tomb = self.get_tomb_status(thread.tid)
            # 获取挖坟回复列表
            thread_dig_list = self.judge_tomb_digging(thread,post_list)
            if len(thread_dig_list) != 0:
                if thread_dig_list != ["疑似挖坟秒删"]:
                # 如果之前就是坟帖，自动封禁
                    if was_tomb:
                        for dig in thread_dig_list.copy():
                            if dig.username == thread.username:
                                continue
                            self.tapi.ban_id(dig.portrait,1,"挖坟（在坟帖《"+thread.title+"》下）")
                            auto_solved_dig_list.append((thread, dig))
                            thread_dig_list.remove(dig)
                # 防爆吧
                    else:
                        anti_attack_result_list = self.anti_attack(thread_dig_list, thread.username, thread.tid)
                        anti_attack_list += anti_attack_result_list
                # 报告挖坟情况
                if len(thread_dig_list) > 0:
                    dig_list.append((thread, thread_dig_list))
 

   

        return dig_list, anti_attack_list, at_del_list, auto_solved_dig_list


    def append_whitelist(self,tid):
        """
        将帖子加入坟帖白名单，以后不再视为坟帖。
        """
        if tid not in self.permanent_whitelist:
            self.permanent_whitelist.append(tid)
            return True
        else:
            return False

    def anti_attack(self, dig_list: List[Post], lz:str, tid:int):
        """
        防爆吧，自动封禁连续疑似挖坟用户。
        return:
        List[str]: 连续疑似挖坟的“昵称（用户名）”。
        """
        result_list = []
        for dig in dig_list:
            if self.unsolved_digger.__contains__(dig.username) and self.unsolved_digger[dig.username] != tid and dig.username != lz:
                self.tapi.ban_id(dig.portrait,1,"连续多次挖坟")
                self.unsolved_digger.pop(dig.portrait)
                result_list.append(dig.nickname + "（" + dig.username + "）")
            elif dig.username != lz:
                self.unsolved_digger[dig.portrait] = tid
        return result_list

    
    def _post_cmp(self, x: Post, y: Post):
        if x.reply_time < y.reply_time:
            return 1
        if x.reply_time > y.reply_time:
            return -1
        return 0

