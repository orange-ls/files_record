"""
共享常量模块
集中管理多个 fetcher 共用的常量，避免重复定义。
"""
import re

# ──────────────────────────────────────────────
# 城市列表（来自 reservoir_area_stock.city_fields，排除武汉后用于备料计算）
# ──────────────────────────────────────────────
CITY_FIELDS = [
    '武汉', 'whbj', '北京', '福州', '上海', '西安', '成都', '厦门', '肇庆', '合肥',
    '南京', '广州', '阿克苏', '大连', '呼和浩特', '济南', '昆明', '重庆', '南宁', '宁波',
    '沈阳', '长春', '哈尔滨', '兰州', '石家庄', '太原', '天津', '乌鲁木齐', '西宁', '银川',
    '汕头', '深圳', '东莞', '烟台', '海口', '武汉项目', '待定', '佛山', '贵阳', '杭州',
    '郑州', '长沙', '龙岩', '青岛', '南昌', '廊坊',
]

# ──────────────────────────────────────────────
# XC02/XC16/XC17 库存地配置（鲲鹏日报中的特殊库存地）
# ──────────────────────────────────────────────
STOCK_ADDRESSES = [
    {'stock': 'MHMU', 'name': 'XC02'},
    {'stock': 'MHMU', 'name': 'XC16'},
    {'stock': 'MH48', 'name': 'XC17'},
]

# ──────────────────────────────────────────────
# 库存预警中文映射
# ──────────────────────────────────────────────
ALERT_MAP = {
    'adequate': '充足',
    'replenished': '补货',
    'urgently_replenished': '急需补货',
    'out_of_stock': '无库存',
}


# ──────────────────────────────────────────────
# 服务时效判断（多个 fetcher 共用）
# ──────────────────────────────────────────────
# 正则预编译，避免每次调用重新编译
_TIER1_RE = re.compile(r'(白金\+?|7\*24\*2H)')
_TIER2_RE = re.compile(r'(金牌\+?|7\*24\*4H)')
_TIER3_RE = re.compile(r'(标准\+?|7\*24\*ND|7\*24\*3CD|7\*24\*5CD)')


def get_service_level(config_desc: str, default: str = '基础保修') -> str:
    """
    根据服务描述判断服务时效等级。
    :param config_desc: 逗号分隔的服务描述字符串
    :param default: 无匹配时的默认值
    :return: '2H/4H' / 'ND' / default
    """
    if not config_desc:
        return default
    items = [s.strip() for s in config_desc.split(',') if s.strip()]
    # 白金/金牌 → 2H/4H
    if any(_TIER1_RE.search(i) for i in items) or any(_TIER2_RE.search(i) for i in items):
        return '2H/4H'
    # 标准 → ND
    if any(_TIER3_RE.search(i) for i in items):
        return 'ND'
    return default
