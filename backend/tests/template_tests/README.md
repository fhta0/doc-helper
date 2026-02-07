# 模板测试套件

本目录包含文档格式模板的完整测试套件，用于验证模板提取和检测功能的准确性。

## 📁 目录结构

```
template_tests/
├── scripts/              # 测试脚本
│   ├── test_template_accuracy.py      # 格式规则测试
│   ├── test_template_with_ai.py       # 完整测试（格式+AI）
│   └── import_templates.py            # 模板导入脚本
├── documents/            # 测试文档
│   ├── format_tests/     # 格式测试文档（3个）
│   └── ai_tests/         # AI测试文档（3个）
├── reports/              # 测试报告
│   ├── TEST_SUMMARY.md                      # 快速总结
│   ├── COMPLETE_TEMPLATE_TEST_REPORT.md     # 完整测试报告
│   ├── TEMPLATE_ACCURACY_TEST_REPORT.md     # 格式测试报告
│   └── TEMPLATE_IMPORT_SUMMARY.md           # 模板导入报告
└── README.md             # 本文件
```

## 🚀 快速开始

### 运行格式测试

测试格式规则检测功能（不含AI）：

```bash
cd /mnt/d/code/doc-ai/backend
python tests/template_tests/scripts/test_template_accuracy.py
```

**测试内容**:
- 页边距检测
- 字体字号检测
- 段落格式检测
- 标题样式检测

**预期结果**: 100%通过

### 运行完整测试（推荐）

测试格式规则 + AI内容检测：

```bash
python tests/template_tests/scripts/test_template_with_ai.py
```

**测试内容**:
- 所有格式规则（同上）
- AI错别字检测
- AI交叉引用检测

**预期结果**: 100%通过（AI检测允许±1误差）

### 导入新模板

从.docx文件导入新的格式模板：

```bash
python tests/template_tests/scripts/import_templates.py
```

**功能**:
- 解析.docx文档格式
- 提取页面设置、标题样式、正文格式
- 保存为系统模板到数据库

## 📊 测试覆盖

### 格式检测测试

| 测试项 | 覆盖 | 准确率 |
|-------|------|--------|
| 页边距 | ✅ | 100% |
| 纸张大小 | ✅ | 100% |
| 字体字号 | ✅ | 100% |
| 行距 | ✅ | 100% |
| 首行缩进 | ✅ | 100% |
| 标题样式 | ✅ | 100% |

### AI检测测试

| 测试项 | 覆盖 | 准确率 |
|-------|------|--------|
| 同音字错误 | ✅ | 100% |
| 形近字错误 | ✅ | 100% |
| 英文拼写错误 | ✅ | 100% |
| 交叉引用检查 | ✅ | 95%+ |

## 📝 测试文档说明

### 格式测试文档 (format_tests/)

1. **正确_K3S建设方案.docx**
   - 完全符合K3S建设方案模板规范
   - 预期: 0个格式问题

2. **错误_K3S建设方案.docx**
   - 包含6种格式错误
   - 预期: 6个格式问题

3. **正确_K3S设计方案.docx**
   - 完全符合K3S设计方案模板规范
   - 预期: 0个格式问题

### AI测试文档 (ai_tests/)

1. **含错别字_K3S建设方案.docx**
   - 包含7种错别字（同音字、形近字、拼写错误等）
   - 预期: 7个AI检测问题

2. **含引用错误_K3S设计方案.docx**
   - 包含交叉引用错误
   - 预期: 13-14个AI检测问题

3. **完全正确_AI测试.docx**
   - 格式和内容都正确
   - 预期: 0-1个AI误报（可接受）

## 📖 测试报告说明

### TEST_SUMMARY.md
- 快速了解测试情况
- 包含关键统计数据
- **推荐首先阅读**

### COMPLETE_TEMPLATE_TEST_REPORT.md
- 最详细的测试报告
- 包含所有测试用例和结果
- 技术实现细节
- **最完整的参考文档**

### TEMPLATE_ACCURACY_TEST_REPORT.md
- 专注于格式检测测试
- 不包含AI检测内容

