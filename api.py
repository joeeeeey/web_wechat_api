from flask import Flask, url_for
from flask import jsonify
from flask import request
import itchat
from itchat.content import *
import base64

import requests # 发送http包 
from threading import Thread # 多线程
from time import sleep 
import os, sys, time, re, io
import json
import urllib.request
from urllib.parse   import quote
from urllib.request import urlopen
import threading

# 心跳,向文件传输助手定时推送保证不被登出
# def keep_sending(itchat):
#   while 1:
#       try:
#           time_str = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time()))
#           result = itchat.send_msg((time_str + " 还活着呢"), toUserName='filehelper')
#           Ret = result['BaseResponse']['Ret']
#           if Ret != 0:
#               return
#           sleep(10)
#       except Exception as e:
#           print("Error {0}".format(str(e)))
#           return 

# 自动回复
@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    Text = msg['Text']

@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    msg['Text'](msg['FileName'])
    return '@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName'])


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    itchat.add_friend(**msg['Text']) # 该操作会自动将新好友的消息录入，不需要重载通讯录
    itchat.send_msg('Nice to meet you!', msg['RecommendInfo']['UserName'])

    # {'MsgId': '3970970061797680506', 'FromUserName': '@@c47d15dd20ad688bb05837ca869af2d274d7c041c8862e91b3f1c3ab1841fd81', 
    #'ToUserName': '@4c4a1417b6b770402ae3a366e7ffa132', 'MsgType': 1, 'Content': '@Blackice\u2005', 
    #'Status': 3, 'ImgStatus': 1, 'CreateTime': 1489375281, 'VoiceLength': 0, 'PlayLength': 0, 
    #'FileName': '', 'FileSize': '', 'MediaId': '', 'Url': '', 'AppMsgType': 0, 'StatusNotifyCode': 0, 
    #'StatusNotifyUserName': '', 'RecommendInfo': {'UserName': '', 'NickName': '', 'QQNum': 0, 'Province': '', 
    #'City': '', 'Content': '', 'Signature': '', 'Alias': '', 'Scene': 0, 'VerifyFlag': 0, 'AttrStatus': 0, 
    #'Sex': 0, 'Ticket': '', 'OpCode': 0}, 'ForwardFlag': 0, 'AppInfo': {'AppID': '', 'Type': 0}, 
    #'HasProductId': 0, 'Ticket': '', 'ImgHeight': 0, 'ImgWidth': 0, 'SubMsgType': 0, 'NewMsgId': 3970970061797680506, 
    #'OriContent': '', 'ActualUserName': '@6bbbcd29bafd4834cee7145000e505e3', 'ActualNickName': '黄尔东', 'isAt': True, 'Type': 'Text', 'Text': '@Blackice\u2005'}

@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    print(msg)
    if msg['isAt']:
        index = msg['Content'].find('2323')
        Text = msg['Content'][index:200]
        print(Text)
        print(Text[0:4])

# 监控登陆状态 初始化
def monitor_login(itchat):
    isLoggedIn = False
    while 1:
        waiting_time = 0
        while not isLoggedIn:
            status = itchat.check_login()
            waiting_time += 1
            print(waiting_time)
            if status == '200':
                print ("status is 200!")
                isLoggedIn = True
            elif status == '201':
                print ("status is 201!")
                if isLoggedIn is not None: 
                    print ('Please press confirm on your phone.')
                    isLoggedIn = None
            elif status != '408':
                break
            elif waiting_time == 5:
                raise
        if isLoggedIn:
            print ("已经确认登陆了")
            break

    print ("==== here status is ", status)
    itchat.check_login()
    itchat.web_init()
    itchat.show_mobile_login()
    itchat.get_contact(True) 
    # you can do your business here
    itchat.start_receiving()
    itchat.run()

# 将二维码转化为base64 string, 简单的使用了全局变量
qr_b64 = ""
def QR_to_b64(uuid, status, qrcode):
  global qr_b64
  qr_b64 = base64.b64encode(qrcode)
  return qr_b64

app = Flask(__name__)


thread = Thread()
# 生成二维码 登陆
# curl 'http://127.0.0.1:9118/wechat_login' -H Content-Type:application/json -v
@app.route('/wechat_login')
def api_wechat_login():
    global thread
    uuid = itchat.get_QRuuid()
    itchat.get_QR(uuid=uuid, qrCallback=QR_to_b64)
    print(thread.is_alive())
    if thread.is_alive():
        return jsonify({'success': 0, 'msg': '已有登陆线程存在' })

    # thread = task(monitor_login,itchat)
    thread = Thread(target = monitor_login, args = (itchat, ))
    thread.start()
    return jsonify({'success': 1, 'qr': qr_b64.decode("utf-8") })


