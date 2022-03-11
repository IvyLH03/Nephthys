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
answerer_group = int(config["AnswererGroup"])
tscout = TiebaScout(config["BDUSS"],config["STOKEN"],config["TiebaName"])
welcome_message = True

@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    await app.sendFriendMessage(friend,MessageChain.create([Plain("test")]))

@bcc.receiver("GroupMessage")
async def groupMessage(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    global dig_thread_dict
    global tscout
    global bawu_group
    global answerer_group
    msg = message.asDisplay()
    if group.id == bawu_group:
        if message.has(Quote):
            quote_id = message.getFirst(Quote).id
            if dig_thread_dict.__contains__(quote_id):
                tid = dig_thread_dict[quote_id][0].tid
                user_list = dig_thread_dict[quote_id][1]
                if msg.count("已处理") > 0:
                    tscout.dig_record[tid][2] = max(dig_thread_dict[quote_id][0].reply_time,tscout.dig_record[tid][2])
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                    dig_thread_dict.pop(quote_id)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已将帖子"+str(tid)+"标记为已处理")]))
                
                elif msg.count("封禁全部") > 0:
                    tscout.dig_record[tid][2] = max(dig_thread_dict[quote_id][0].reply_time,tscout.dig_record[tid][2])
                    s = " "
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                        tscout.tapi.ban_id(user[2],1,"在坟帖 "+dig_thread_dict[quote_id][0].title+" 下挖坟")
                        s += user[0] + " "
                    dig_thread_dict.pop(quote_id)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已将"+s+"封禁")]))
                
                elif msg.count("封禁并删除") > 0:
                    tscout.dig_record[tid][2] = max(dig_thread_dict[quote_id][0].reply_time,tscout.dig_record[tid][2])
                    s = " "
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                        tscout.tapi.ban_id(user[2],1,"在坟帖 "+dig_thread_dict[quote_id][0].title+" 下挖坟")
                        s += user[0] + " "
                    tscout.tapi.del_thread(dig_thread_dict[quote_id][0].tid)
                    dig_thread_dict.pop(quote_id)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已将"+s+"封禁")]))
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已删帖")]))

                elif msg.count("封禁并屏蔽") > 0:
                    tscout.dig_record[tid][2] = max(dig_thread_dict[quote_id][0].reply_time,tscout.dig_record[tid][2])
                    s = " "
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                        tscout.tapi.ban_id(user[2],1,"在坟帖 "+dig_thread_dict[quote_id][0].title+" 下挖坟")
                        s += user[0] + " "
                    tscout.tapi.block_thread(dig_thread_dict[quote_id][0].tid)
                    dig_thread_dict.pop(quote_id)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已将"+s+"封禁\n已屏蔽")]))

                elif msg.count("楼主更新了") > 0:
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                    tscout.dig_record[tid][0] = False
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已经取消本帖的坟帖标记")]))

                elif msg.count("加入白名单") > 0:
                    for user in user_list:
                        if tscout.unsolved_digger.__contains__(user[2]):
                            tscout.unsolved_digger.pop(user[2])
                    tscout.dig_record[tid][0] = False
                    tscout.append_whitelist(tid)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已将本帖加入白名单")]))
        elif msg.startswith("."):
            if msg == (".测试"):
                await app.sendGroupMessage(group, MessageChain.create([Plain("Hello World!")]))
            elif msg == (".退出"):
                tscout.save_records()
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
                    if msg.find(" ") > 0: 
                        username = msg[msg.find("：")+1:msg.find(" ")]
                        reason = msg[msg.find(" "):]
                    else:
                        username = msg[msg.find("：")+1:len(msg)]
                        reason = " "
                    flag, result = tscout.tapi.ban_id(username,day,reason)
                    if flag:
                        await app.sendGroupMessage(group, MessageChain.create([Plain("封禁成功")]))
                    else:
                        await app.sendGroupMessage(group, MessageChain.create([Plain("封禁失败，原因："+result)]))
                except Exception as err:
                    print(err)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.封禁10天：圆号与游走球 恶意挖坟”\n目前仅支持封禁1、3、10天")]))
            elif msg.startswith(".删除："):
                try:
                    tid = int(msg[msg.find("：")+1:])
                    tscout.tapi.del_thread(tid)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("已删除 https://tieba.baidu.com/p/"+str(tid))]))
                except Exception as err:
                    print(err)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.删除：1234567890”")]))
            elif msg.startswith(".解封："):
                try:
                    username = msg[msg.find("：")+1:]
                    flag, result = tscout.tapi.unban_id(username)
                    if flag:
                        await app.sendGroupMessage(group, MessageChain.create([Plain("解封成功")]))
                    else:
                        await app.sendGroupMessage(group,MessageChain.create([Plain("解封失败，原因："+result)]))
                except Exception as err:
                    print(err)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.解封：圆号与游走球”")]))
            elif msg.startswith(".添加广告回复关键词"):
                try:
                    tscout.adPostKeyword += "|" + msg[msg.find("：")+1:]
                    await app.sendGroupMessage(group, MessageChain.create([Plain("添加成功")]))
                except Exception as err:
                    print(err)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("失败：格式有误\n格式示例：“.添加广告回复关键词：摆度网盘”")]))
            elif msg.startswith(".广告回复关键词"):
                s = "当前广告回复关键词："
                lst = tscout.adPostKeyword.split("|")
                for keyword in lst:
                    s += "\n" + keyword
                await app.sendGroupMessage(group, MessageChain.create([Plain(s)]))
            
    elif group.id == answerer_group:
        pass

            

