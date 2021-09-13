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
    msg = message.asDisplay()
    if message.has(Quote):
        quote_id = message.getFirst(Quote).id
        if dig_thread_dict.__contains__(quote_id):
            tid = dig_thread_dict[quote_id][0].tid
            user_list = []
            for dig in dig_thread_dict[quote_id][1]:
                user_list.append(dig.username)
            print(tid)
    elif msg.startswith("."):
        if msg == (".测试"):
            await app.sendGroupMessage(group, MessageChain.create([Plain("Hello World!")]))
        if msg == (".退出"):
            tscout.update_stats()
            await app.sendGroupMessage(group, MessageChain.create([Plain("记录已保存！\n晚安")]))
            exit(0)
            await app.sendGroupMessage(group, MessageChain.create([Plain("退出失败")]))

async def regular_checking():
    global dig_thread_dict
    global bawu_group
    print("start regular checking!")
    for group in await app.groupList():
        if group.id == bawu_group:
            slayerGroup = group
    print("开始一轮新的检测")
    result_list = tscout.regular_checking()
    for i in result_list:
        s = "检测到挖坟"
        s += "标题："+i[0].title+"\n链接：https://tieba.baidu.com/p/"+str(i[0].tid)
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
        k = await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)])).messageId
        dig_thread_dict[k] = i

app.launch_blocking()
loop.run_until_complete(regular_checking())