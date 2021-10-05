import requests as req
from hashlib import md5
import hashlib
from random import random
from time import sleep
import time

from typing import List

from data_class import *

class TiebaApi(object):

    def __init__(self, BDUSS, STOKEN, tieba_name):
        self.BDUSS = BDUSS
        self.STOKEN = STOKEN
        self.tieba_name = tieba_name
        self.app = req.session()
        self.app.headers = req.structures.CaseInsensitiveDict({'Content-Type': 'application/x-www-form-urlencoded',
                                                               'User-Agent': 'bdtb for Android 7.9.2',
                                                               'Connection': 'Keep-Alive',
                                                               'Accept-Encoding': 'gzip',
                                                               'Accept': '*/*',
                                                               'Host': 'c.tieba.baidu.com',
                                                               })

        self.web = req.session()
        self.web.headers = req.structures.CaseInsensitiveDict({'Host': 'tieba.baidu.com',
                                                               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
                                                               'Accept': '*/*',
                                                               'Accept-Encoding': 'gzip, deflate, br',
                                                               'DNT': '1',
                                                               'Cache-Control': 'no-cache',
                                                               'Connection': 'keep-alive',
                                                               'Upgrade-Insecure-Requests': '1'
                                                               })
        self.web.cookies.update({'BDUSS': self.BDUSS, 'STOKEN': self.STOKEN})
        self.fid = self._get_fid(tieba_name)
        self._get_tbs()
    def _get_fid(self,tieba_name):
        res = self.web.get("http://tieba.baidu.com/sign/info", params={
                                    'kw': tieba_name, 'ie': 'utf-8'}, timeout=(3, 10))

        if res.status_code != 200:
            raise ValueError("status code is not 200")

        main_json = res.json()
        if int(main_json['no']):
            raise ValueError(main_json['error'])
        if int(main_json['data']['errno']):
            raise ValueError(main_json['data']['errmsg'])

        self.fid = int(main_json['data']['forum_info']
                    ['forum_info']['forum_id'])
        return self.fid

    def _get_tbs(self):
        """
        获取tbs
        """
        r = self.web.get('http://tieba.baidu.com/dc/common/tbs').json()
        if r['is_login'] == 1: 
            self.tbs = r['tbs']
        else: 
            raise Exception('获取tbs时发生错误:' + str(r))
        return self.tbs

    @staticmethod
    def _app_sign(data: dict):
        """
        对参数字典做贴吧客户端签名
        """

        if data.__contains__('sign'):
            del data['sign']

        raw_list = [f"{key}={value}" for key, value in data.items()]
        raw_str = "".join(raw_list) + "tiebaclient!!!"

        md5 = hashlib.md5()
        md5.update(raw_str.encode('utf-8'))
        data['sign'] = md5.hexdigest().upper()

        return data

    def _get_user_info(self, id:str):
        """
        获取用户信息
        参数：
            id: string 昵称/用户名/id
        返回值：
            username: 用户名
            nickname: 用户昵称
            user_id: 用户 ID
            portrait: 用户头像portrait值
        """
        if id.startswith("tb."):
            params = {'id': id}
        else:
            params = {'un': id}
        try:
            res = self.web.get(
                "https://tieba.baidu.com/home/get/panel", params=params, timeout=(3, 10))

            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['no']):
                raise ValueError(main_json['error'])

            info_dict = main_json['data']
            username = info_dict.get('name', '')
            nickname = info_dict.get('name_show', '')
            user_id = info_dict.get('id', None)
            portrait = info_dict['portrait']

            return username, nickname, user_id, portrait

        except Exception as err:
            print(f"Failed to get UserInfo of {id} Reason:{err}")
            return '', '', '', ''

    def ban_id(self, id, day, reason='违反吧规'):
        """
        封禁用户
        参数:
            user_name：string 昵称或用户名
            day：int 封禁天数
            reason：string 封禁理由
        返回值：
            bool 是否封禁成功
            string 失败信息
        """
        username, nickname, user_id, portrait = self._get_user_info(id)
        if username == "" and nickname == "":
            return False, "获取用户信息失败"
        payload = {'BDUSS': self.BDUSS,
                    '_client_version': '7.9.2',
                    'day': day,
                    'fid': self.fid,
                    'nick_name': nickname, 
                    'ntn': 'banid',
                    'portrait': portrait, 
                    'post_id': 'null',
                    'reason': reason,
                    'tbs': self._get_tbs(),
                    'un': username,
                    'word': self.tieba_name,
                    'z': '6955178525',
                    }
        try:
            res = self.app.post("http://c.tieba.baidu.com/c/c/bawu/commitprison", data=self._app_sign(payload), timeout=(3, 10))
            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])

        except Exception as err:
            print(
                f"Failed to block {user.logname} in {tieba_name} Reason:{err}")
            return False, str(err)

        return True, ""

    def unban_id(self,id):
        """
        解封用户
        """
        username, nickname, user_id, portrait = self._get_user_info(id)
        payload = {'fn': self.tieba_name,
                   'fid': self.fid,
                   'block_un': username,
                   'block_uid': user_id,
                   'block_nickname': nickname,
                   'tbs': self._get_tbs()
                   }

        try:
            res = self.web.post(
                "https://tieba.baidu.com/mo/q/bawublockclear", data=self._app_sign(payload), timeout=(3, 10))

            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['no']):
                raise ValueError(main_json['error'])

        except Exception as err:
            print(str(err))
            return False, str(err)

        return True, ""

    def get_threads(self, pn=1, rn=30):
        """
        获取首页帖子。
        return:
            List[Thread]
        """
        payload = {'_client_version': '7.9.2',
                    'kw': self.tieba_name,
                    'pn': pn,
                    'rn': rn
                    }
        try:
            res = self.app.post("http://c.tieba.baidu.com/c/f/frs/page", data=self._app_sign(payload), timeout=(3, 10))
            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()

            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])
            
            user_dict = {}
            thread_list = []
            for user in main_json['user_list']:
                user_dict[user['id']] = user['name'], user['name_show'], user['portrait']
            for thread_raw in main_json['thread_list']:
                thread = Thread(thread_raw['tid'],
                                thread_raw['title'],
                                thread_raw['abstract'],
                                thread_raw['create_time'],
                                thread_raw['last_time_int'],
                                thread_raw['reply_num'],
                                user_dict[thread_raw['author_id']][0],
                                user_dict[thread_raw['author_id']][1],
                                user_dict[thread_raw['author_id']][2]
                                )
                thread_list.append(thread)

            return thread_list

        except Exception as err:
            print(str(err))
            return []
    def get_comments(self,tid,pid,pn=1,rn=30):
        """
        获取回复的楼中楼。
        参数:
            tid: 帖子的 tid
            pid: 回复的 pid
        return:
            List[Comment]
        """
        payload = {'_client_version':'7.9.2',
                   'kz':tid,
                   'pid':pid,
                   'pn':pn}

        try:
            res = self.app.post("http://c.tieba.baidu.com/c/f/pb/floor", data=self._app_sign(payload),timeout=(3,10))
            
            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])

            floor_no = main_json['post']['floor']
            post_list = []
            for raw_post in main_json['subpost_list']:
                post = Post(raw_post['id'],
                            raw_post['time'],
                            raw_post['content'],
                            raw_post['author']['name_show'],
                            raw_post['author']['name'],
                            floor_no,
                            True,
                            raw_post['author']['portrait'],
                            raw_post['author']['level_id'])
                post_list.append(post)
            if pn != 1:
                return post_list
            for i in range(2,int(main_json['page']['total_page'])+1):
                post_list += (self.get_comments(tid,pid,i))
            
            return post_list
        except Exception as err:
            print(str(err))

        return []

    def get_posts(self, tid, pn=1, rn=30):
        """
        获取帖子的回复
        参数:
            tid: 帖子的 tid
        return：
            List[Post]
        """
        payload = {'_client_version': '7.9.2',
                   'kz': tid,
                   'pn': pn,
                   'rn': rn
                   }
        #try:
        res = self.app.post("http://c.tieba.baidu.com/c/f/pb/page",data=self._app_sign(payload),timeout=(3,10))
            
        if res.status_code != 200:
            raise ValueError("status code is not 200")

        main_json = res.json()
        if int(main_json['error_code']):
            raise ValueError(main_json['error_msg'])

        post_list = []
        user_dict = {}
        for user in main_json['user_list']:
            if not user.get('portrait',None):
                continue
            if not user.__contains__('name'):
                continue
            user_dict[user['id']] = user['name'], user['name_show'], user['portrait'], user['level_id']
        for post_raw in main_json['post_list']:
            post = Post(post_raw['id'],
                        post_raw['time'],
                        post_raw['content'],
                        user_dict[post_raw['author_id']][1],
                        user_dict[post_raw['author_id']][0],
                        post_raw['floor'],
                        False,
                        user_dict[post_raw['author_id']][2],
                        user_dict[post_raw['author_id']][3]
                        )
            post_list.append(post)
            if int(post_raw['sub_post_number']) > 0:
                post_list += self.get_comments(tid,post_raw['id'])
        if pn != 1:
            return post_list

        page_num = int(main_json['page']['total_page'])
        if page_num :
            for i in range(2,page_num+1):
                post_list += self.get_posts(tid,i)
        return post_list

        #except Exception as err:
         #   print("错误，原因："+str(err))

        return []

    def get_thread(self,tid,pn=1,rn=30):
        """
        根据tid获取帖子信息。
        注意：无法正常获取最后回复信息
        """
        payload = {'_client_version': '7.9.2',
                   'kz': tid,
                   'pn': pn,
                   'rn': rn
                   }
        #try:
        res = self.app.post("http://c.tieba.baidu.com/c/f/pb/page",data=self._app_sign(payload),timeout=(3,10))
            
        if res.status_code != 200:
            raise ValueError("status code is not 200")

        main_json = res.json()
        if int(main_json['error_code']):
            raise ValueError(main_json['error_msg'])

        post_list = []
        user_dict = {}

        first_floor = main_json['post_list'][0]
        user = main_json['user_list'][0]


        return Thread(tid,first_floor['title'], main_json['thread']['origin_thread_info']['abstract'],first_floor['time'],0,main_json['thread']['reply_num'],user['name'],user['name_show'],user['portrait'])
    
    def reply_thread(self,tid,content):
        """
        回复帖子。
        """
        payload={'BDUSS': self.BDUSS,
        '_client_type': '2',
        '_client_version': '7.9.2',
        '_phone_imei': '000000000000000',
        'anonymous': '1',
        'content': content,
        'fid': self.fid,
        'from': '1008621x',
        'is_ad': '0',
        'kw': self.tieba_name,
        'model': 'MI+5',
        'net_type': '1',
        'new_vcode': '1',
        'tbs': self.tbs,
        'tid': tid,
        'timestamp': str(int(time.time())),
        'vcode_tag': '11',}

        try:
            res = self.app.post("http://c.tieba.baidu.com/c/c/post/add",data=self._app_sign(payload),timeout=(3,10))
        except Exception as err:
            print(err)

        sleep(2)




    def del_thread(self,tid):
        """
        删除主题帖。
        """
        payload = {'ie': 'utf-8',
                   'fid': self.fid,
                   'kw':self.tieba_name,
                   'tbs': self._get_tbs(),
                   'tid': str(tid),
                   'is_ban':0
                   }
        try:
            res = self.web.post(
                "https://tieba.baidu.com/f/commit/thread/batchDelete", data=payload, timeout=(3, 10))
            print(res.json())
            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])

        except Exception as err:
            print(err)

    def block_thread(self,tid):
        """
        屏蔽主题帖。
        """
        payload = {'BDUSS': self.BDUSS,
                   '_client_version': '7.9.2',
                   'fid': self.fid,
                   'is_frs_mask': 1,
                   'tbs': self.tbs,
                   'z': tid
                   }
        try:
            res = self.app.post(
                "http://c.tieba.baidu.com/c/c/bawu/delthread", data=self._app_sign(payload), timeout=(3, 10))

            print(res.json())
            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])

        except Exception as err:
            print(err)

    def del_post(self, tid, pid):
        """
        删除回复
        """

        payload = {'BDUSS': self.BDUSS,
                   '_client_version': '7.9.2',
                   'fid': self.fid,
                   'pid': pid,
                   'tbs': self.tbs,
                   'z': tid
                   }

        try:
            res = self.app.post(
                "http://c.tieba.baidu.com/c/c/bawu/delpost", data=self._app_sign(payload), timeout=(3, 10))

            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['error_code']):
                raise ValueError(main_json['error_msg'])

        except Exception as err:
            print(err)


    def get_at(self):
        payload = {'BDUSS':self.BDUSS}

        try:
            res = self.app.post(
                "http://c.tieba.baidu.com/c/u/feed/atme", data=self._app_sign(payload), timeout=(3, 10))
            main_json = res.json()

        except Exception as err:
            print(err)
            return []
    
        try:
            at_list = []
            if not main_json['at_list']:
                return []
            for at_raw in main_json['at_list']:
                print(at_raw)
                username = at_raw['quote_user']['name']
                if username == "": 
                    username = at_raw['quote_user']['name_show']
                nickname = at_raw['quote_user']['name_show']
                tid = at_raw['thread_id']
                text = at_raw['content']
                pid = at_raw['post_id']
                at_list.append([username, nickname,tid,text,pid])
            return at_list

        except Exception as err:
            print(err)
        
        return []

