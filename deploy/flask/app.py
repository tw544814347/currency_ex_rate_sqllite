from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
import os
import threading
import time
from currency_crawler import CurrencyExchangeRateCrawler

app = Flask(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'currency_rates.db')

def get_latest_rates():
    """获取最新汇率数据"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT base_currency, target_currency, rate, timestamp, utc8_hour 
        FROM exchange_rates 
        WHERE (base_currency, target_currency, timestamp) IN (
            SELECT base_currency, target_currency, MAX(timestamp) 
            FROM exchange_rates 
            GROUP BY base_currency, target_currency
        )
        ORDER BY target_currency
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        rates = []
        for row in results:
            rates.append({
                'base': row[0],
                'target': row[1],
                'rate': row[2],
                'timestamp': row[3],
                'utc8_hour': row[4]
            })
        
        return rates
    except Exception as e:
        print(f"查询数据失败: {e}")
        return []

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/rates')
def api_rates():
    """API接口：获取最新汇率"""
    rates = get_latest_rates()
    return jsonify({
        'success': True,
        'data': rates,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/update')
def api_update():
    """API接口：手动触发更新"""
    try:
        crawler = CurrencyExchangeRateCrawler(db_path=DB_PATH)
        rates = crawler.fetch_exchange_rates()
        if rates:
            crawler.save_to_db(rates)
            crawler.close()
            return jsonify({
                'success': True,
                'message': f'成功更新{len(rates)}条汇率数据'
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取汇率数据失败'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

def update_rates_periodically():
    """后台线程：定期更新汇率"""
    while True:
        try:
            crawler = CurrencyExchangeRateCrawler(db_path=DB_PATH)
            rates = crawler.fetch_exchange_rates()
            if rates:
                crawler.save_to_db(rates)
            crawler.close()
            print(f"[{datetime.now()}] 汇率更新完成")
        except Exception as e:
            print(f"[{datetime.now()}] 更新失败: {e}")
        
        # 等待1小时
        time.sleep(3600)

# 启动后台更新线程
update_thread = threading.Thread(target=update_rates_periodically, daemon=True)
update_thread.start()

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 初始化数据库
    crawler = CurrencyExchangeRateCrawler(db_path=DB_PATH)
    crawler.close()
    
    # 运行Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000) 