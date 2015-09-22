#!/usr/bin/env python
from __future__ import print_function

import json
import requests
import sys
import threading
import time
import tornado.ioloop
import tornado.web
import zephyr

from settings import *

def log(*args):
    print(*args, file=sys.stderr)

def on_zephyr(msg):
    if msg.kind != 2:
        return
    if msg.opcode.lower() == 'auto':
        return
    if msg.cls.lower() not in ZEPHYR_TO_SLACK:
        return

    sender = msg.sender.lower()
    if sender.endswith('@athena.mit.edu'):
        sender = sender.split('@')[0]
    cls = msg.cls.lower()
    instance = msg.instance.lower()
    body = msg.fields[-1]

    link = 'https://zephyrplus.mit.edu/class/%s/instance/%s' % (cls, instance)

    payload = {
        'attachments': [
            {
                'fallback': body,
                'pretext': '<%s|-c %s -i %s>' % (link, cls, instance),
                'text': body
                }
            ],
        'username': sender,
        'channel': ZEPHYR_TO_SLACK[cls],
        }
    log('Send', payload)
    requests.post(SLACK_URL, json.dumps(payload))

def on_slack(msg):
    if msg.channel not in SLACK_TO_ZEPHYR:
        return
    if msg.sender == 'slackbot':
        return
    z = zephyr.ZNotice(cls=SLACK_TO_ZEPHYR[msg.channel],
                       sender=msg.sender,
                       message='via Slack\0%s' % msg.body.encode('utf-8'),
                       opcode='AUTO')
    log('Send', z.__dict__)
    z.send()

def listen_zephyr():
    subs = zephyr.Subscriptions()
    subs.add(('garywang-slack-test', '*', '*'))
    subs.add(('thetans', '*', '*'))
    while True:
        msg = zephyr.receive(True)
        if msg is not None:
            log('Receive', msg.__dict__)
            on_zephyr(msg)

def listen_slack():
    class SlackMessage(object):
        pass

    class SlackHandler(tornado.web.RequestHandler):
        def post(self):
            if self.get_body_argument('token') != SLACK_TOKEN:
                return
            log('Receive', self.request.body)
            msg = SlackMessage()
            msg.sender = self.get_body_argument('user_name')
            msg.channel = self.get_body_argument('channel_name')
            msg.body = self.get_body_argument('text')
            on_slack(msg)

    app = tornado.web.Application([
            (r'/', SlackHandler)
            ])

    app.listen(PORT)
    tornado.ioloop.IOLoop.current().start()

def main():
    zephyr.init()
    zephyrThread = threading.Thread(target=listen_zephyr)
    zephyrThread.daemon = True
    zephyrThread.start()
    slackThread = threading.Thread(target=listen_slack)
    slackThread.daemon = True
    slackThread.start()
    log('Slack <-> Zephyr started')
    while True:
        time.sleep(10000)

if __name__ == '__main__':
    main()
