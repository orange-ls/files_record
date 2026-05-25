"""
配置读取模块
从 config.ini 读取数据库及外部系统连接信息
"""
import configparser
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')

_config = None


def get_config() -> configparser.ConfigParser:
    """获取配置对象（单例）"""
    global _config
    if _config is None:
        if not os.path.exists(_CONFIG_PATH):
            raise FileNotFoundError(
                f'配置文件不存在：{_CONFIG_PATH}\n'
                '请参考 data_skill.md 中的"配置文件说明"创建 config.ini'
            )
        _config = configparser.ConfigParser()
        _config.read(_CONFIG_PATH, encoding='utf-8')
    return _config


def get_pg_config() -> dict:
    """获取 PostgreSQL 连接参数"""
    cfg = get_config()['postgresql']
    return {
        'host': cfg['host'],
        'port': int(cfg.get('port', 5432)),
        'dbname': cfg['dbname'],
        'user': cfg['user'],
        'password': cfg['password'],
    }


def get_oracle_conn_str() -> str:
    """获取 Oracle 连接字符串"""
    return get_config()['oracle']['conn_str']


def get_wms_config() -> dict:
    """获取 WMS 接口配置"""
    cfg = get_config()['wms']
    return {
        'base_url': cfg['base_url'],
        'app_key': cfg['app_key'],
        'app_secret': cfg['app_secret'],
        'sub_app_key': cfg['sub_app_key'],
    }


def get_bcm_config() -> dict:
    """获取 BCM 数据库连接参数"""
    cfg = get_config()['bcm']
    return {
        'host': cfg['host'],
        'port': int(cfg.get('port', 5432)),
        'dbname': cfg['dbname'],
        'user': cfg['user'],
        'password': cfg['password'],
    }


def get_wms_k3_config() -> dict:
    """获取 WMS K3 BA 数据库连接参数（工厂物料清单使用）"""
    cfg = get_config()['wms_k3_ba']
    return {
        'host': cfg['host'],
        'port': int(cfg.get('port', 3306)),
        'dbname': cfg['dbname'],
        'user': cfg['user'],
        'password': cfg['password'],
    }
