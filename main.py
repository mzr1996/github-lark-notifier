# -*- coding:utf-8 -*-
from flask import Flask, request, jsonify
import json

import os
import requests
import json
import time
import urllib3
from loguru import logger
from datetime import datetime, timedelta
from threading import Thread

from actions import ACTIONS, CONFIG

WEBHOOK = CONFIG['web']['WEBHOOK']
HISTORY_FILE = 'history.txt'

urllib3.disable_warnings()
os.makedirs('./log', exist_ok=True)
logger.add("log/lark_log.log", rotation="1 week")

try:
    JSONDecodeError = json.decoder.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def is_not_null_and_blank_str(content):
    """
    非空字符串
    :param content: 字符串
    :return: 非空 - True，空 - False
    """
    if content and content.strip():
        return True
    else:
        return False

def parse_github_action(message: dict):

    return None


class LarkBot(object):

    def __init__(self,
                 webhook,
                 secret=None,
                 pc_slide=False,
                 fail_notice=False):
        '''
        机器人初始化
        :param webhook: 飞书群自定义机器人webhook地址
        :param secret:  机器人安全设置页面勾选“加签”时需要传入的密钥
        :param pc_slide:  消息链接打开方式，默认False为浏览器打开，设置为True时为PC端侧边栏打开
        :param fail_notice:  消息发送失败提醒，默认为False不提醒，开发者可以根据返回的消息发送结果自行判断和处理
        '''
        super(LarkBot, self).__init__()
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.webhook = webhook
        self.secret = secret
        self.pc_slide = pc_slide
        self.fail_notice = fail_notice

    def send_text(self, msg, open_id=[]):
        """
        消息类型为text类型
        :param msg: 消息内容
        :return: 返回消息发送结果
        """
        data = {"msg_type": "text", "at": {}}
        if is_not_null_and_blank_str(msg):  # 传入msg非空
            data["content"] = {"text": msg}
        else:
            logger.error("text类型，消息内容不能为空！")
            raise ValueError("text类型，消息内容不能为空！")

        logger.debug('text类型：%s' % data)
        return self.post(data)

    def post(self, data):
        """
        发送消息（内容UTF-8编码）
        :param data: 消息数据（字典）
        :return: 返回消息发送结果
        """
        try:
            post_data = json.dumps(data)
            response = requests.post(self.webhook,
                                     headers=self.headers,
                                     data=post_data,
                                     verify=False)
        except requests.exceptions.HTTPError as exc:
            logger.error("消息发送失败， HTTP error: %d, reason: %s" %
                          (exc.response.status_code, exc.response.reason))
            raise
        except requests.exceptions.ConnectionError:
            logger.error("消息发送失败，HTTP connection error!")
            raise
        except requests.exceptions.Timeout:
            logger.error("消息发送失败，Timeout error!")
            raise
        except requests.exceptions.RequestException:
            logger.error("消息发送失败, Request Exception!")
            raise
        else:
            try:
                result = response.json()
            except JSONDecodeError:
                logger.error("服务器响应异常，状态码：%s，响应内容：%s" %
                              (response.status_code, response.text))
                return {'errcode': 500, 'errmsg': '服务器响应异常'}
            else:
                logger.debug('发送结果：%s' % result)
                # 消息发送失败提醒（errcode 不为 0，表示消息发送异常），默认不提醒，开发者可以根据返回的消息发送结果自行判断和处理
                if self.fail_notice and result.get('errcode', True):
                    time_now = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(time.time()))
                    error_data = {
                        "msgtype": "text",
                        "text": {
                            "content":
                            "[注意-自动通知]飞书机器人消息发送失败，时间：%s，原因：%s，请及时跟进，谢谢!" %
                            (time_now, result['errmsg'] if result.get(
                                'errmsg', False) else '未知异常')
                        },
                        "at": {
                            "isAtAll": False
                        }
                    }
                    logger.error("消息发送失败，自动通知：%s" % error_data)
                    requests.post(self.webhook,
                                  headers=self.headers,
                                  data=json.dumps(error_data))
                return result


app = Flask(__name__)
app.debug = False


def work_time():
    now = datetime.now()
    today = dict(year=now.year, month=now.month, day=now.day)

    begin_work = datetime.strptime(CONFIG['behavior']['begin_work'], '%H:%M').replace(**today)
    end_work = datetime.strptime(CONFIG['behavior']['end_work'], '%H:%M').replace(**today)

    if CONFIG['behavior'].getboolean('only_weekdays') and now.weekday() >= 5:
        return False

    if begin_work < now < end_work:
        return True
    else:
        return False


def time_to_work(now):
    today = dict(year=now.year, month=now.month, day=now.day)
    begin_work = datetime.strptime(CONFIG['behavior']['begin_work'], '%H:%M').replace(**today)

    begin_work = begin_work + timedelta(days=1) if now >= begin_work else begin_work

    if CONFIG['behavior'].getboolean('only_weekdays'):
        while begin_work.weekday() >= 5:
            begin_work += timedelta(days=1)
    return begin_work

def lark_send_history():
    while True:
        now = datetime.now()
        next_work_time = time_to_work(now)
        # Sleep to the next workday 10:00 AM.
        logger.info(f'Next work time {next_work_time}')
        time.sleep((next_work_time - now).total_seconds())

        if os.path.exists(HISTORY_FILE):
            text = "休息期间错过的消息：\n"
            with open(HISTORY_FILE, 'r') as f:
                history = f.readlines()
                for item in history:
                    text += item
            os.remove(HISTORY_FILE)
        else:
            text = "平安夜，休息期间没有新的消息"
        logger.info("=== Send text:\n{}".format(text.strip()))
        bot = LarkBot(WEBHOOK)
        bot.send_text(text)


@app.route('/github/lark', methods=['post'])
def lark_robot():
    if request.data is None or len(request.data) == 0:
        return jsonify(dict(state="ok"))

    jsonstr = request.data.decode('utf-8')
    if CONFIG['behavior'].getboolean('save_receive'):
        os.makedirs('./receive', exist_ok=True)
        now_time = datetime.now().strftime('%Y%m%d-%H%M%S')
        save_path = f"./receive/{now_time}_0.json"
        index = 1
        while os.path.exists(save_path):
            save_path = f"./receive/{now_time}_{index}.json"
            index += 1
        with open(save_path, 'w') as f:
            f.write(jsonstr)
    jsonobj = json.loads(jsonstr)
    if jsonobj is None:
        logger.warning("parse json object is None: {}".format(jsonstr))
        return jsonify(dict(state="ok"))

    text = None
    type_ = 'Unknown'

    for action in ACTIONS:
        if action.condition(jsonobj):
            text = action.report(jsonobj)
            type_ = action.__class__.__name__
            break

    logger.info(f"=== Got action: {jsonobj.get('action', '')} | type: {type_}")

    if text is None:
        return jsonify(dict(state="ok"))

    if not work_time():
        # Save to HISTORY_FILE
        history_text = text.strip().replace('\n', ', ')
        logger.info(f"=== Not worktime, add {history_text} to history.txt")
        with open(HISTORY_FILE, 'a') as f:
            f.write(history_text + '\n')

        return jsonify(dict(state="ok"))

    logger.info("=== Send text:\n{}".format(text.strip()))
    bot = LarkBot(WEBHOOK)
    bot.send_text(text)

    return jsonify(dict(state="ok"))


if __name__ == '__main__':
    history_reporter = Thread(target=lark_send_history)
    history_reporter.start()
    app.run(host=CONFIG['web']['host'], port=int(CONFIG['web']['port']))
