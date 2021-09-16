from data_class import *
from TiebaApi import *
from tomb_digger_manager import *

class TiebaScout(object):
    def __init__(self, BDUSS, STOKEN, tieba_name, *args, **kwargs):
        self.tapi = TiebaApi(BDUSS,STOKEN,tieba_name)
        self.tdm = TombDiggerManager()
        self.illegal_words = []

    def regular_checking(self,type=0):
        """
        type暂时没用
        """
        thread_list =  self.tapi.get_threads()
        dig_list =  []
        auto_solved_dig_list = []
        for thread in thread_list:
            if self.tdm.dig_record.__contains__(thread.tid) and thread.reply_time == self.tdm.dig_record[thread.tid][1]:
                # 如果并没有新回复，跳过本帖
                continue
            post_list = self.tapi.get_posts(thread.tid)
            post_list = sorted(post_list, key=attrgetter('reply_time'), reverse=True) # 从最晚回复到最早回复排序
            # 查找是否存在挖坟
            was_tomb = self.tdm.dig_record[thread.tid]
            thread_dig_list = self.tdm.judge_tomb_digging(thread,post_list)
            if len(thread_dig_list) != 0:
                dig_list.append((thread, thread_dig_list))
        """
            # 查询at列表：
        at_del_list = []
        try:
            at_list = self.tapi.get_at()
            for i in at_list:
                if i[0] in self.tdm.managers and i[3].count("删除") > 0:
                    self.tapi.del_thread(int(i[2]))
                    at_del_list.append([username, tid])
        except Exception as err:
            print(err)
        """

        return dig_list

    def save_records(self):
        self.tdm.save_records()

    def append_whitelist(self,tid):
        if tid not in self.tdm.permanent_whitelist:
            self.tdm.permanent_whitelist.append(tid)
            return True
        else:
            return False

    def _post_cmp(self, x: Post, y: Post):
        if x.reply_time < y.reply_time:
            return 1
        if x.reply_time > y.reply_time:
            return -1
        return 0

