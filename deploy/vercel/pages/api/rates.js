import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

export default async function handler(req, res) {
  try {
    // 打开数据库连接
    const db = await open({
      filename: path.join(process.cwd(), 'data', 'currency_rates.db'),
      driver: sqlite3.Database
    });

    // 查询最新汇率
    const rates = await db.all(`
      SELECT base_currency, target_currency, rate, timestamp, utc8_hour 
      FROM exchange_rates 
      WHERE (base_currency, target_currency, timestamp) IN (
        SELECT base_currency, target_currency, MAX(timestamp) 
        FROM exchange_rates 
        GROUP BY base_currency, target_currency
      )
      ORDER BY target_currency
    `);

    await db.close();

    // 格式化响应数据
    const formattedRates = rates.map(rate => ({
      base: rate.base_currency,
      target: rate.target_currency,
      rate: rate.rate,
      timestamp: rate.timestamp,
      utc8Hour: rate.utc8_hour
    }));

    res.status(200).json({
      success: true,
      data: formattedRates,
      lastUpdate: rates[0]?.timestamp || null
    });
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
} 