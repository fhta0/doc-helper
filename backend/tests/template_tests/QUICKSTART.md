# 快速开始指南

## 5分钟快速上手

### 1. 运行格式测试 (30秒)

```bash
cd /mnt/d/code/doc-ai/backend
python tests/template_tests/scripts/test_template_accuracy.py
```

✅ **预期输出**: 100%通过

### 2. 运行完整测试 (60秒)

```bash
python tests/template_tests/scripts/test_template_with_ai.py
```

✅ **预期输出**: 100%通过（需要AI配置）

### 3. 查看测试报告

```bash
cat tests/template_tests/reports/TEST_SUMMARY.md
```

## 一行命令

```bash
# 运行所有pytest测试 + 模板测试
\
pytest && \
python tests/template_tests/scripts/test_template_accuracy.py && \
python tests/template_tests/scripts/test_template_with_ai.py
```

## 常见问题

### Q: 测试失败：模板不存在
**A**: 先运行导入脚本
```bash
python tests/template_tests/scripts/import_templates.py
```

### Q: AI测试失败
**A**: 检查 `.env` 中的AI配置：
```
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your_key
AI_MODEL=deepseek-chat
```

### Q: 想了解更多
**A**: 阅读完整文档
```bash
cat tests/template_tests/README.md
```

## 测试内容

- ✅ 页边距、纸张大小
- ✅ 字体、字号
- ✅ 行距、缩进
- ✅ 标题样式
- ✅ 错别字检测（AI）
- ✅ 交叉引用检测（AI）

## 下一步

1. 阅读 `README.md` 了解详细信息
2. 查看 `reports/COMPLETE_TEMPLATE_TEST_REPORT.md` 了解测试细节
3. 根据需要定制测试用例

---
**提示**: 格式测试不需要AI，可以离线运行。AI测试需要网络连接。
