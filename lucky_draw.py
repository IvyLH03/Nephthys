import json
from TiebaApi import *
import time
import datetime as dt
import random
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
import asyncio
from graia.application.message.elements.internal import *
from graia.application.friend import Friend
from graia.application.group import Group,Member
from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify
from graia.scheduler import timers


with open("config.json","r",encoding="utf-8") as f:
    config = json.load(f)
tapi = TiebaApi(config['BDUSS'],config['STOKEN'],"terraria")
managers = config['Managers']

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

@bcc.receiver("GroupMessage")
async def groupMessage(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if message.asDisplay() == ".测试":
        s = lucky_draw()
        await app.sendGroupMessage(group, MessageChain.create([Plain("抽奖脚本正常")]))
    elif message.asDisplay() == ".抽奖":
        for group in await app.groupList():
            if group.id == bawu_group:
                bawuGroup = group
        s = lucky_draw()
        await app.sendGroupMessage(bawuGroup,MessageChain.create([Plain(s)]))


def lucky_draw():

    start_time = int(time.mktime(dt.date.today().timetuple())) - 86400
    end_time = int(time.mktime(dt.date.today().timetuple()))

    post_list = tapi.get_posts(7712493061)
    user_list = []
    meaningless = [1]

    post_list.reverse()
    for i in post_list:
        if not i.floor_no in meaningless and i.reply_time > start_time and i.reply_time < end_time and not i.is_lzl and int(i.level) >= 3 and i.portrait not in user_list and i.username != "TerrariaTieba":
            user_list.append(i.portrait)
        if i.is_lzl and i.username in managers and i.content == "本回复不符合主题":
            meaningless.append(i.floor_no)
    
    random.seed(time.time())
    rand_result = []
    print("共有",len(user_list),"人参与抽奖")
    tmp_user_list = user_list.copy()
    result = "【本日抽奖结果】\n游戏激活码："
    for i in range(1,6):
        x = random.randint(0,len(user_list)-1)
        rand_result.append(x)
        user = tapi._get_user_info(user_list[x])
        user_list.remove(user_list[x])
        result += "\n"+user[1]
        if user[1] != user[0]:
            result += "("+ user[0] + ")"
    result += "\n京东卡："
    x = random.randint(0,len(tmp_user_list)-1)
    rand_result.append(x)
    user = tapi._get_user_info(tmp_user_list[x])
    result += "\n"+user[1]
    if user[1] != user[0]:
        result += "("+ user[0] + ")"

    return result
    
scheduler = GraiaScheduler(loop,bcc)
@scheduler.schedule(crontabify("1 0 * * * 0"))
async def check():
    for group in await app.groupList():
            if group.id == bawu_group:
                bawuGroup = group
    s = lucky_draw()
    await app.sendGroupMessage(bawuGroup,MessageChain.create([Plain(s)]))

app.launch_blocking()
