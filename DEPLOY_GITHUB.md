# GitHub Actions 部署指南

本指南将帮助您将汇率爬虫系统部署到 GitHub，实现代码云端存储和自动更新。

## 步骤 1：创建 GitHub 仓库

1. 登录您的 GitHub 账号（如果没有，请在 https://github.com 注册）
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - Repository name: `currency-exchange-rates`
   - Description: 实时汇率查询系统
   - 选择 Public（公开）或 Private（私有）
   - 勾选 "Add a README file"
4. 点击 "Create repository"

## 步骤 2：上传代码到 GitHub

### 方法 A：使用 Git 命令行

```bash
# 1. 进入项目目录
cd /Users/wei.tao/Desktop/Cursor\ FIles/currency_ex_rate_sqllite

# 2. 初始化 Git 仓库
git init

# 3. 添加所有文件
git add .

# 4. 创建首次提交
git commit -m "Initial commit: 汇率爬虫系统"

# 5. 添加远程仓库（替换 YOUR_USERNAME 为您的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/currency-exchange-rates.git

# 6. 推送到 GitHub
git push -u origin main
```

### 方法 B：使用 GitHub Desktop（图形界面）

1. 下载并安装 GitHub Desktop: https://desktop.github.com/
2. 登录您的 GitHub 账号
3. 点击 "Add" → "Add Existing Repository"
4. 选择项目文件夹
5. 点击 "Publish repository"

## 步骤 3：配置 GitHub Actions

1. 在您的仓库中，确保已经创建了 `.github/workflows/update-rates.yml` 文件
2. 该文件内容应该如下：

```yaml
name: Update Exchange Rates

on:
  schedule:
    # 每小时运行一次 (UTC时间)
    - cron: '0 * * * *'
  workflow_dispatch: # 允许手动触发

jobs:
  update-rates:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v3
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests
    
    - name: Run currency crawler
      run: |
        cd currency_ex_rate_sqllite
        python -c "from currency_crawler import CurrencyExchangeRateCrawler; crawler = CurrencyExchangeRateCrawler(); crawler.run_once()"
    
    - name: Commit and push if changed
      run: |
        git config --global user.email "github-actions[bot]@users.noreply.github.com"
        git config --global user.name "github-actions[bot]"
        git add currency_ex_rate_sqllite/data/currency_rates.db
        git diff --quiet && git diff --staged --quiet || (git commit -m "Update exchange rates [skip ci]" && git push)
```

## 步骤 4：启用 GitHub Actions

1. 在您的仓库页面，点击 "Actions" 标签
2. 如果看到提示，点击 "I understand my workflows, go ahead and enable them"
3. 找到 "Update Exchange Rates" 工作流
4. 点击 "Run workflow" → "Run workflow" 手动触发一次测试

## 步骤 5：创建 GitHub Pages 展示页面（可选）

创建一个简单的网页来展示汇率数据：

1. 创建 `docs/index.html` 文件：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>实时汇率查询</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
    </style>
</head>
<body>
    <h1>实时汇率查询系统</h1>
    <p>数据每小时自动更新</p>
    <div id="rates">加载中...</div>
    
    <script>
        // 这里可以添加 JavaScript 代码来读取和显示数据
        document.getElementById('rates').innerHTML = '<p>请查看仓库中的 data/currency_rates.db 文件获取最新数据</p>';
    </script>
</body>
</html>
```

2. 在仓库设置中启用 GitHub Pages：
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: main, /docs
   - 点击 Save

## 步骤 6：监控和维护

1. **查看运行状态**：
   - 在 Actions 标签页查看每次运行的结果
   - 绿色勾号表示成功，红色叉号表示失败

2. **查看数据更新**：
   - 每次成功运行后，`data/currency_rates.db` 文件会自动更新
   - 可以在仓库的提交历史中看到每次更新

3. **调整更新频率**：
   - 修改 `.github/workflows/update-rates.yml` 中的 cron 表达式
   - 例如：`'0 */2 * * *'` 表示每2小时运行一次

## 常见问题

### Q: Actions 运行失败怎么办？
A: 点击失败的运行记录查看详细日志，常见问题包括：
- Python 包安装失败：检查 requirements.txt
- 路径错误：确保文件路径正确
- API 限制：检查是否超过 API 调用限制

### Q: 如何手动触发更新？
A: 在 Actions 页面，选择 "Update Exchange Rates" 工作流，点击 "Run workflow"

### Q: 数据库文件太大怎么办？
A: 可以定期清理旧数据，或使用 Git LFS 存储大文件

## 优势总结

1. **完全免费**：使用 GitHub 免费服务
2. **自动化运行**：无需本地电脑，云端自动执行
3. **数据持久化**：所有数据都保存在 Git 仓库中
4. **版本控制**：可以查看历史数据变化
5. **易于分享**：可以将仓库设为公开，与他人分享

## 下一步

1. 可以创建一个简单的 API 服务来读取数据库数据
2. 使用 GitHub Pages 创建一个更美观的展示页面
3. 添加更多货币对或其他金融数据 