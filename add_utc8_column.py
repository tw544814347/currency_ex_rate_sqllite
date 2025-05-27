import sqlite3
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("数据库迁移")

def add_utc8_column(db_path='data/currency_rates.db'):
    """添加UTC-8整点时间列到数据库"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(exchange_rates)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'utc8_hour' in columns:
            logger.info("utc8_hour列已存在，无需添加")
            return
        
        # 添加新列
        logger.info("开始添加utc8_hour列...")
        cursor.execute('''
        ALTER TABLE exchange_rates 
        ADD COLUMN utc8_hour TEXT
        ''')
        
        # 更新现有记录的UTC-8时间
        logger.info("更新现有记录的UTC-8时间...")
        cursor.execute('''
        SELECT id, timestamp FROM exchange_rates
        ''')
        
        records = cursor.fetchall()
        for record_id, timestamp_str in records:
            # 解析时间戳
            try:
                # 处理不同格式的时间戳
                if '+0000' in timestamp_str:
                    # 格式如: "Tue, 27 May 2025 00:02:31 +0000"
                    dt = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %z")
                else:
                    # ISO格式
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # 转换为UTC-8
                utc8_tz = timezone(timedelta(hours=-8))
                dt_utc8 = dt.astimezone(utc8_tz)
                
                # 获取整点时间
                utc8_hour = dt_utc8.replace(minute=0, second=0, microsecond=0).isoformat()
                
                # 更新记录
                cursor.execute('''
                UPDATE exchange_rates 
                SET utc8_hour = ? 
                WHERE id = ?
                ''', (utc8_hour, record_id))
                
            except Exception as e:
                logger.error(f"处理记录ID {record_id} 时出错: {e}")
        
        conn.commit()
        logger.info("UTC-8时间列添加完成")
        
        # 显示更新后的表结构
        cursor.execute("PRAGMA table_info(exchange_rates)")
        columns_info = cursor.fetchall()
        logger.info("更新后的表结构:")
        for col in columns_info:
            logger.info(f"  {col[1]} - {col[2]}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"添加UTC-8列失败: {e}")
        raise

if __name__ == "__main__":
    add_utc8_column() 