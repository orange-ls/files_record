"""
公共基类模块
提供：
  - PostgreSQL 连接管理
  - 事务上下文（失败自动回滚）
  - 进度回调接口
  - 查询结果格式化（Markdown 表格）
"""
import contextlib
import decimal
import logging
from typing import Callable, Optional

import psycopg2
import psycopg2.extras

from ._config import get_pg_config

_logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 连接管理
# ──────────────────────────────────────────────

def get_connection():
    """创建并返回 psycopg2 连接（autocommit=False）"""
    params = get_pg_config()
    conn = psycopg2.connect(**params)
    conn.autocommit = False
    return conn


@contextlib.contextmanager
def transaction(conn):
    """
    事务上下文管理器。
    正常退出时 commit，异常时 rollback 并重新抛出。

    用法：
        with transaction(conn):
            cur.execute(...)
    """
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        _logger.error('[xc_spare_parts] 事务回滚，原因：%s', e, exc_info=True)
        raise


# ──────────────────────────────────────────────
# 进度回调
# ──────────────────────────────────────────────

ProgressCallback = Optional[Callable[[int, int, str], None]]


def report(on_progress: ProgressCallback, step: int, total: int, message: str):
    """触发进度回调，同时打印日志"""
    _logger.info('[xc_spare_parts] [%d/%d] %s', step, total, message)
    if on_progress:
        on_progress(step, total, message)


# ──────────────────────────────────────────────
# 查询结果格式化
# ──────────────────────────────────────────────

def fetch_records(conn, sql: str, params=None, limit: int = 20, offset: int = 0) -> list:
    """
    执行 SQL 并返回 dict 列表。
    :param conn: psycopg2 连接
    :param sql: 查询 SQL（不含 LIMIT/OFFSET，由本函数追加）
    :param params: SQL 参数
    :param limit: 返回条数
    :param offset: 偏移量
    """
    paged_sql = f'{sql} LIMIT %s OFFSET %s'
    all_params = list(params or []) + [limit, offset]
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(paged_sql, all_params)
        rows = cur.fetchall()
    # 将 Decimal 转为 float/int，避免下游 JSON 序列化报错
    result = []
    for row in rows:
        d = {}
        for k, v in dict(row).items():
            if isinstance(v, decimal.Decimal):
                d[k] = int(v) if v == v.to_integral_value() else float(v)
            else:
                d[k] = v
        result.append(d)
    return result


def count_records(conn, sql: str, params=None) -> int:
    """统计总记录数，sql 为原始查询 SQL（不含 LIMIT/OFFSET）"""
    count_sql = f'SELECT COUNT(1) FROM ({sql}) _t'
    with conn.cursor() as cur:
        cur.execute(count_sql, params or [])
        return cur.fetchone()[0]


def to_markdown_table(records: list, fields: list, field_labels: dict,
                      total: int, limit: int, offset: int) -> str:
    """
    将查询结果格式化为 Markdown 表格字符串。
    :param records: dict 列表
    :param fields: 展示字段列表（按顺序）
    :param field_labels: {字段名: 中文名}
    :param total: 总记录数
    :param limit: 当前页大小
    :param offset: 当前偏移
    """
    if not records:
        return f'共 0 条，暂无数据。'

    start = offset + 1
    end = offset + len(records)
    summary = f'共 **{total}** 条，当前显示第 {start}-{end} 条\n\n'

    # 表头
    headers = [field_labels.get(f, f) for f in fields]
    header_row = '| ' + ' | '.join(headers) + ' |'
    sep_row = '| ' + ' | '.join(['---'] * len(fields)) + ' |'

    # 数据行（截断超长字段）
    data_rows = []
    for rec in records:
        cells = []
        for f in fields:
            val = rec.get(f, '')
            if val is None:
                val = ''
            val = str(val)
            # 超过 30 字符截断
            if len(val) > 30:
                val = val[:28] + '…'
            cells.append(val)
        data_rows.append('| ' + ' | '.join(cells) + ' |')

    return summary + '\n'.join([header_row, sep_row] + data_rows)


def build_result(success: bool, count: int = 0, message: str = '',
                 error: str = '') -> dict:
    """构造刷新操作的标准返回结果"""
    if success:
        return {'success': True, 'count': count, 'message': message or f'刷新成功，共写入 {count} 条'}
    return {'success': False, 'error': error, 'message': message or f'刷新失败，已回滚。原因：{error}'}