async def regular_checking(welcome_message=False):
    global dig_thread_dict
    global bawu_group
    global answerer_group
    for group in await app.groupList():
        if group.id == bawu_group:
            slayerGroup = group
        elif group.id == answerer_group:
            answererGroup = group
    dig_result_list, anti_attack_result_list, at_del_list, auto_solved_dig_list, auto_del_list = tscout.regular_checking(welcome_message)
    for i in dig_result_list:
        s = "检测到挖坟\n"
        s += "标题："+i[0].title+"\n链接：https://tieba.baidu.com/p/"+str(i[0].tid)+"\n"
        user_list = []
        if i[1] == ["疑似挖坟秒删"]:
            s += "\n疑似挖坟秒删"
            await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))
            continue
        else:
            s += "\n挖坟回复:\n"
            for j in i[1]:
                s += "\n" + str(j.floor_no) + "楼"
                if j.is_lzl:
                    s += "(楼中楼）"
                s += "：" + j.nickname 
                if j.nickname != j.username:
                    s += "(" + j.username +")"
                if j.username == i[0].username:
                    s += "【楼主】"
                s += "\n回复内容：\n" + j.content + "\n"
                user_list.append([j.username, j.pid, j.portrait])
        k = await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))
        k = k.messageId
        dig_thread_dict[k] = [i[0], user_list]
    for i in anti_attack_result_list:
        await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain("检测到连续疑似挖坟："+i+"\n已自动封禁")]))

    for at_del in at_del_list:
        s = at_del[0] + " " + at_del[2] + "了 " + "https://tieba.baidu.com/p/" + str(at_del[1])
        if at_del[0] in tscout.answerers:
            t = tscout.tapi.get_thread(at_del[1])
            s += "\n标题：" + t.title + "\n内容：\n" + t.content
            await app.sendGroupMessage(answererGroup,MessageChain.create([Plain(s)]))
        else:
            await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))

    for i in auto_solved_dig_list:
        s = "自动封禁挖坟\n" 
        s += "标题："+i[0].title+"\n链接：https://tieba.baidu.com/p/"+str(i[0].tid)+"\n"
        s += "\n挖坟回复:\n"
        s += str(i[1].floor_no) + "楼"
        if i[1].is_lzl:
            s += "(楼中楼）"
        s +=  "："+i[1].nickname 
        if i[1].nickname != i[1].username:
            s += "(" + i[1].username +")"
        s += "\n回复内容：\n" + i[1].content + "\n"
        await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))

    for i in auto_del_list:
        s = "关键词删帖\n\n"
        if isinstance(i, Thread):
            s += "标题："+i.title+"\n链接：https://tieba.baidu.com/p/"+str(i.tid)+"\n内容:" + i.content+"\n\n发帖人:"+i.username+"\nportrait："+i.portrait
        else:
            s += "链接：https://tieba.baidu.com/p/"+str(i[0].tid)+"\n回复内容："+i[1].content+"\n\n发帖人:"+i[1].username+"\nportrait："+i[1].portrait
        await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain(s)]))


scheduler = GraiaScheduler(loop,bcc)
@scheduler.schedule(crontabify("* * * * * 0,5,10,15,20,25,30,35,40,45,50,55"))
async def regular_check_schedule():
    global welcome_message
    if welcome_message:
        for group in await app.groupList():
            if group.id == bawu_group:
                slayerGroup = group
        await app.sendGroupMessage(slayerGroup,MessageChain.create([Plain("早上好")]))
        await regular_checking(welcome_message=True)
        welcome_message = False
    else:
        await regular_checking()



app.launch_blocking()