# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import os
import json
import time
import sqlite3

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from infogen.gen import Gen, support_site_list

# 创建APP并获得config设置
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')

# 相关应用设置
CORS(app)  # 允许跨站请求
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])  # 请求频率限制

# Pt-Gen数据库地址
DATABASE = os.path.join(os.getcwd(), 'database', 'pt-gen.sqlite3')


# 数据库辅助方法
def db_exec(query: str, args=(), fetch_one: bool = False):
    with sqlite3.connect(DATABASE) as db:
        cur = db.execute(query, args)
        rv = [dict((cur.description[idx][0], value)
                   for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if fetch_one else rv


def get_key(key):
    ret = None
    if request.method == "POST":
        ret = request.form[key]
    elif request.method == "GET":
        ret = request.args.get(key)
    return ret


@app.route('/')
def home():
    return app.send_static_file('ptgen.html')


@app.route('/infogen')
@limiter.limit(["500/7days", "200 per day", "50 per hour"]) # 频率限制
def infogen():
    t0 = time.time()
    url = get_key("url")
    if url:
        gen = Gen(url)
        site = gen.site or ''
        sid = gen.sid
    else:
        site = get_key("site") or ''
        sid = get_key("sid")
        gen = Gen({'site': site.lower(), 'sid': sid})

    if site.lower() not in support_site_list:
        return jsonify({'error': 'Miss site key' + site.lower()})

    if sid is None:
        return jsonify({'error': 'Miss sid'})

    nocache = get_key('nocache')
    if nocache and app.config.get('PTGEN_ALLOW_NOCACHE'):
        db_exec('DELETE FROM `info_gen` WHERE `site` = ? AND `sid` = ?', (site, sid))

    # Check Database Cache
    d = db_exec('SELECT `data` FROM `info_gen` WHERE `site`= ? AND `sid` = ?', (site, sid), fetch_one=True)
    if d is None:
        data = gen.gen()
        if data['success']:
            db_exec('INSERT INTO `info_gen`(`site`, `sid`, `data`) VALUES (?,?,?)',
                    (site.lower(), sid, json.dumps(data, ensure_ascii=False, sort_keys=True)))
    else:
        data = json.loads(d['data'])

    data["cost"] = time.time() - t0
    data['site'] = site
    data['sid'] = sid
    return jsonify(data)


@app.cli.command('update_infogen')
def update_infogen():
    to_updates = db_exec("SELECT `site`,`sid` FROM `info_gen` "
                         "WHERE STRFTIME('%s',update_at) < STRFTIME('%s','now','-15 days')"  # 15天以上算过期失效
                         " ORDER BY RANDOM() LIMIT 5")  # 每次随机读5个
    for url in to_updates:
        site = url['site']
        sid = url['sid']
        gen = Gen({'site': site, 'sid': sid})
        data = gen.gen()
        if data['success']:
            db_exec("UPDATE `info_gen` SET `data` = ?, update_at=STRFTIME('%s','now') WHERE `site` = ? AND `sid` = ?",
                    (json.dumps(data, ensure_ascii=False, sort_keys=True), site, sid))
            print('Update {} {} Success'.format(site, sid))


if __name__ == '__main__':
    app.run()
