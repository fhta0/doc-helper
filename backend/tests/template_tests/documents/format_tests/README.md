# 测试文档说明

本目录包含用于测试模板准确性的.docx文档。

## 📁 文件列表

### K3S建设方案模板测试

1. **正确_K3S建设方案.docx**
   - 完全符合K3S建设方案模板规范
   - 页边距: 上2.8/下2.4/左2.6/右2.4cm
   - 正文: 宋体 12pt, 行距18磅, 首行缩进2字符
   - 标题: 黑体 12pt, 不加粗
   - 预期检查结果: 0个问题

2. **错误_K3S建设方案.docx**
   - 故意包含多种格式错误
   - 用于验证检测功能的准确性
   - 预期检查结果: 6个问题
   - 错误类型: 页边距、字体、字号、行距、缩进、标题格式

### K3S设计方案模板测试

3. **正确_K3S设计方案.docx**
   - 完全符合K3S设计方案模板规范
   - 页边距: 上2.54/下2.54/左3.18/右3.18cm
   - 正文: 宋体 12pt, 行距18磅, 首行缩进2字符
   - 标题: 12pt, 加粗（从3级标题开始）
   - 预期检查结果: 0个问题

## 🔧 如何使用

这些文档由 `test_template_accuracy.py` 自动生成。

重新生成测试文档：
```bash
cd /mnt/d/code/doc-ai/backend
python test_template_accuracy.py
```

## 📊 测试结果

最新测试结果请查看: `TEMPLATE_ACCURACY_TEST_REPORT.md`

## 🎯 扩展测试

如需添加新的测试用例，可以修改 `test_template_accuracy.py` 中的：
- `TemplateTestDocumentGenerator` 类：添加新的文档生成方法
- `main()` 函数：添加新的测试文件配置

示例：
```python
# 添加新的测试用例
tester.test_template(
    template_id=12,
    test_files=[
        {
            "name": "边界情况测试",
            "path": "/path/to/test.docx",
            "expected_issues": 2
        }
    ]
)
```