# 查看登陆状态
# curl 'http://127.0.0.1:9118/wechat_check_login' -H Content-Type:application/json -v
@app.route('/wechat_check_login', methods=['GET', 'POST'])
def wechat_check_login():
    return itchat.check_login()

# curl -d '{"msg": "你好啊", "UserName": "filehelper"}' 'http://127.0.0.1:9118/send_msg' -H Content-Type:application/json -v
# 发送消息
@app.route('/send_msg', methods=['GET', 'POST'])
def send_msg():
    # itchat.send_msg('Hello, filehelper呀这是接口发送', toUserName='filehelper')
    try:
        data = json.loads(request.data)
        msg = data['msg']
        userName = data['UserName']
        if len(itchat.get_friends()) != 0:
            result = itchat.send_msg(msg, toUserName=userName)
            # <ItchatReturnValue: {'BaseResponse': {'Ret': 0, 'ErrMsg': '请求成功', 'RawMsg': '请求成功'}, 'MsgID': '1034229085747027697', 'LocalID': '14887975733746'}>
            print(result)
            Ret = result['BaseResponse']['Ret']
            return jsonify({'success': 1, 'msg': '成功发送', 'Ret': Ret})
        else:
            return jsonify({'success': 0, 'msg': '尚未登陆'})  
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# curl -d '{"fileDir": "/images/qr_code.png", "UserName": "filehelper"}' 'http://127.0.0.1:9118/send_image' -H Content-Type:application/json -v
# 发送消息
@app.route('/send_image', methods=['GET', 'POST'])
def send_image():
    try:
        data = json.loads(request.data)
        fileDir = data['fileDir']
        userName = data['UserName']
        if len(itchat.get_friends()) != 0:
            result = itchat.send_msg(fileDir=fileDir, toUserName=userName)
            Ret = result['BaseResponse']['Ret']
            if Ret == 0:
                return jsonify({'success': 1, 'msg': '成功发送', 'Ret': Ret})
            else:   
                return jsonify({'success': 0, 'msg': '成功失败', 'Ret': Ret})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 获取微信群
# curl 'http://127.0.0.1:9118/get_chatrooms' -H Content-Type:application/json -v
@app.route('/get_chatrooms', methods=['GET', 'POST'])
def get_chatrooms():
    try:
        return jsonify({'success': 1, 'data': itchat.get_chatrooms()})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 获取微信好友
# curl 'http://127.0.0.1:9118/get_friends' -H Content-Type:application/json -v
@app.route('/get_friends', methods=['GET', 'POST'])
def get_friends():
    try:
        return jsonify({'success': 1, 'data':itchat.get_friends()})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 获取微信公众号
# curl 'http://127.0.0.1:9118/get_mps' -H Content-Type:application/json -v
@app.route('/get_mps', methods=['GET', 'POST'])
def get_mps():
    try:
        data = json.loads(request.data)
        name = data['name']
        return jsonify({'success': 1, 'data': itchat.get_mps()})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 查找微信好友
# curl -d '{"name": "Blackice"}' 'http://127.0.0.1:9118/search_friends' -H Content-Type:application/json -v
@app.route('/search_friends', methods=['GET', 'POST'])
def search_friends():
    try:
        data = json.loads(request.data)
        name = data['name']
        return jsonify({'success': 1, 'data': itchat.search_friends(name=name)})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 查找微信群
# curl -d '{"name": "老年人活动中心"}' 'http://127.0.0.1:9118/search_chatrooms' -H Content-Type:application/json -v
@app.route('/search_chatrooms', methods=['GET', 'POST'])
def search_chatrooms():
    try:
        data = json.loads(request.data)
        name = data['name']
        return jsonify({'success': 1, 'data': itchat.search_chatrooms(name=name)})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 更新讨论组
# curl -d '{"userName": "das"}' 'http://127.0.0.1:9118/update_chatroom' -H Content-Type:application/json -v
@app.route('/update_chatroom', methods=['GET', 'POST'])
def update_chatroom():
    try:
        data = json.loads(request.data)
        userName = data['userName']
        return jsonify({'success': 1, 'data': itchat.update_chatroom(userName=userName)})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  


# 登出
# curl 'http://127.0.0.1:9118/logout' -H Content-Type:application/json -v
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        # notify_LoggedStatus('0')
        itchat.logout()
        return jsonify({'success': 1, 'msg': '已经登出'})
    except Exception as e:
        return jsonify({'success': 0, 'msg': "Error {0}".format(str(e))})  

if __name__ == '__main__':
    app.run(port=9118)
    # app.run(debug=True, port=9118)