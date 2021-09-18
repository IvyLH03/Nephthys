from data_class import *
from TiebaApi import *
from tomb_digger_manager import *
from typing import List

class TiebaScout(object):
    def __init__(self, BDUSS, STOKEN, tieba_name, *args, **kwargs):
        self.tapi = TiebaApi(BDUSS,STOKEN,tieba_name)
        self.tdm = TombDiggerManager()
        self.illegal_words = []
        self.unsolved_digger = {}

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
            if self.tdm.dig_record.__contains__(thread.tid):
                # 如果并没有新回复，跳过本帖
                if thread.reply_time == self.tdm.dig_record[thread.tid][1]:
                    continue
                last_round_reply_time = self.tdm.dig_record[thread.tid][1]


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
                if (i.username in self.tdm.managers) and i.content == ".删除":
                    self.tapi.del_thread(thread.tid)
                    at_del_list.append((i.username, thread.tid))
                    break

            # 处理坟帖
            # 判断记录中的坟帖状态
            was_tomb = self.tdm.get_tomb_status(thread.tid)
            # 获取挖坟回复列表
            thread_dig_list = self.tdm.judge_tomb_digging(thread,post_list)
            if len(thread_dig_list) != 0:
                # 如果之前就是坟帖，自动封禁并封坟
                # 【等封号解除后再完善这部分】

                # 防爆吧
                if thread_dig_list != ["疑似挖坟秒删"]:
                    anti_attack_result_list = self.anti_attack(thread_dig_list, thread.username, thread.tid)
                anti_attack_list += anti_attack_result_list

                # 报告挖坟情况，就算已经自动处理了也报告
                dig_list.append((thread, thread_dig_list))
 

   

        return dig_list, anti_attack_list, at_del_list

    def save_records(self):
        self.tdm.save_records()

    def append_whitelist(self,tid):
        """
        将帖子加入坟帖白名单，以后不再视为坟帖。
        """
        if tid not in self.tdm.permanent_whitelist:
            self.tdm.permanent_whitelist.append(tid)
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

