# 3 步使用 v3

1. 安装一次依赖：

```bash
python3 -m pip install -r requirements.txt
```

2. 对你的文章运行：

```bash
python3 scripts/pipeline.py package "/path/to/文章.md"
```

3. 打开终端输出的发布包目录，确认：

```bash
python3 scripts/pipeline.py check "<发布包目录>"
```

然后：公众号复制 `微信公众号.md`；小红书按 `小红书.md` 的顺序上传三张图；即刻上传封面并复制 `即刻.md`。

需要换输出目录时：

```bash
python3 scripts/pipeline.py package "/path/to/文章.md" --output "/path/to/发布包"
```
