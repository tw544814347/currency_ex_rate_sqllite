import requests
import sqlite3
import time
from datetime import datetime, timedelta, timezone
import logging
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("汇率爬虫")

# 创建数据库目录
os.makedirs('data', exist_ok=True)

class CurrencyExchangeRateCrawler:
    def __init__(self, db_path='data/currency_rates.db'):
        """初始化爬虫和数据库"""
        self.db_path = db_path
        self.conn = None
        self.base_currency = 'USD'  # 基准货币
        self.currencies = ['CNY', 'EUR', 'GBP', 'JPY', 'HKD', 'AUD', 'CAD', 'CHF', 'SGD', 'XAU']  # 要获取的货币，XAU为黄金
        # 使用免费的汇率API
        self.api_url = f"https://open.er-api.com/v6/latest/{self.base_currency}"
        
        # 初始化数据库
        self.init_db()
    
    def init_db(self):
        """初始化SQLite数据库和表结构"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # 创建汇率表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_currency TEXT NOT NULL,
                target_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                utc8_hour TEXT
            )
            ''')
            
            # 删除旧的非唯一索引（如果存在）
            cursor.execute('''
            DROP INDEX IF EXISTS idx_currency_timestamp
            ''')
            
            # 创建唯一索引，防止重复数据
            cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_currency_timestamp 
            ON exchange_rates (base_currency, target_currency, timestamp)
            ''')
            
            self.conn.commit()
            logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
            
    def get_last_update_time(self):
        """获取数据库中最后一条记录的时间"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT MAX(timestamp) FROM exchange_rates
            ''')
            last_update = cursor.fetchone()[0]
            if last_update:
                return datetime.fromisoformat(last_update)
            return None
        except Exception as e:
            logger.error(f"获取最后更新时间失败: {e}")
            return None
    
    def fetch_exchange_rates(self):
        """从API获取最新汇率数据"""
        try:
            logger.info(f"开始获取汇率数据，基准货币: {self.base_currency}")
            response = requests.get(self.api_url)
            response.raise_for_status()  # 如果请求失败则抛出异常
            
            data = response.json()
            
            if data.get('result') != 'success':
                logger.error(f"API返回错误: {data.get('error-type', '未知错误')}")
                return None
            
            rates = data.get('rates', {})
            timestamp = data.get('time_last_update_utc', datetime.now().isoformat())
            
            result = []
            for currency in self.currencies:
                if currency in rates:
                    result.append({
                        'base_currency': self.base_currency,
                        'target_currency': currency,
                        'rate': rates[currency],
                        'timestamp': timestamp
                    })
            
            logger.info(f"成功获取{len(result)}个货币的汇率数据")
            return result
        except requests.RequestException as e:
            logger.error(f"获取汇率数据失败: {e}")
            return None
    
    def save_to_db(self, rates_data):
        """将汇率数据保存到数据库（整点覆盖模式）"""
        if not rates_data:
            logger.warning("没有数据需要保存")
            return
        
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            updated_count = 0
            inserted_count = 0
            
            for rate_info in rates_data:
                # 计算UTC-8整点时间
                utc8_hour = self.calculate_utc8_hour(rate_info['timestamp'])
                
                # 先检查是否已存在相同时间戳的记录
                cursor.execute('''
                SELECT id FROM exchange_rates 
                WHERE base_currency = ? AND target_currency = ? AND timestamp = ?
                ''', (
                    rate_info['base_currency'],
                    rate_info['target_currency'],
                    rate_info['timestamp']
                ))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # 如果存在，则更新记录
                    cursor.execute('''
                    UPDATE exchange_rates 
                    SET rate = ?, created_at = ?, utc8_hour = ?
                    WHERE id = ?
                    ''', (
                        rate_info['rate'],
                        now,
                        utc8_hour,
                        existing_record[0]
                    ))
                    updated_count += 1
                else:
                    # 如果不存在，则插入新记录
                    cursor.execute('''
                    INSERT INTO exchange_rates 
                    (base_currency, target_currency, rate, timestamp, created_at, utc8_hour) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        rate_info['base_currency'],
                        rate_info['target_currency'],
                        rate_info['rate'],
                        rate_info['timestamp'],
                        now,
                        utc8_hour
                    ))
                    inserted_count += 1
            
            self.conn.commit()
            logger.info(f"数据保存完成：新增{inserted_count}条，更新{updated_count}条")
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")
            self.conn.rollback()
    
    def calculate_utc8_hour(self, timestamp_str):
        """计算UTC-8时区的整点时间"""
        try:
            # 解析时间戳
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
            utc8_hour = dt_utc8.replace(minute=0, second=0, microsecond=0)
            
            return utc8_hour.isoformat()
        except Exception as e:
            logger.error(f"计算UTC-8时间失败: {e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")
    
    def calculate_next_hour(self):
        """计算到下一个整点的秒数"""
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()
        return next_hour, wait_seconds
    
    def run(self, interval=3600):
        """运行爬虫，定期获取数据"""
        try:
            logger.info(f"爬虫开始运行，数据获取间隔: {interval}秒")
            while True:
                # 直接获取并保存数据，避免递归调用
                rates = self.fetch_exchange_rates()
                if rates:
                    self.save_to_db(rates)
                else:
                    logger.warning("本次获取数据失败，将在下一个周期重试")
                
                logger.info(f"休眠{interval}秒后继续获取数据...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("用户中断，爬虫停止运行")
        finally:
            self.close()
    
    def run_once(self):
        """只运行一次爬虫获取数据"""
        try:
            self.fill_missing_data()
            return self.fetch_exchange_rates()
        finally:
            self.close()
            
    def generate_hourly_timestamps(self, start_time, end_time=None):
        """生成从起始时间到结束时间的所有整点时间戳列表"""
        if end_time is None:
            end_time = datetime.now()
        
        # 将起始时间调整到下一个整点
        if start_time.minute != 0 or start_time.second != 0 or start_time.microsecond != 0:
            start_time = (start_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        # 将结束时间调整到最近的过去整点
        end_time = end_time.replace(minute=0, second=0, microsecond=0)
        
        # 如果开始时间晚于结束时间，返回空列表
        if start_time > end_time:
            return []
        
        # 生成所有小时整点的列表
        hourly_timestamps = []
        current = start_time
        while current <= end_time:
            hourly_timestamps.append(current)
            current += timedelta(hours=1)
        
        return hourly_timestamps
    
    def fill_missing_data(self):
        """获取从最后更新时间到当前时间的所有整点数据"""
        # 获取最后更新时间
        last_update = self.get_last_update_time()
        
        if last_update:
            logger.info(f"数据库最后更新时间: {last_update}")
        else:
            logger.info("数据库中没有历史数据，将获取当前时间的数据")
            # 直接获取数据，避免调用 run_once() 导致递归
            rates = self.fetch_exchange_rates()
            if rates:
                self.save_to_db(rates)
            return rates
        
        # 生成需要获取的整点时间列表
        hourly_timestamps = self.generate_hourly_timestamps(last_update)
        
        if not hourly_timestamps:
            logger.info("没有需要更新的数据")
            return None
        
        logger.info(f"需要获取的整点数据数量: {len(hourly_timestamps)}")
        for ts in hourly_timestamps:
            logger.info(f"  - {ts}")
        
        # 由于API限制，只能获取当前汇率，所以我们只获取最新的一个整点数据
        # 注意：如果付费使用API，可以修改此处代码获取历史数据
        logger.info("由于API限制，仅获取最新整点数据")
        rates = self.fetch_exchange_rates()
        if rates:
            self.save_to_db(rates)
        
        logger.info("数据更新完成")
        return rates


def query_latest_rates(db_path='data/currency_rates.db'):
    """查询最新汇率数据"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT base_currency, target_currency, rate, timestamp, utc8_hour 
        FROM exchange_rates 
        WHERE (base_currency, target_currency, timestamp) IN (
            SELECT base_currency, target_currency, MAX(timestamp) 
            FROM exchange_rates 
            GROUP BY base_currency, target_currency
        )
        ORDER BY base_currency, target_currency
        ''')
        
        results = cursor.fetchall()
        
        print("最新汇率数据:")
        print("=" * 80)
        print(f"{'基准货币':<10}{'目标货币':<10}{'汇率':<15}{'UTC时间':<30}{'PST时间(UTC-8)'}")
        print("-" * 80)
        for row in results:
            base, target, rate, timestamp, utc8_hour = row
            # 格式化UTC-8时间显示
            if utc8_hour:
                try:
                    dt = datetime.fromisoformat(utc8_hour)
                    utc8_display = dt.strftime("%Y-%m-%d %H:%M PST")
                except:
                    utc8_display = "N/A"
            else:
                utc8_display = "N/A"
            
            # 格式化UTC时间显示
            if '+0000' in timestamp:
                utc_display = timestamp.split(' +')[0]
            else:
                utc_display = timestamp
            
            if target == 'XAU':
                print(f"{base:<10}{target:<10}{rate:<15.6f}{utc_display:<30}{utc8_display} (黄金)")
            else:
                print(f"{base:<10}{target:<10}{rate:<15.6f}{utc_display:<30}{utc8_display}")
        
        conn.close()
    except Exception as e:
        print(f"查询数据失败: {e}")


def query_gold_price(db_path='data/currency_rates.db'):
    """查询最新黄金价格"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT base_currency, rate, timestamp 
        FROM exchange_rates 
        WHERE target_currency = 'XAU' 
        AND (base_currency, target_currency, timestamp) IN (
            SELECT base_currency, target_currency, MAX(timestamp) 
            FROM exchange_rates 
            WHERE target_currency = 'XAU'
            GROUP BY base_currency, target_currency
        )
        ''')
        
        result = cursor.fetchone()
        
        if result:
            base, rate, timestamp = result
            # 黄金价格通常是以盎司为单位
            print("\n最新黄金价格:")
            print("=" * 50)
            print(f"1盎司黄金 = {1/rate:.2f} {base}")
            print(f"更新时间: {timestamp}")
        else:
            print("未找到黄金价格数据，请先运行爬虫获取数据")
        
        conn.close()
    except Exception as e:
        print(f"查询黄金价格失败: {e}")


if __name__ == "__main__":
    # 示例用法
    print("国际货币汇率爬虫")
    print("1. 获取一次汇率数据")
    print("2. 持续获取汇率数据 (每小时)")
    print("3. 查看最新汇率数据")
    print("4. 获取缺失的整点数据")
    
    choice = input("请选择操作 (1/2/3/4): ")
    
    if choice == '1':
        crawler = CurrencyExchangeRateCrawler()
        crawler.run_once()
        print("数据获取完成")
    elif choice == '2':
        crawler = CurrencyExchangeRateCrawler()
        crawler.run()
    elif choice == '3':
        query_latest_rates()
    elif choice == '4':
        crawler = CurrencyExchangeRateCrawler()
        crawler.fill_missing_data()
    else:
        print("无效选择") 