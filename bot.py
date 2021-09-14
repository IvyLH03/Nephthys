from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
import asyncio

from TiebaApi import *
from tieba_scout import *

from graia.application.message.elements.internal import *
from graia.application.friend import Friend
from graia.application.group import Group,Member

from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify
from graia.scheduler import timers

import datetime
import time
import json
from threading import Thread as tThread
import sys

with open("config.json","r",encoding="utf-8") as f:
    config = json.load(f)

dig_thread_dict = {}


loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080",
        authKey=config["AuthKey"],
        account=int(config["BotQQ"]),
        websocket=True 
    )
)
bawu_group = int(config["BawuGroup"])

tscout = TiebaScout(config["BDUSS"],config["STOKEN"],config["TiebaName"])

@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    await app.sendFriendMessage(friend,MessageChain.create([Plain("test")]))

@bcc.receiver("GroupMessage")
async def groupMessage(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    global dig_thread_dict
    global tscout
    msg = message.asDisplay()
    if message.has(Quote):
        quote_id = message.getFirst(Quote).id
        if dig_thread_dict.__contains__(quote_id):
            tid = dig_thread_dict[quote_id][0].tid
            user_list = dig_thread_dict[quote_id][1]
            print(tid)
            if msg.count("已处理") > 0:
                tscout.tdm.dig_record[tid][2] = dig_thread_dict[quote_id][0].reply_time
                dig_thread_dict.pop(quote_id)
                await app.sendGroupMessage(group, MessageChain.create([Plain("已将帖子"+str(tid)+"标记为已处理")]))
            elif msg.count("封禁全部") > 0:
                tscout.tdm.dig_record[tid][2] = dig_thread_dict[quote_id][0].reply_time
                for user in user_list:
                    tscout.tapi.ban_id(user,1,"在坟帖"+dig_thread_dict[quote_id][0].title+"下挖坟")
                dig_thread_dict.pop(quote_id)
                await app.sendGroupMessage(group, MessageChain.create([Plain("已将帖子"+str(tid)+"下所有挖坟回复封禁")]))
    elif msg.startswith("."):
        if msg == (".测试"):
            await app.sendGroupMessage(group, MessageChain.create([Plain("Hello World!")]))
        elif msg == (".退出"):
            tscout.update_stats()
            await app.sendGroupMessage(group, MessageChain.create([Plain("记录已保存！")]))
            await app.sendGroupMessage(group, MessageChain.create([Plain("晚安")]))
            exit(0)
            await app.sendGroupMessage(group, MessageChain.create([Plain("退出失败")]))
        elif msg.startswith(".加入白名单："):
            try:
                tid = int(msg[msg.find("：")+1:])
                if tscout.append_whitelist(tid):
                    await app.sendGroupMessage(group, MessageChain.create([Plain("加入成功")]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([Plain("失败：帖子已在白名单中")]))
            except Exception as err:
                print(err)
                await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.加入白名单：1234567890”")]))
        elif msg.startswith(".封禁"):
            try:
                day = int(msg[msg.find("禁")+1:msg.find("天")])
                username = msg[msg.find("：")+1:msg.find(" ")]
                reason = msg[msg.find(" "):]
                flag, result = tscout.tapi.ban_id(username,day,reason)
                if flag:
                    await app.sendGroupMessage(group, MessageChain.create([Plain("封禁成功")]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([Plain("封禁失败，原因："+result)]))
            except Exception as err:
                print(err)
                await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.封禁10天：圆号与游走球 恶意挖坟”\n目前仅支持封禁1、3、10天")]))

async def regular_checking():
    global dig_thread_dict
    global bawu_group
    for group in await app.groupList():
        if group.id == bawu_group:
            slayerGroup = group
    print("开始一轮新的检测")
    result_list = tscout.regular_checking()
    for i in result_list:
        s = "检测到挖坟"
        s += "标题："+i[0].title+"\n链接：https://tieba.baidu.com/p/"+str(i[0].tid)
        user_list = []
        if i[1] == ["疑似挖坟秒删"]:
            s += "\n疑似挖坟秒删"
            await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))
            continue
        else:
            s += "\n挖坟回复:\n"
            for j in i[1]:
                s += "\n" + str(j.floor_no)
                if j.is_lzl:
                    s += "(楼中楼）"
                s += "：" + j.content + "\n昵称：" + j.nickname + "\n用户名：" + j.username +"\n"
                user_list.append(j.username)
        k = await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))
        k = k.messageId
        dig_thread_dict[k] = [i[0], user_list]


scheduler = GraiaScheduler(loop,bcc)
@scheduler.schedule(crontabify("* * * * * 0"))
async def regular_check_schedule():
    await regular_checking()




app.launch_blocking()