import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

DB_PATH = 'data/currency_rates.db'

def check_db_exists():
    """检查数据库文件是否存在"""
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件 {DB_PATH} 不存在")
        print("请先运行 currency_crawler.py 获取数据")
        return False
    return True

def get_all_currencies():
    """获取数据库中所有可用的货币代码"""
    if not check_db_exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有基准货币
    cursor.execute("SELECT DISTINCT base_currency FROM exchange_rates")
    base_currencies = [row[0] for row in cursor.fetchall()]
    
    # 获取所有目标货币
    cursor.execute("SELECT DISTINCT target_currency FROM exchange_rates")
    target_currencies = [row[0] for row in cursor.fetchall()]
    
    # 合并并去重
    all_currencies = list(set(base_currencies + target_currencies))
    
    conn.close()
    return sorted(all_currencies)

def get_latest_rates(base='USD'):
    """获取指定基准货币的最新汇率"""
    if not check_db_exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    query = f'''
    SELECT base_currency, target_currency, rate, timestamp 
    FROM exchange_rates 
    WHERE base_currency = ? AND (base_currency, target_currency, timestamp) IN (
        SELECT base_currency, target_currency, MAX(timestamp) 
        FROM exchange_rates 
        WHERE base_currency = ?
        GROUP BY base_currency, target_currency
    )
    ORDER BY target_currency
    '''
    
    df = pd.read_sql_query(query, conn, params=(base, base))
    conn.close()
    
    if df.empty:
        print(f"未找到基准货币 {base} 的汇率数据")
        return None
    
    return df

def get_historical_rates(base='USD', target='CNY', days=30):
    """获取指定货币对的历史汇率数据"""
    if not check_db_exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    # 计算时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = '''
    SELECT base_currency, target_currency, rate, timestamp 
    FROM exchange_rates 
    WHERE base_currency = ? AND target_currency = ? 
    AND datetime(timestamp) >= datetime(?)
    ORDER BY timestamp
    '''
    
    df = pd.read_sql_query(query, conn, params=(base, target, start_date.isoformat()))
    conn.close()
    
    if df.empty:
        print(f"未找到货币对 {base}/{target} 的历史数据")
        return None
    
    # 转换时间戳并设置为索引
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    return df

def plot_rate_trend(base='USD', target='CNY', days=30):
    """绘制指定货币对的汇率走势图"""
    df = get_historical_rates(base, target, days)
    
    if df is None or df.empty:
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['rate'])
    plt.title(f'{base}/{target} 汇率走势 (过去{days}天)')
    plt.xlabel('日期')
    plt.ylabel('汇率')
    plt.grid(True)
    plt.tight_layout()
    
    # 创建图表目录
    os.makedirs('charts', exist_ok=True)
    plt.savefig(f'charts/{base}_{target}_{days}days.png')
    plt.close()
    
    print(f"已保存走势图到 charts/{base}_{target}_{days}days.png")

def display_menu():
    """显示主菜单"""
    print("\n===== 汇率数据查询工具 =====")
    print("1. 查看最新汇率数据")
    print("2. 查看历史汇率数据")
    print("3. 绘制汇率走势图")
    print("4. 查看所有可用货币")
    print("0. 退出程序")
    
    return input("\n请选择操作 (0-4): ")

def main():
    while True:
        choice = display_menu()
        
        if choice == '0':
            print("程序已退出")
            break
            
        elif choice == '1':
            available_currencies = get_all_currencies()
            if not available_currencies:
                continue
                
            print(f"可用的基准货币: {', '.join(available_currencies)}")
            base = input("请输入基准货币代码 (默认: USD): ").upper() or 'USD'
            
            df = get_latest_rates(base)
            if df is not None:
                print("\n最新汇率数据:")
                print("=" * 60)
                print(df.to_string(index=False))
        
        elif choice == '2':
            available_currencies = get_all_currencies()
            if not available_currencies:
                continue
                
            print(f"可用的货币代码: {', '.join(available_currencies)}")
            base = input("请输入基准货币代码 (默认: USD): ").upper() or 'USD'
            target = input("请输入目标货币代码 (默认: CNY): ").upper() or 'CNY'
            days_str = input("请输入查询天数 (默认: 30): ") or '30'
            
            try:
                days = int(days_str)
                df = get_historical_rates(base, target, days)
                if df is not None:
                    print(f"\n{base}/{target} 历史汇率数据 (过去{days}天):")
                    print("=" * 60)
                    print(df.to_string())
            except ValueError:
                print("错误：请输入有效的天数")
        
        elif choice == '3':
            available_currencies = get_all_currencies()
            if not available_currencies:
                continue
                
            print(f"可用的货币代码: {', '.join(available_currencies)}")
            base = input("请输入基准货币代码 (默认: USD): ").upper() or 'USD'
            target = input("请输入目标货币代码 (默认: CNY): ").upper() or 'CNY'
            days_str = input("请输入图表显示天数 (默认: 30): ") or '30'
            
            try:
                days = int(days_str)
                plot_rate_trend(base, target, days)
            except ValueError:
                print("错误：请输入有效的天数")
        
        elif choice == '4':
            currencies = get_all_currencies()
            if currencies:
                print("\n可用的货币代码:")
                print(", ".join(currencies))
        
        else:
            print("无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    # 检查是否安装了必要的依赖
    try:
        import pandas
        import matplotlib
    except ImportError:
        print("错误：缺少必要的依赖。")
        print("请运行以下命令安装依赖：")
        print("pip install pandas matplotlib")
        exit(1)
        
    main() 