# 📄pdf-to-markdown — 各类PDF 转 Markdown 自动化流水线

> **把 PDF 扔进去，Markdown 自动出来。扫描件？批量？全自动。你只管读。**

---

## 📌 为什么还需要这个工具？

[MarkItDown](https://github.com/microsoft/markitdown) 已经能把 Word、PPT、Excel、PDF 等五花八门的文件转成 Markdown。那为什么还要包一层？

**因为总有些 PDF 格式不那么友好——尤其是你花了大价钱下载的非免费文献。**

| 场景 | MarkItDown 自己 | pdf-to-markdown |
|------|----------------|-------------|
| 📄 **文字版 PDF** | ✅ 正常工作 | ✅ 自动处理 |
| 🚫 **复制限制 PDF**（可读但"禁止复制"） | ❌ **拒绝提取**（pypdf 遵守权限flag） | ✅ **PyMuPDF 绕过限制**，直接提取文本 |
| 🖼️ **扫描件 PDF**（图片型，无文字层） | ❌ **输出空文件** | ✅ **自动 OCR 识别**文字 |
| 📚 **批量 50 篇混合 PDF** | ❌ 得手写脚本循环 | ✅ **放进去就完事** |
| 👀 **持续监听新文件** | ❌ 每次手动敲命令 | ✅ **watch 模式**，拖进去自动转 |
| 🧠 **喂给 LLM 分析** | ✅ 能用 | ✅ **带元信息头**（标题/来源/页数），更友好 |
| 🔒 **密码加密 PDF**（打开就要密码） | ❌ **无法打开** | ⚠️ **检测加密**并提示用户，可选集成解密工具 |

pdf-to-markdown = MarkItDown + OCR + 批处理 + 文件监听，开箱即用。

---

## 📌 项目简介

### 怎么工作的？

```
你放 PDF                 你拿到的
───────     ─────────     ────────
paper.pdf   →  自动化   →   paper.md
                   流程：
                   PDF → 智能判断
                   ├─ 可复制 → 直接提取
                   └─ 扫描件 → OCR 识别（pytesseract）
                   统一 → MarkItDown 润色 → 带元信息的 Markdown
```

### 适合谁？

| 用户 | 用途 |
|------|------|
| 🧪 **科研人员 / 研究生** | 刷论文、写综述，PDF 论文批量转笔记 |
| 📊 **咨询 / 分析师** | 整理行业报告、PDF 研报全文提取 |
| 🏛️ **法律 / 政务** | 大批扫描件电子化归档 |
| 🤖 **LLM / AI 用户** | 批量准备语料，让 ChatGPT、Claude 吃干净文本 |
| 📝 **知识管理爱好者** | Obsidian / Notion / Logseq 素材导入流水线 |
| 🔄 **任何每天跟 PDF 打交道的人** | 一句话：PDF in → Markdown out |

---

## 🚀 快速开始（5 分钟搞定）

### 方法零：用 AI 编程助手一句话装好 ⭐

**不想手动敲命令？打开任意 AI 编程助手（Claude Code / Codex / Cursor / GitHub Copilot / Windsurf / Continue / Cline / 豆包 MarsCode / 通义灵码……），把下面这句话发给它：**

```text
""帮我从 https://github.com/lanyuanyayi/pdf-to-markdown 克隆这个项目，
安装所有依赖（包括 Tesseract OCR），然后检查环境是否就绪"
```

AI 会自动帮你：
1. ✅ `git clone` 下载项目
2. ✅ `pip install -r requirements.txt` 安装 Python 依赖
3. ✅ `conda install tesseract`（或引导你安装 OCR 引擎）
4. ✅ `python main.py --check` 验证环境

全程不需要你敲一行命令，AI 帮你搞定。

> 💡 **对话示例：**
> - "帮我装好这个 PDF 转 Markdown 工具"
> - "配置一下项目环境，我要开始用了"
> - "检查下环境还缺什么，帮我补上"

---

### 手动安装（跟着走也行）

### 第一步：安装 Python

确保已有 Python 3.10+（推荐 3.11/3.12）。

```bash
python --version
# 应该显示 Python 3.10.x 或更高
```

如果没有，去 https://www.python.org/downloads/ 下载安装。

### 第二步：安装 Tesseract-OCR（处理扫描件 PDF 需要）

> ⚠️ 仅处理**扫描件 PDF** 需要此步骤。文字版 PDF 可直接使用。

**方法一：conda（推荐，如果有 Miniconda/Anaconda）**
```bash
conda install -y conda-forge::tesseract
```
工具随后会自动下载语言数据包。

**方法二：手动安装（没有 conda）**
1. 打开 https://github.com/UB-Mannheim/tesseract/wiki
2. 下载 `tesseract-ocr-w64-setup-...exe`（最新版）
3. 安装时**务必勾选**：简体中文语言包 + 添加到 PATH
4. 验证：`tesseract --version`

> 不想装 Tesseract？没问题——**文字版 PDF 完全不受影响**，只有扫描件会跳过。

### 第三步：安装 Python 依赖

```bash
# 进入项目目录
cd pdf-to-markdown

# 一键安装所有依赖
pip install -r requirements.txt
```

这条命令会自动安装：
- `pymupdf` → PDF 文本提取
- `pytesseract` → OCR（文字识别）
- `pdf2image` → PDF 转图片
- `pillow` → 图片处理
- `watchdog` → 文件夹自动监听
- `markitdown` → Microsoft 官方格式转换

### 第四步：验证环境

```bash
python main.py --check
```

你会看到类似输出：

```
==================================================
  pdf-to-markdown — 环境检查
==================================================
  Python:   3.13.13 ✓
  PyMuPDF:  已安装 ✓
  Pillow:   已安装 ✓
  pytesseract: 已安装 ✓
  pdf2image: 已安装 ✓
  watchdog: 已安装 ✓
  MarkItDown: 可用 ✓
  Tesseract-OCR: 已配置 ✓
  input_pdfs/: ✓
  output_md/: ✓
  temp/: ✓
==================================================
  环境检查通过 ✓ 一切就绪！
==================================================
```

---

## 📖 使用方法

### 方式一：用 AI 编程助手自然语言操作 ⭐

**不会写命令？没关系。打开任意 AI 编程助手（Claude Code / Codex / Cursor / GitHub Copilot / Windsurf / Continue / Cline / 豆包 MarsCode / 通义灵码……），在聊天框里直接说中文就行：**

```text
"帮我处理这个文件夹里所有 PDF，转成 Markdown"
"把扫描件的论文 OCR 识别后转成 md"
"监听 input_pdfs 文件夹，有新 PDF 自动处理"
"帮我把这篇 paper.pdf 转成 Markdown"
"批量处理所有 PDF，中文的用 chi_sim 语言"
```

AI 助手会自动帮你运行对应的命令，你只需要把 PDF 放进 `input_pdfs/` 文件夹即可。

> 💡 **推荐工作流：**
> 1. 用 AI 编程助手打开本项目的文件夹
> 2. 把 PDF 拖入 `input_pdfs/`
> 3. 打字说："帮我把这些 PDF 转成 Markdown"
> 4. 等着收 `output_md/` 里的结果

### 方式二：拖放文件 → 自动处理

```bash
python main.py --watch
```

然后，**直接把 PDF 文件拖进 `input_pdfs/` 文件夹**。

工具会自动：
1. 检测到新文件进入
2. 判断是文字版还是扫描件
3. 处理并输出到 `output_md/`
4. 同名 `.md` 文件自动生成

> 💡 **注意：** 文件处理中窗口会显示进度，完成后会在同一文件名后生成 .md 文件。请勿在输出目录打开文件时处理，可能会有权限冲突。

### 方式三：批量处理整个文件夹

把 PDF 全部放入 `input_pdfs/` 后运行：

```bash
python main.py
```

程序会自动处理该目录下 **所有 PDF 文件**。

### 方式四：处理单个文件

```bash
python main.py --input "C:\Users\xxx\paper.pdf"
```

### 方式五：自定义参数

```bash
python main.py --input ./input_pdfs --output ./my_notes --lang chi_sim
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--input` / `-i` | 输入 PDF 文件或目录 | `./input_pdfs/` |
| `--output` / `-o` | 输出目录 | `./output_md/` |
| `--watch` / `-w` | 持续监听模式 | off |
| `--lang` | OCR 语言 (`eng` / `chi_sim`) | `eng` |
| `--dpi` | OCR 分辨率（越高越清晰但越慢） | `300` |
| `--password` / `-p` | PDF 密码（加密文献需要） | 无 |
| `--check` / `-c` | 仅检查环境不处理 | off |
| `--verbose` / `-v` | 显示详细日志 | off |

---

## 📂 项目结构

```
pdf-to-markdown/
│
├── input_pdfs/       ← 你放 PDF 的地方（拖进去就行）
├── temp/             ← OCR 中间图片（自动管理）
├── output_md/        ← 转换好的 Markdown 文件
│
├── main.py           ← 主程序入口（双击或命令行运行）
├── pdf_parser.py     ← PDF 文本提取模块
├── ocr_engine.py     ← OCR 识别模块（扫描件专用）
├── md_converter.py   ← MarkItDown 转换封装
├── watcher.py        ← 文件夹自动监听模块
│
├── requirements.txt  ← Python 依赖清单
└── README.md         ← 本说明书
```

---

## 🔄 工作流程

```
                    ┌─────────────────────┐
                    │   input_pdfs/       │
                    │   (放入 PDF)        │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  PDF 解析            │
                    │  (PyMuPDF 读文本)    │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  ⛔ 密码加密？       │
                    │  → 提示用户 --password│
                    └──────┬──────────────┘
                           │ 无密码
                           ▼
                    ┌─────────────────────┐
                    │  可复制文本？        │
                    │  长度 > 100 字符？   │
                    └──────┬──────┬───────┘
                           │      │
                       是  │      │  否
                           │      │
                           ▼      ▼
               ┌────────────┐  ┌──────────────┐
               │ 直接提取    │  │ OCR 识别      │
               │ 文本        │  │ (pytesseract) │
               └──────┬─────┘  └──────┬───────┘
                      │               │
                      └───────┬───────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  MarkItDown 转换     │
                    │  原始文本 → Markdown │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  output_md/         │
                    │  paper.md ✓         │
                    └─────────────────────┘
```

---

## ❓ 常见问题（FAQ）

### Q1: PDF 放进去后没有生成 .md 文件？

**可能的原因：**

1. **没有启动程序** — 需要先运行 `python main.py` 或 `python main.py --watch`
2. **文件正在被占用** — PDF 正在被其他程序打开（如浏览器、Adobe Reader），关闭后再试
3. **文件名含特殊字符** — 重命名为纯英文/数字
4. **Tesseract 未安装**（扫描件 PDF）— 看下面的 OCR 相关 FAQ

### Q2: OCR 失败 / 提示 "Tesseract not found"

**原因：** 没有安装 Tesseract-OCR 引擎。

**解决方法：**

```bash
# 第一步：下载安装
# 打开 https://github.com/UB-Mannheim/tesseract/wiki
# 下载 tesseract-ocr-w64-setup-...exe

# 第二步：安装后验证
tesseract --version

# 第三步：如果路径不在 PATH 中，可以手动指定
# 打开 ocr_engine.py，修改 TESSERACT_CANDIDATE_PATHS
# 加入你的安装路径，例如:
#   r"D:\Program Files\Tesseract-OCR\tesseract.exe"
```

安装后重新运行 `python main.py --check` 验证。

### Q3: PDF 能复制文字，但工具仍然走 OCR？

**原因：** 程序的判断阈值是文本长度 < 100 字符。

**解决方法：**
打开 `pdf_parser.py`，修改：

```python
TEXT_LENGTH_THRESHOLD = 100   # 改为更小的值，如 20
```

数字越小，越不容易被判定为扫描件。

### Q4: MarkItDown 找不到 / 转换失败？

只需确保 markitdown 已安装即可：

**如果报找不到：**

```bash
# 方法一：pip 安装
pip install markitdown

# 方法二：从 GitHub 克隆最新版
git clone https://github.com/microsoft/markitdown.git
cd markitdown
pip install -e .
```

### Q5: 中文乱码？

**原因：** OCR 默认使用英文语言包，中文 PDF 无法识别。

**解决方法：**

```bash
# 处理中文 PDF 时加 --lang chi_sim 参数
python main.py --lang chi_sim

# 或者安装更多语言包（在 Tesseract 安装时勾选）
# 支持的语言：eng（英文）, chi_sim（简体中文）, chi_tra（繁体中文）
```

### Q6: PDF 加密/有密码怎么办？

某些非免费文献的 PDF 带有密码保护。本工具会自动检测加密状态：

- **无密码 → 正常处理** ✅
- **有密码但未提供 → 给出友好提示并跳过** ⚠️

```bash
# 如果你知道密码：
python main.py --input encrypted.pdf --password "你的密码"

# 或者让 AI 助手直接处理：
# "帮我用密码 xxx 处理这个加密 PDF"
```

常见情况：
- 有些 PDF 的"复制限制"不是真加密，PyMuPDF 可以直接绕过 ← ✅ 本工具自动处理
- 有些 PDF 有 owner password（打开不需要密码，但限制编辑/复制）← ✅ 同样绕过
- 只有打开就需要输密码的才需要 `--password`

### Q7: 日志在哪里看？

所有处理日志会直接打印在终端窗口中。如果要保存到文件：

```bash
python main.py --verbose 2>&1 | tee process.log
```

---

## 🧪 高级用法

### 配合 Obsidian / Logseq

在输出目录 `output_md/` 上创建符号链接到你的笔记库即可。

```bash
# Windows (管理员 PowerShell)
New-Item -ItemType SymbolicLink -Path "D:\Obsidian\我的笔记\PDF导入" -Target "D:\你的路径\pdf-to-markdown\output_md"
```

### 配合 ChatGPT / Claude 分析

直接拖拽 `.md` 文件到 ChatGPT 或 Claude 的对话窗口即可——LLM 读 Markdown 比读 PDF 准得多。

### 批量处理 + 不同语言混合

如果文件夹里同时有中英文 PDF：

```bash
# 先处理英文的
python main.py --lang eng

# 再处理中文的（移动已处理的 PDF 后）
python main.py --lang chi_sim
```

---

## 🔧 文件说明

| 文件 | 功能 | 你可能会修改的地方 |
|------|------|-------------------|
| `main.py` | 主入口，命令行参数解析 | 很少修改 |
| `pdf_parser.py` | PDF 文本提取与扫描件判断 | `TEXT_LENGTH_THRESHOLD`（扫描件阈值） |
| `ocr_engine.py` | OCR 识别 | `TESSERACT_CANDIDATE_PATHS`（Tesseract路径） |
| `md_converter.py` | MarkItDown 封装 | 很少修改 |
| `watcher.py` | 文件夹监听 | `cooldown`（防重复触发间隔） |

---

## 📋 依赖清单

| 包名 | 用途 | 安装 |
|------|------|------|
| pymupdf | PDF 文本提取 | `pip install pymupdf` |
| pytesseract | OCR 封装 | `pip install pytesseract` |
| pdf2image | PDF→图片 | `pip install pdf2image` |
| pillow | 图片处理 | `pip install pillow` |
| watchdog | 文件监听 | `pip install watchdog` |
| markitdown | Markdown 转换 | `pip install markitdown` |
| Tesseract-OCR | 识别引擎 | 手动安装（见上文） |

---

## 📄 License

MIT — 自由使用、修改、分发。

---

## ⭐ 如果对你有帮助

觉得好用的话给项目点个 Star ⭐ 欢迎提 Issue 或 PR 改进。

**Happy Researching! 🧪📚**
