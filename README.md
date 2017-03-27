# web_wechat_api
基于itchat&amp;flask的web微信接口

# 用法 
    将微信的登陆发消息接口可以用restful接口的形式调用

# 依赖安装(macOS,Centos)

```bash
# 建议python3
$ sudo pip install itchat
$ sudo pip install flask
```

# 启动
```bash
$ python api.py # 端口在api.py底部配置
```

# 微信二维码登陆
```bash
$ curl 'http://127.0.0.1:9118/wechat_login' -H Content-Type:application/json -v # 返回json {'success': 1, 'qr': "xxxx..." } 这里将二维码图片转为base64的字符,方便调用端显示。
```

# 其他接口
    见 api.py 中 @app.route。
