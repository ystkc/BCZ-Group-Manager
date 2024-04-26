import os
import sys
import time
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self) -> None:
        '''配置类'''
        self.config_file = f'./config.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8840,
            'database_path': './data.db',
            'main_token': '',
            'output_file': './小班数据.xlsx',
            'daily_record': '59 23 * * *',
            'cache_second': 60,
        }
        self.initConfig()
        self.raw = self.read()
        self.host = self.raw.get('host', '')
        self.port = self.raw.get('port', '')
        self.database_path = self.raw.get('database_path', '')
        self.main_token = self.raw.get('main_token', '')
        self.output_file = self.raw.get('output_file', '')
        self.daily_record = self.raw.get('daily_record', '')
        self.cache_second = self.raw.get('cache_second', '')
        self.verify()

    def initConfig(self):
        '''初始化配置文件'''
        try:
            if path := os.path.dirname(self.config_file):
                os.makedirs(path, exist_ok=True)
            open(self.config_file, encoding='utf-8')
        except:
            json.dump(self.default_config_dict, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            logger.info('初次启动，已在当前执行目录生成配置文件，请修改配置后再次启动，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def read(self, key: str=None) -> list | dict | str | int | bool:
        '''获取指定配置'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            if key:
                json_data = json.load(open(self.config_file, encoding='utf-8')).get(key)
            return json_data
        except Exception as e:
            logger.error(f'配置文件读取异常: {e}，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def save(self, key: str, value: list | dict | str | int | bool) -> None:
        '''保存指定配置文件'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            json_data[key] = value
            json.dump(json_data, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    def verify(self):
        '''验证配置文件的完整性'''
        value = None
        if self.host == '':
            key = 'host'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.host = value
        if self.port == '':
            key = 'port'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.port = value
        if self.database_path == '':
            key = 'database_path'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.database_path = value
        if self.main_token == '':
            key = 'main_token'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.main_token = value
        if self.output_file == '':
            key = 'output_file'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.output_file = value
        if self.daily_record == '':
            key = 'daily_record'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.daily_record = value
        if self.cache_second == '':
            key = 'cache_second'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.cache_second = value

    def getInfo(self) -> dict:
        '''获取配置文件相关状态信息'''
        return {
            'main_token': self.main_token,
            'output_file': self.output_file,
            'daily_record': self.daily_record,
            'cache_second': self.cache_second,
        }