# 贡献指南

感谢您对Smart Energy Platform项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告问题

1. 使用GitHub Issues报告bug
2. 清晰描述问题和复现步骤
3. 提供相关的日志或截图

### 提交代码

1. Fork项目仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建Pull Request

### 开发规范

#### 代码风格

- Python：遵循PEP 8，使用Black格式化
- TypeScript：使用ESLint + Prettier
- 提交信息：使用Conventional Commits格式

#### 测试要求

- 新功能需要添加单元测试
- 确保所有测试通过：`pytest tests/`
- 保持测试覆盖率不降低

#### 文档要求

- 更新README.md（如有必要）
- 为新API添加文档字符串
- 更新API文档注释

## 开发环境

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/smart-energy-platform.git
cd smart-energy-platform

# 启动基础服务
docker-compose -f docker-compose.dev.yml up -d

# 启动后端
cd data_service
pip install -r requirements.txt
uvicorn main:app --reload

# 启动前端
cd web_app
npm install
npm run dev
```

### 运行测试

```bash
# 单元测试
cd data_service
pytest tests/ -v

# 集成测试
./scripts/test_integration.sh
```

## Pull Request流程

1. 确保代码通过所有检查
2. 更新相关文档
3. 填写PR描述，说明改动内容
4. 等待代码审查
5. 合并到主分支

## 行为准则

- 尊重所有参与者
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

## 联系方式

如有任何问题，请通过以下方式联系我们：

- GitHub Issues
- Email: your-email@example.com

感谢您的贡献！🎉