import time
import logging
import threading
import traceback

logger = logging.getLogger(__name__)

class Schedule:
    def __init__(self, crontab: str, func: callable, *args, **kwargs) -> None:
        '''计划调用类'''
        self.crontab_expr = crontab
        self.exec = func
        if len(self.crontab_expr.split()) != 5:
            logger.warning('未正确设置schedule，故未启动计划')
            return
        self.cron = self.parse_crontab(self.crontab_expr)
        self.thread = threading.Thread(
            target=self.run,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        logger.info(f'启动计划 [{self.crontab_expr}]')
        self.thread.setName(f'Schedule: {crontab}')
        self.thread.start()

    def run(self, *args, **kwargs) -> None:
        '''执行函数'''
        while time.localtime().tm_sec != 0:
            time.sleep(1)
        while True:
            try:
                now = time.localtime()
                if (now.tm_min in self.cron[0] and
                        now.tm_hour in self.cron[1] and
                        now.tm_mday in self.cron[2] and
                        now.tm_mon in self.cron[3] and
                        now.tm_wday in self.cron[4]):
                    logger.info(f'执行计划[{self.crontab_expr}]')
                    threading.Thread(
                        target=self.exec,
                        args=args,
                        kwargs=kwargs,
                        daemon=True,
                    ).start()
                time.sleep(60)
            except:
                traceback.print_exc()

    def parse_crontab(self, crontab_expr: str) -> list:
        '''解析crontab'''
        fields = crontab_expr.split(' ')
        minute = self.parse_field(fields[0], 0, 59)
        hour = self.parse_field(fields[1], 0, 23)
        day_of_month = self.parse_field(fields[2], 1, 31)
        month = self.parse_field(fields[3], 1, 12)
        day_of_week = self.parse_field(fields[4], 0, 6)
        return (minute, hour, day_of_month, month, day_of_week)

    def parse_field(self, field: str, min_value: int, max_value: int):
        '''解析field'''
        if field == '*':
            return set(range(min_value, max_value + 1))
        values = set()
        for part in field.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))
        return values
