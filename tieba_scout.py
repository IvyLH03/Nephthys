from data_class import *
from TiebaApi import *
from tomb_digger_manager import *

class TiebaScout(object):
    def __init__(self, BDUSS, STOKEN, tieba_name, *args, **kwargs):
        self.tapi = TiebaApi(BDUSS,STOKEN,tieba_name)
        self.tdm = TombDiggerManager()

    def regular_checking(self):
        thread_list =  self.tapi.get_threads()
        dig_list =  []
        for thread in thread_list:
            if thread.reply_time == self.tdm.dig_record[thread.tid][1]:
                continue
            post_list = self.tapi.get_posts(thread.tid)
            thread_dig_list = self.tdm.judge_tomb_digging(thread,post_list)
            if len(thread_dig_list) != 0:
                dig_list.append((thread, thread_dig_list))
                print(thread_dig_list)
        return dig_list


    def update_stats(self):
        self.tdm.save_records()


