# 实时汇率查询系统 💱

一个自动获取和存储国际货币汇率的Python爬虫系统，支持云端自动更新。

## 功能特点

- 🔄 自动获取9种主要货币对美元的实时汇率
- 📊 使用SQLite数据库存储历史数据
- ⏰ 支持定时自动更新（每小时）
- 🌍 包含UTC-8时区转换
- ☁️ 支持GitHub Actions云端自动运行
- 🚫 智能去重，避免重复数据

## 支持的货币

- 🇨🇳 CNY - 人民币
- 🇪🇺 EUR - 欧元
- 🇬🇧 GBP - 英镑
- 🇯🇵 JPY - 日元
- 🇭🇰 HKD - 港币
- 🇦🇺 AUD - 澳元
- 🇨🇦 CAD - 加元
- 🇨🇭 CHF - 瑞士法郎
- 🇸🇬 SGD - 新加坡元
- 🏆 XAU - 黄金(盎司)

## 快速开始

### 本地运行

1. 克隆仓库：
```bash
git clone https://github.com/YOUR_USERNAME/currency-exchange-rates.git
cd currency-exchange-rates/currency_ex_rate_sqllite
```

2. 安装依赖：
```bash
pip install requests
```

3. 运行爬虫：
```bash
python currency_crawler.py
```

选择操作：
- 1: 获取一次汇率数据
- 2: 持续获取汇率数据（每小时）
- 3: 查看最新汇率数据
- 4: 获取缺失的整点数据

### 云端自动运行

本项目已配置GitHub Actions，会自动：
- 每小时获取一次最新汇率
- 将数据保存到SQLite数据库
- 自动提交更新到GitHub

详细部署步骤请查看 [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md)

## 项目结构

```
currency_ex_rate_sqllite/
├── currency_crawler.py      # 主爬虫程序
├── data/
│   └── currency_rates.db   # SQLite数据库文件
├── clean_duplicates.py     # 数据清理工具
├── add_utc8_column.py      # 数据库迁移脚本
├── test_timezone.py        # 时区测试脚本
├── deploy/                 # 部署相关文件
│   ├── vercel/            # Vercel部署配置
│   └── flask/             # Flask应用
├── .github/
│   └── workflows/
│       └── update-rates.yml # GitHub Actions配置
└── README.md              # 本文件
```

## 数据库结构

`exchange_rates` 表：
- `id`: 主键
- `base_currency`: 基准货币（USD）
- `target_currency`: 目标货币
- `rate`: 汇率
- `timestamp`: UTC时间戳
- `created_at`: 记录创建时间
- `utc8_hour`: PST时间（UTC-8）

## API数据源

使用免费的汇率API：https://open.er-api.com/

## 部署选项

1. **GitHub Actions**（推荐）
   - 完全免费
   - 自动运行
   - 数据存储在Git仓库

2. **Vercel**
   - Next.js + React前端
   - Serverless API

3. **Flask + Render**
   - 传统Web应用
   - 包含Web界面

## 常见问题

### Q: 如何修改更新频率？
A: 编辑 `.github/workflows/update-rates.yml` 中的 cron 表达式

### Q: 如何添加新的货币？
A: 修改 `currency_crawler.py` 中的 `self.currencies` 列表

### Q: 数据库太大怎么办？
A: 运行 `clean_duplicates.py` 清理重复数据

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 作者

Wei Tao

---

⭐ 如果这个项目对您有帮助，请给个Star！ 