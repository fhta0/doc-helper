# 规则说明（简要）

每条规则对象字段说明：

- `id`: 规则唯一标识（字符串，大写下划线）
- `name`: 规则名称（人类可读）
- `category`: 规则分类（page, font, paragraph, heading, figure, reference, other）
- `match`: 规则应用目标（document, section, paragraph, run, style, table, figure, reference）
- `condition`: 规则判断条件，字段结构随 `category` 而不同，例如页面边距使用 `top_mm`/`left_mm` 等
- `error_message`: 发现问题时的提示文本
- `suggestion`: 修复建议
- `checker`: 可选，`deterministic`（本地规则判断）、`ai`（调用大模型）、`hybrid`（先本地再AI）
- `prompt_template`: 当 `checker` 为 `ai` 或 `hybrid` 时可选的模型 prompt 模板
- `timeout_sec`: optional，AI 调用超时设置（秒）

使用方式建议：
1. 后端加载规则（数据库或 JSON 文件）
2. 解析 `.docx` 文档，提取页面设置、段落、样式、图表和参考文献数据
3. 对于 `checker` 为 `deterministic` 的规则，同步运行并直接产生 issue；对于 `checker` 为 `ai` 的规则，可选择异步任务或同步调用模型（注意成本与延迟）
4. 针对每条规则的 `match` 与 `condition` 做布尔判断，若不匹配则生成 issue

示例文件：`sample_rules.json` 包含若干常用示例规则供参考。

示例文件：`sample_rules.json` 包含若干常用示例规则供参考。