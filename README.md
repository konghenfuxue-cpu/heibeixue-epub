# 黑背雪 EPUB 工坊

用于分享黑背雪制作的 EPUB、可复用排版模板，以及 EPUB 检查与修复工具。

## 当前内容

- `skills/txt-to-epub-template`：把中文小说 TXT 制作为带封面、简介、制作说明、目录和章节页的 EPUB 3。
- `skills/epub-repair`：检查并安全修复 EPUB 的 ZIP 包装、container、OPF、manifest、spine 和导航引用。
- `books/`：存放原创、已获授权或公版 EPUB 的清单及发布说明。

当前仓库首版只发布工具和模板，不包含商业小说正文。

## 排版效果预览

以下页面由仓库内的 TXT 转 EPUB 模板生成，文字均为原创示例，不含商业小说正文。实际阅读时，正文背景会跟随阅读器主题。

| 封面 | 简介 | 制作说明 |
| --- | --- | --- |
| ![自适应封面](docs/images/cover.png) | ![双层卡片简介页](docs/images/introduction.png) | ![制作说明页](docs/images/production-note.png) |

| 卷页 | 正文 |
| --- | --- |
| ![卷标题页](docs/images/volume-page.png) | ![中文正文排版](docs/images/chapter-page.png) |

## 使用 TXT 转 EPUB 模板

在 Codex 中可以直接说：

```text
使用 $txt-to-epub-template，把这份中文小说 TXT 制作为 EPUB。
```

也可以直接运行：

```powershell
python skills/txt-to-epub-template/scripts/txt_to_epub.py "原稿.txt" `
  --title "书名" `
  --author "作者" `
  --cover "封面.jpg" `
  --output "书名.epub"
```

运行：

```powershell
python skills/txt-to-epub-template/scripts/txt_to_epub.py --help
```

可查看封面、简介、制作团队、版本、日期、来源与排版致谢等参数。

## 安装 Skills

将需要的 Skill 文件夹复制到个人 Codex Skills 目录，或从本仓库安装。每个 Skill 都包含自己的 `SKILL.md`、脚本和资源文件。

## 版式致谢

模板的制作说明与简介页参考鬼鬼制作的《塞壬之刃》；正文背景和封面适配参考湖心溪露制作的《我的超能力每周刷新》。生成的制作说明页默认保留排版参考致谢。

本仓库与上述制作者及作品不存在官方隶属或授权关系，引用仅用于说明版式灵感来源。

## 版权规则

只接受以下 EPUB：

1. 上传者拥有完整版权的原创作品；
2. 已获得作者或版权方明确公开授权的作品；
3. 已进入公有领域的作品；
4. 许可证明确允许再分发的作品。

请勿提交来源不明、购买获得、平台抓取或未经许可传播的商业小说。详细要求见 [BOOKS_POLICY.md](BOOKS_POLICY.md)。

## 许可证

仓库中的脚本、Skill 指令和通用样式以 [MIT License](LICENSE) 发布。书籍内容不自动适用 MIT；每本书必须在 `books/catalog.yml` 中单独声明权利状态与许可证。
