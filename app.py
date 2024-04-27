import sys
import time
import logging

from flask import Flask, Response, render_template, send_file, jsonify, redirect, request
from werkzeug.serving import WSGIRequestHandler, _log

from src.bcz import BCZ, recordInfo, refreshTempMemberTable, analyseWeekInfo, getWeekOption
from src.config import Config
from src.sqlite import SQLite
from src.xlsx import Xlsx
from src.schedule import Schedule

# if '--debug' in sys.argv or (hasattr(sys, 'gettrace') and sys.gettrace() is not None):
if '--debug' in sys.argv:
    level = logging.DEBUG
else:
    level = logging.INFO

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)

WSGIRequestHandler.address_string = lambda self: self.headers.get('x-real-ip', self.client_address[0])
class MyRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        _log(type, f'{self.address_string()} {message % args}\n')


app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False

config = Config()
bcz = BCZ(config)
xlsx = Xlsx(config)
sqlite = SQLite(config)
processing = False

if not config.main_token:
    print('未配置授权令牌，请在[config.json]文件中填入正确main_token后重启，程序会在5秒后自动退出')
    time.sleep(5)
    sys.exit(0)

@app.route('/')
def index():
    return redirect('group')

@app.route('/group', methods=['GET'])
def group():
    return render_template('group.html')

@app.route('/group/<id>', methods=['GET'])
def details(id=None):
    return render_template('details.html')

@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')

@app.route('/data', methods=['GET'])
def data():
    return render_template('data.html')

@app.route('/setting', methods=['GET'])
def setting():
    return render_template('setting.html')

@app.route('/download', methods=['POST'])
def download():
    global processing
    if processing:
        return restful(403, '有正在处理的下载，请稍后再试 (ᗜ ˰ ᗜ)"')
    processing = True
    try:
        result = sqlite.queryMemberTable(request.json)
        xlsx = Xlsx(config)
        xlsx.write('用户信息', result[0])
        xlsx.save()
    except Exception as e:
        return restful(500, f'下载数据时发生错误: {e}')
    finally:
        processing = False
    return send_file(config.output_file)

@app.route('/get_data_info', methods=['GET'])
def get_data_info():
    info = bcz.getInfo()
    info.update(sqlite.getInfo())
    return restful(200, '', info)

@app.route('/get_user_group', methods=['GET'])
def get_user_group():
    user_id = request.args.get('id')
    group_list = bcz.getUserGroupInfo(user_id)
    if group_list:
        return restful(200, '', group_list)
    else:
        return restful(404, '未查询到该用户的小班Σ(っ °Д °;)っ')

@app.route('/observe_group', methods=['GET', 'POST'])
def observe_group():
    if request.method == 'GET':
        '''获取关注小班列表'''
        group_id = request.args.get('id', '')
        try:
            if group_id:
                full_info = True
            else:
                full_info = False
            group_list = sqlite.queryObserveGroupInfo(group_id)
            group_list = bcz.updateGroupInfo(group_list, full_info)
            sqlite.updateObserveGroupInfo(group_list)
            for group in group_list:
                group['auth_token'] = len(group['auth_token']) * '*'
            if not group_list:
                return restful(404, '未查询到该小班Σ(っ °Д °;)っ')
            return restful(200, '', group_list)
        except Exception as e:
            return restful(400, str(e))

    elif request.method == 'POST':
        '''添加或修改关注小班列表'''
        group_list = sqlite.queryObserveGroupInfo()
        if 'share_key' in request.json and len(request.json) == 1:
            share_key = request.json.get('share_key')
            if share_key in [group_info['share_key'] for group_info in group_list]:
                return restful(403, '该小班已存在ヾ(≧▽≦*)o')
            group_info = bcz.getGroupInfo(share_key)
            sqlite.addObserveGroupInfo([group_info])
            msg = '成功添加新的关注小班ヾ(≧▽≦*)o'
        elif 'id' in request.json:
            group_id = request.json.get('id')
            if int(group_id) not in [group_info['id'] for group_info in group_list]:
                return restful(403, '该小班不存在Σ(っ °Д °;)っ')
            group_info = sqlite.queryObserveGroupInfo(group_id=group_id)[0]
            group_info.update(request.json)
            if group_info['late_daka_time'] == '00:00':
                group_info['late_daka_time'] = ''
            sqlite.updateObserveGroupInfo([group_info])
            msg = '操作成功! ヾ(≧▽≦*)o'
        else:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        return restful(200, msg)

@app.route('/query_group_details', methods=['POST'])
def query_group_details():
    '''获取关注小班列表'''
    group_id = request.json.get('id', '')
    week = request.json.get('week', '')
    if not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        group_list = refreshTempMemberTable(bcz, sqlite, group_id)
        for group in group_list:
            group['auth_token'] = len(group['auth_token']) * '*'
        analyseWeekInfo(group_list, sqlite, week)
        if not group_list:
            return restful(404, '未查询到该小班Σ(っ °Д °;)っ')
        return restful(200, '', group_list)
    except Exception as e:
        return restful(400, str(e))

@app.route('/get_group_details_option', methods=['GET'])
def get_group_details_option():
    option = {'week': getWeekOption()}
    return restful(200, '', option)

@app.route('/get_search_option', methods=['GET'])
def get_search_option():
    option = sqlite.getSearchOption()
    return restful(200, '', option)

@app.route('/query_member_table', methods=['POST'])
def query_member_table():
    try:
        refreshTempMemberTable(bcz, sqlite)
        result = sqlite.queryMemberTable(request.json, header=True, union_temp=True)
        return restful(200, '', result)
    except Exception as e:
        return restful(500, f'{e}')

@app.route('/search_group', methods=['GET'])
def search_group():
    share_key = request.args.get('share_key')
    user_id = request.args.get('uid')
    try:
        if share_key:
            group_info = bcz.getGroupInfo(share_key)
            result = {group_info['id']: group_info}
        elif user_id:
            result = bcz.getUserGroupInfo(user_id)
        else:
            return restful(400, '请求参数错误Σ(っ °Д °;)っ')
        if len(result):
            return restful(200, '', result)
        return restful(404, '未搜索到符合条件的小班 (ᗜ ˰ ᗜ)"')
    except Exception as e:
        return restful(400, f'{e}')

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if request.method == 'GET':
        '''获取配置文件'''
        info = config.getInfo()
        info['main_token'] = len(info['main_token']) * '*'
        return restful(200, '', info)
    elif request.method == 'POST':
        '''修改配置文件'''
        try:
            config.modify(request.json)
        except Exception as e:
            return restful(400, str(e))
        return restful(200, '配置修改成功! ヾ(≧▽≦*)o')


def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return jsonify({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }), code

if __name__ == '__main__':
    logging.info('BCZ-Group-Manger 启动中...')
    if config.daily_record:
        Schedule(config.daily_record, lambda: recordInfo(bcz, sqlite))
    # app.run(config.host, config.port, debug=True)
    app.run(config.host, config.port, debug=True, request_handler=MyRequestHandler)