# 刷题通 · Shuati

把现成试卷整理成题库，在同一个页面完成练习、错题复习和模拟考试。支持 DOCX、Excel、TXT、文本型 PDF，以及单选、多选、判断、填空、简答五种题型。

**第一次体验直接打开根目录 `index.html`。** 需要账号和多设备读取时，再启动 Flask / Docker 版。两种模式的题库分别保存，不会自动同步。

[用五题示例开始](#用五题示例完成一次练习) · [整理自己的试卷](#整理自己的试卷) · [账号版](#需要账号时启动部署版) · [数据与备份](#数据保存与备份) · [实现](#文档怎样变成题库)

## 用五题示例完成一次练习

下载并解压完整仓库，或运行：

```bash
git clone https://github.com/kayaduster607-jpg/shuati.git
cd shuati
```

1. 浏览器打开根目录 `index.html`，进入“题库管理”，新建名为“入门演示”的题库。
2. 在这个题库中选择“上传文档导入”，上传 [examples/questions.txt](examples/questions.txt)。文件里已经包含五种题型，可以直接使用。
3. 逐题检查导入预览中的题干、选项、答案和解析；修正警告后确认新增。**预览完成还没有入库，确认后才会保存。**
4. 进入练习，第一道题选择 A（Python），查看对错与解析。再试一道错题，回到错题入口重练。
5. 退出普通练习后再次进入，检查续练进度；需要整套测试时，在模拟考试中设置各题型数量和每题分值，再组卷、交卷查看成绩。

你输入的是试题文件和作答内容。系统输出可练习的题库、答案反馈、错题与考试成绩；通常不产生下载文件。本地版数据放在当前浏览器，需要联网加载文档解析库。

## 整理自己的试卷

TXT / DOCX 正文推荐按下面的格式排版：

```text
一、单选题
1. 以下哪种语言用于编写 Flask 应用？
A. Python
B. CSS
C. SQL
D. HTML
答案：A
解析：Flask 是 Python Web 框架。

二、多选题
2. 以下哪些属于浏览器端技术？
A. HTML
B. CSS
C. JavaScript
D. SQLAlchemy
答案：A,B,C
```

Excel 推荐使用 `题型、题目、A、B、C、D、答案、解析` 列。旧 `.doc` 先另存为 `.docx`；扫描 PDF 需先通过其他工具 OCR 成可提取文本的文档。

导入会检查缺答案、选项不足、题干异常与重复候选。解析是规则识别，预览是必要步骤。填空、简答采用清理后的字符串比较，不做语义评分；多选需要选项组合一致，不按部分正确计分。

## 需要账号时启动部署版

### Docker Compose

从项目根目录运行：

```bash
docker compose up -d --build
docker compose logs -f shuati
```

打开 [http://localhost:4000](http://localhost:4000)。首次启动且用户列表为空时创建以下**公开演示账号**：

| 用户名 | 初始密码 | 用途 |
| --- | --- | --- |
| `admin` | `admin123` | 创建用户、重置密码、查看统计 |
| `user` / `user2` / `user3` | `123456` | 个人题库与练习 |

登录后沿用上面的“五题示例”流程。让其他人访问前，修改保留账号密码并删除不用的演示用户；当前没有公开自助注册。

### 不使用 Docker

在 Windows PowerShell 中运行；其他系统用相应虚拟环境的 Python：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask Flask-Cors
$env:DATA_DIR = Join-Path (Get-Location) "data"
.\.venv\Scripts\python.exe app.py
```

同样访问 4000 端口。显式设置 DATA_DIR，可避免使用默认绝对目录 `/data`。该程序直接读取进程环境变量。

## 数据保存与备份

| 模式 | 保存位置 | 重启或换设备后 |
| --- | --- | --- |
| 根目录 HTML | localStorage 中的题库、题目、记录和续练进度 | 同一浏览器来源可以继续；清理浏览器数据会丢失 |
| Flask / Docker | DATA_DIR 下的 JSON，按用户目录分开 | 同账号访问同一服务可读取已保存内容；重启后重新登录 |

部署版的 `data/users.json` 保存账号；`data/userdata/<user_id>/` 保存 `banks.json`、`questions.json`、`records.json`、`saved_practice.json`。Compose 挂载整个 `./data` 和 `./static`，备份时先停止写入，再复制完整 `data/`，不要只复制账号文件。

普通练习支持续练；模拟考试没有同一份续练快照，不要依赖刷新恢复考试。删除题库会删除题目，旧答题记录没有同步级联清理。

## 文档怎样变成题库

![本地与账号模式的数据流](docs/assets/architecture.png)

文件解析、候选校验、题目渲染、判题和成绩计算都在浏览器完成。部署版仅把确认后的结构化题目及练习记录交给 Flask；后端按登录用户选择 JSON 目录。两份页面分别位于 `index.html` 和 `static/index.html`，修改公共逻辑时需要一起检查。

这让个人使用不必部署数据库，但也限定了服务能力：整份 JSON 无文件锁，Token 在内存中且没有过期机制，密码使用无盐 SHA-256。当前适合本机或受控的单实例练习。题目答案会发到浏览器，考试成绩用于自测，不具备正式考试防作弊保证。

## 排查与开发

| 问题 | 先检查 |
| --- | --- |
| 导入后没有题目 | 是否确认新增；是否仍有缺答案等警告 |
| PDF 预览为空 | 是否扫描件；当前无 OCR |
| 本地题库没出现在账号版 | 两套存储独立，当前没有自动迁移 |
| 容器有 API 但页面打不开 | 单独 docker run 时是否漏挂载 static；推荐用 Compose |
| 简答意思正确仍判错 | 当前比较字符串，核对标准答案或人工调整 |

```bash
python scripts/verify_api.py
node scripts/verify_frontend.cjs
```

验证范围见 [docs/validation.md](docs/validation.md)。API 核心入口是 `app.py`，包括 `/api/auth/*`、`/api/banks`、`/api/questions`、`/api/records` 和 `/api/saved-practice`；业务请求使用登录返回的 Bearer Token。架构图另有 [SVG 原稿](docs/assets/architecture.svg)。

仓库没有独立 LICENSE；使用和再分发时请先确认授权。
