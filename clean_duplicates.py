import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("数据清理")

def clean_duplicate_rates(db_path='data/currency_rates.db'):
    """清理数据库中的重复汇率数据"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 首先查看有多少重复数据
        cursor.execute('''
        SELECT base_currency, target_currency, timestamp, COUNT(*) as count
        FROM exchange_rates
        GROUP BY base_currency, target_currency, timestamp
        HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        logger.info(f"发现{len(duplicates)}组重复数据")
        
        # 删除重复数据，保留id最小的记录
        for base, target, timestamp, count in duplicates:
            logger.info(f"清理重复数据: {base}->{target} at {timestamp}, 重复{count}次")
            
            # 获取该组合的所有记录ID
            cursor.execute('''
            SELECT id FROM exchange_rates
            WHERE base_currency = ? AND target_currency = ? AND timestamp = ?
            ORDER BY id
            ''', (base, target, timestamp))
            
            ids = [row[0] for row in cursor.fetchall()]
            
            # 保留第一个ID，删除其余的
            if len(ids) > 1:
                ids_to_delete = ids[1:]
                cursor.execute(f'''
                DELETE FROM exchange_rates
                WHERE id IN ({','.join('?' * len(ids_to_delete))})
                ''', ids_to_delete)
        
        conn.commit()
        logger.info("重复数据清理完成")
        
        # 显示清理后的数据统计
        cursor.execute('SELECT COUNT(*) FROM exchange_rates')
        total_records = cursor.fetchone()[0]
        logger.info(f"数据库中现有{total_records}条记录")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"清理数据失败: {e}")
        raise

if __name__ == "__main__":
    clean_duplicate_rates() 