from data_class import *
from TiebaApi import *
from typing import List, Dict
import json
from operator import attrgetter
import time
import os
import functools
import re

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
            self.config = json.load(f)
        self.managers = self.config["Managers"]
        self.answerers = self.config["Answerers"]
        self.sealing_keywords = ["坟"]
        self.adPostKeyword = self.config["AdPostKeyword"]
        self.adThreadKeyword = self.config["AdThreadKeyword"]

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
        self.config["AdPostKeyword"] = self.adPostKeyword
        self.config["AdThreadKeyword"] = self.adThreadKeyword
        with open("config.json","w",encoding="utf-8") as f:
            json.dump(self.config,f)




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

        dig_list =  []
        anti_attack_list = []
        auto_solved_dig_list = []
        at_del_list = []
        auto_del_list = []

        # 处理吧务删帖申请
        at_list = self.tapi.get_at()
        for i in at_list:
            if i[0] in self.managers and i[3].count("删除") > 0:
                self.tapi.del_post(int(i[2]),int(i[4]))
                self.tapi.del_thread(int(i[2]))
                at_del_list.append((i[0], i[2], "删除"))
            elif i[0] in self.managers and i[3].count("删封10天") > 0:
                self.tapi.ban_id(self.tapi.get_thread(int(i[2])).portrait, 10, "广告")
                self.tapi.del_post(int(i[2]),int(i[4]))
                self.tapi.del_thread(int(i[2]))
                at_del_list.append((i[0], i[2], "删封10天"))
            elif i[0] in self.managers and i[3].count("解除屏蔽") > 0:
                self.tapi.del_post(int(i[2]),int(i[4]))
                self.tapi.recover(int(i[2]), is_frs_mask=True)
                at_del_list.append((i[0], i[2], "解除屏蔽"))
            elif (i[0] in self.managers or i[0] in self.answerers) and i[3].count("屏蔽") > 0:
                self.tapi.del_post(int(i[2]),int(i[4]))
                self.tapi.block_thread(int(i[2]))
                at_del_list.append((i[0], i[2], "屏蔽"))

        # 获取首页帖子
        if first_check:
            thread_list = self.tapi.get_threads()+self.tapi.get_threads(2)+self.tapi.get_threads(3)
        else:
            thread_list =  self.tapi.get_threads()

        for thread in thread_list:
            # 跳过贴吧活动帖
            if thread.tid == 7559254857 or thread.tid == 7569495155:
                continue

            # 根据关键词自动删帖
            if re.search(self.adThreadKeyword,thread.content):
                self.tapi.del_thread(thread.tid)
                auto_del_list.append(thread)
                continue

            last_round_reply_time = 0
            if self.dig_record.__contains__(thread.tid):
                # 如果并没有新回复，跳过本帖
                if thread.reply_time == self.dig_record[thread.tid][1]:
                    continue
                last_round_reply_time = self.dig_record[thread.tid][1]

            try:
                post_list = self.tapi.get_posts(thread.tid)
                post_list = sorted(post_list, key=attrgetter('reply_time'), reverse=True) # 从最晚回复到最早回复排序

                for i in post_list:
                    if i.reply_time <= last_round_reply_time:
                        break
                    # 处理吧务删帖申请
                    if (i.username in self.managers):
                        if i.content == ".删除":
                            self.tapi.del_thread(thread.tid)
                            at_del_list.append((i.username, thread.tid, "删除"))
                        elif i.content == ".屏蔽":
                            self.tapi.block_thread(thread.tid)
                            self.tapi.del_post(thread.tid, i.pid)
                            at_del_list.append((i.username, thread.tid, "屏蔽"))
                    # 关键词删回复
                    if re.search(self.adPostKeyword, i.content):
                        self.tapi.del_post(thread.tid, i.pid)
                        auto_del_list.append((thread, i))

                # 处理坟帖
                # 判断记录中的坟帖状态
                was_tomb = self.get_tomb_status(thread.tid)
                # 获取挖坟回复列表
                thread_dig_list = self.judge_tomb_digging(thread,post_list)
                if len(thread_dig_list) != 0:
                    if thread_dig_list != ["疑似挖坟秒删"]:
                    # 防爆吧
                        anti_attack_result_list = self.anti_attack(thread_dig_list, thread.username, thread.tid)
                        anti_attack_list += anti_attack_result_list
                    # 报告挖坟情况
                    if len(thread_dig_list) > 0:
                        dig_list.append((thread, thread_dig_list))
            except Exception as e:
                print(str(e))
 

   

        return dig_list, anti_attack_list, at_del_list, auto_solved_dig_list, auto_del_list


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
            if self.unsolved_digger.__contains__(dig.portrait) and self.unsolved_digger[dig.portrait] != tid and dig.username != lz:
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

