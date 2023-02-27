"""
@Author         : Ailitonia
@Date           : 2023/2/19 21:31
@FileName       : emergency_shutdown
@Project        : Server UPS Support
@Description    : Shutdown emergency when environment power off (for Linux), need root to run.
@GitHub         : https://github.com/Ailitonia
@Software       : PyCharm 
"""

import logging
import os
import re
import subprocess
import sys
import time


__HOST: str = '192.168.200.32'
__FAILED_COUNT: int = 0
__FAILED_THRESHOLD: int = 6

# 日志配置
logger = logging.getLogger('Shutdown Emergency')
logger.setLevel(logging.INFO)

# 设置命令行输出日志
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(logging.Formatter('[%(asctime)s %(name)s] %(levelname)s: %(message)s'))
logger.addHandler(default_handler)


def ping_test(target_host: str) -> bool:
    """ping 测试环境电源, 返回 is_power_on"""
    ping = subprocess.Popen(
        ['ping', '-c', '3', '-w', '8', target_host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        outs, errs = ping.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        ping.kill()
        outs, errs = ping.communicate()

    is_power_on: bool = True
    try:
        matcher = re.compile(
            '^(\d) packets transmitted, (\d) received,( \+(\d+?) errors?,)? (\d+?)% packet loss, time \d+?ms$',
            flags=re.MULTILINE
        )
        matched = matcher.search(outs.decode())
        if matched:
            logger.info(f'PING {target_host!r} completed: {matched.string[matched.start():matched.end()]}')
            _, _, _, errors, loss = matched.groups()
            if (errors and int(errors) > 1) or int(loss) > 50:
                is_power_on = False
                logger.warning(f'PING {target_host!r} failed with {errors} errors and {loss}% packet loss')
    except Exception as e:
        is_power_on = False
        logger.error(f'PING {target_host!r} result matched failed, stdout: {outs.decode()!r}, {e}')
    return is_power_on


def monitor_main(target_host: str, *, detect_delay: int = 30):
    """通过 ping 测试判断环境是否停电, 并在停电时关闭主机电源"""
    global __FAILED_COUNT
    while True:
        try:
            ping_test_result = ping_test(target_host=target_host)
            if not ping_test_result:
                logger.warning(f'Environment power maybe off, checking again after {detect_delay} second')
                __FAILED_COUNT += 1
            else:
                __FAILED_COUNT = 0
        except Exception as e:
            logger.error(f'PING test failed with exception: {e}, checking again after {detect_delay} second')
            __FAILED_COUNT += 1

        if __FAILED_COUNT > 1:
            logger.warning(f'PING test failed count is now {__FAILED_COUNT}')

        if __FAILED_COUNT > __FAILED_THRESHOLD:
            logger.critical(f'Environment power off, system will shutdown immediately')
            os.system('shutdown -P +1 "Server is going down for environment power off. Please save your work ASAP."')
            break
        time.sleep(detect_delay)


if __name__ == '__main__':
    logger.info('Shutdown Emergency - Environment power PING test started')
    monitor_main(target_host=__HOST)