### TEMPLATE_IMPORT_SUMMARY.md
- 模板导入过程记录
- Bug修复说明

## 🔧 测试原理

### 调用的现有API

所有测试都调用系统现有的API和函数，不重复实现：

```python
# 1. 文档解析
from app.services.docx_parser import parse_document_safe
doc_data = parse_document_safe(file_path)

# 2. 规则生成
from app.services.rule_engine import config_to_rules
rules = config_to_rules(template.config_json)

# 3. 格式检测
from app.services.rule_engine import create_rule_engine
engine = create_rule_engine(rules)
result = engine.check_document_sync(doc_data)

# 4. AI检测
from app.services.ai_content_checker import create_ai_content_checker
ai_checker = create_ai_content_checker()
ai_results = await ai_checker.check_all(doc_data, ["spell_check", "cross_ref_check"])
```

### 测试方法

1. **生成测试文档** - 使用python-docx库创建各种测试场景
2. **执行检测** - 调用系统API进行检测
3. **验证结果** - 对比实际问题数与预期问题数
4. **生成报告** - 输出详细的测试结果

## 🎯 集成到CI/CD

### 作为常规测试的一部分

将模板测试添加到项目的测试流程中：

```bash
# 在CI/CD pipeline中
cd backend

# 运行所有测试
pytest                                    # 单元测试和集成测试
python tests/template_tests/scripts/test_template_accuracy.py  # 格式测试
python tests/template_tests/scripts/test_template_with_ai.py   # 完整测试
```

### 测试频率建议

- **每次修改模板相关代码后** - 必须运行
- **每周一次** - 常规回归测试
- **发布前** - 完整测试套件

## ⚙️ 环境要求

### 必需

- Python 3.8+
- 已安装依赖: `pip install -r requirements.txt`
- 数据库中已有模板（ID: 12, 13）

### AI测试额外要求

- 配置AI API密钥（DeepSeek）
- 在 `.env` 中设置:
  ```
  AI_BASE_URL=https://api.deepseek.com
  AI_API_KEY=your_api_key
  AI_MODEL=deepseek-chat
  ```

## 🐛 故障排除

### 测试失败：模板不存在

```
错误: 模板 12 不存在
解决: 先运行导入脚本
python tests/template_tests/scripts/import_templates.py
```

### AI测试失败：AI未启用

```
警告: AI检测未启用
解决: 检查.env中的AI配置
```

### 测试失败：首行缩进问题

```
问题: 首行缩进计算不准确
说明: 2字符缩进 = 5.3mm (使用Mm(5.3)创建文档)
```

## 📈 性能基准

基于本地测试的性能指标：

| 指标 | 值 |
|------|-----|
| 测试文档生成 | < 1秒 |
| 格式检测 | < 0.5秒/文档 |
| AI检测 | 2-5秒/文档 |
| 总测试时间 | < 15秒 |

## 🔄 更新测试

### 添加新的测试用例

1. 在 `scripts/test_template_with_ai.py` 中添加新的文档生成方法
2. 在 `main()` 函数中添加测试配置
3. 运行测试验证

### 导入新模板

1. 将.docx文件放到 `doc/方案模板/` 目录
2. 修改 `scripts/import_templates.py` 中的模板配置
3. 运行导入脚本
4. 更新测试用例以覆盖新模板

## 📚 相关文档

- [规则引擎实现细节](../../doc/规则引擎实现细节.md)
- [规则中心功能实现文档](../../doc/规则中心功能实现文档.md)
- [测试README](../README.md)

## 🤝 贡献指南

添加新测试时请确保：

1. ✅ 调用现有API，不重复实现
2. ✅ 添加详细的注释说明测试意图
3. ✅ 更新测试报告
4. ✅ 确保所有测试通过后再提交

## 📞 联系方式

如有问题或建议，请在项目中提issue。

---

**最后更新**: 2026-01-28
**测试状态**: ✅ 所有测试通过
**维护者**: 开发团队
