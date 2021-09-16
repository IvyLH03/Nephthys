
class TiebaStats(object):
    def __init__(self, *args, **kwargs):
        self.thread_yesterday_reply = {}
        self.thread_last_hour_reply = {}
        self.thread_this_hour_reply = {}

        try:
            with open("stats.txt","r",encoding="utf-8") as f:
            # 读取保存的数据
            # 文件格式：
            # 1     七个数字，本周每天回复量
            # 2     七个数字，本周每天新帖量
            # 3     24个数字，今日每小时回复量
            # 4     24个数字，今日每小时新帖量
            # 5...... n     tid 昨天统计到的最后回复量 上小时统计到的最后回复量 本小时统计到的最后回复量
            # n+1 空行
            # n+2   一行，username，用空格分隔，今天活跃的用户
            # n+3   一行，username，用空格分隔，本小时活跃的用户
            # n+4   一行，七个数字，本周每天活跃用户数
            # n+5   一行，24个数字，今日每小时活跃用户数
                self.weekly_new_reply = f.readline().split()
                self.weekly_new_thread = f.readline().split()
                self.daily_new_reply = f.readline().split()
                self.daily_new_thread = f.readline().split()

                for i in self.weekly_new_reply: i = int(i)
                for i in self.weekly_new_thread: i = int(i)
                for i in self.daily_new_reply: i = int(i)
                for i in self.daily_new_thread: i = int(i)


                while True:
                    line = f.readline()
                    if line:
                        p1 = line.find(" ")
                        p2 = line.find(" ",start = p1 + 1)
                        p3 = line.find(" ",start = p2 + 1)
                        tid = int(line[:p1])
                        self.thread_yesterday_reply[tid] = int(line[p1+1:p2])
                        self.thread_last_hour_reply[tid] = int(line[p2+1:p3]) 
                        self.thread_this_hour_reply[tid] = int(line[p3+1:])
                    else:
                        break
                self.today_users = f.readline().split()
                self.this_hour_users = f.readline().split()
                self.weekly_users_num = f.readline().split()
                self.daily_users_num = f.readline().split()

                for i in self.weekly_users_num: i = int(i)
                for i in self.daily_users_num: i = int(i)
        except Exception as err:
            self.weekly_new_reply = [0,0,0,0,0,0,0]
            self.weekly_new_thread = [0,0,0,0,0,0,0]
            self.weekly_users_num = [0,0,0,0,0,0,0]
            self.daily_new_reply = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            self.daily_new_thread = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            self.daily_users_num = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

            self.today_users = []
            self.this_hour_users = []
     

    def save_record(self):
        with open("stats.txt","w",encoding="utf-8") as f:
            for i in self.weekly_new_reply:
                f.write(str(i)+" ")
            f.write("\n")
            for i in self.weekly_new_thread:
                f.write(str(i)+" ")
            f.write("\n")
            for i in self.daily_new_reply:
                f.write(str(i)+" ")
            f.write("\n")
            for i in self.daily_new_thread:
                f.write(str(i)+" ")
            f.write("\n")
            for i in range(len(self.thread_yesterday_reply)):
                f.write(str(i)+" "+str(self.thread_yesterday_reply[i])+" "+str(self.thread_last_hour_reply[i])+" "+str(self.thread_this_hour_reply)+"\n")
            f.write("\n")
            for i in self.today_users:
                f.write(i+" ")
            f.write("\n")
            for i in self.this_hour_users:
                f.write(i+" ")
            f.write("\n")
            for i in self.weekly_users_num:
                f.write(str(i)+" ")
            f.write("\n")
            for i in self.daily_users_num:
                f.write(str(i)+" ")
            f.write("\n")

    def regular_update(self, thread, post_list):
        pass

    def hourly_update(self):
        pass
