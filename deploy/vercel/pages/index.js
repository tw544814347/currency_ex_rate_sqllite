import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchRates();
    // 每分钟刷新一次
    const interval = setInterval(fetchRates, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchRates = async () => {
    try {
      const response = await fetch('/api/rates');
      const data = await response.json();
      
      if (data.success) {
        setRates(data.data);
        setLastUpdate(data.lastUpdate);
        setError(null);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN');
    } catch {
      return timestamp;
    }
  };

  const formatUTC8Time = (utc8Hour) => {
    if (!utc8Hour) return 'N/A';
    try {
      const date = new Date(utc8Hour);
      return date.toLocaleString('zh-CN', { 
        timeZone: 'America/Los_Angeles',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return utc8Hour;
    }
  };

  const currencyNames = {
    'CNY': '人民币',
    'EUR': '欧元',
    'GBP': '英镑',
    'JPY': '日元',
    'HKD': '港币',
    'AUD': '澳元',
    'CAD': '加元',
    'CHF': '瑞士法郎',
    'SGD': '新加坡元',
    'XAU': '黄金(盎司)'
  };

  return (
    <div className="container">
      <Head>
        <title>实时汇率查询系统</title>
        <meta name="description" content="实时查询国际货币汇率" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <h1>💱 实时汇率查询系统</h1>
        
        {loading && <div className="loading">加载中...</div>}
        
        {error && <div className="error">错误: {error}</div>}
        
        {!loading && !error && (
          <>
            <div className="update-info">
              最后更新: {formatTime(lastUpdate)}
            </div>
            
            <table className="rates-table">
              <thead>
                <tr>
                  <th>货币</th>
                  <th>代码</th>
                  <th>汇率</th>
                  <th>1美元兑换</th>
                  <th>PST时间</th>
                </tr>
              </thead>
              <tbody>
                {rates.map((rate) => (
                  <tr key={`${rate.base}-${rate.target}`}>
                    <td>{currencyNames[rate.target] || rate.target}</td>
                    <td>{rate.target}</td>
                    <td>{rate.rate.toFixed(4)}</td>
                    <td>{rate.rate.toFixed(2)} {rate.target}</td>
                    <td>{formatUTC8Time(rate.utc8Hour)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <div className="refresh-button">
              <button onClick={fetchRates}>刷新数据</button>
            </div>
          </>
        )}
      </main>

      <style jsx>{`
        .container {
          min-height: 100vh;
          padding: 0 0.5rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          background-color: #f5f5f5;
        }

        main {
          padding: 2rem 0;
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          background-color: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          max-width: 900px;
          width: 100%;
          margin: 20px;
        }

        h1 {
          margin: 0 0 2rem;
          font-size: 2.5rem;
          color: #333;
        }

        .loading, .error {
          padding: 20px;
          text-align: center;
          font-size: 1.2rem;
        }

        .error {
          color: #e74c3c;
        }

        .update-info {
          margin-bottom: 20px;
          color: #666;
          font-size: 0.9rem;
        }

        .rates-table {
          width: 100%;
          border-collapse: collapse;
          margin: 20px 0;
        }

        .rates-table th,
        .rates-table td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #ddd;
        }

        .rates-table th {
          background-color: #4CAF50;
          color: white;
          font-weight: bold;
        }

        .rates-table tr:hover {
          background-color: #f5f5f5;
        }

        .refresh-button {
          margin-top: 20px;
        }

        .refresh-button button {
          background-color: #4CAF50;
          color: white;
          border: none;
          padding: 10px 20px;
          font-size: 16px;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.3s;
        }

        .refresh-button button:hover {
          background-color: #45a049;
        }

        @media (max-width: 600px) {
          h1 {
            font-size: 1.8rem;
          }
          
          .rates-table {
            font-size: 0.9rem;
          }
          
          .rates-table th,
          .rates-table td {
            padding: 8px;
          }
        }
      `}</style>
    </div>
  );
} 