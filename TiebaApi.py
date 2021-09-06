import requests as req
from hashlib import md5
import hashlib
from random import random
from time import sleep

class TiebaApi(object):

    def __init__(self, BDUSS, STOKEN, tieba_name):
        self.BDUSS = BDUSS
        self.STOKEN = STOKEN
        self.tieba_name = tieba_name
        self.app = req.session()
        self.app.headers = req.structures.CaseInsensitiveDict({'Content-Type': 'application/x-www-form-urlencoded',
                                                               'User-Agent': 'bdtb for Android 12.8.2.1',
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

    def _get_user_info(self, user_name):
        """
        获取用户信息
        参数：
            user_name: string 昵称或用户名
        返回值：
            user_id: 用户名
            nickname: 用户昵称
            portrait: 用户头像portrait值
        """
        params = {'un': user_name}
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
            print(f"Failed to get UserInfo of {user_name} Reason:{err}")
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
                    '_client_version': '12.8.2.1',
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
                "https://tieba.baidu.com/mo/q/bawublockclear", data=payload, timeout=(3, 10))

            if res.status_code != 200:
                raise ValueError("status code is not 200")

            main_json = res.json()
            if int(main_json['no']):
                raise ValueError(main_json['error'])

        except Exception as err:
            print(str(err))
            return False

        return True