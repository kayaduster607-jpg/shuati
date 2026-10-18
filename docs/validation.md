# 公开发布验证记录

验证日期：2026-10-18。

## 实际结果

| 检查 | 结果 | 覆盖范围 |
| --- | --- | --- |
| Flask API 隔离验证 | **27 项通过** | 静态首页、登录/错误密码、匿名拒绝、管理员权限、用户隔离、题库与题目、批量去重、编辑、记录、进度、用户管理和注销 |
| 两份页面的脚本与逻辑 | **32 项通过** | JavaScript 语法、示例五种题型解析、Excel 列映射、题干去重和答案比较 |
| Compose 配置 | **通过** | `docker compose config --quiet`，显式传入空配置文件，避免自动加载本地 env 文件 |
| 架构图 | **通过** | SVG 导出 1600 × 1230 PNG 后检查文字和连接关系 |
| 源码与文档检查 | **通过** | Python 语法、README 本地链接、导航锚点、发布文件清单及敏感数据排除 |

## 验证环境

- Windows，Python 3.13.5，Flask 3.1.3，Flask-Cors 6.0.5。
- Node.js 22.22.2，用于内联脚本语法和纯函数验证。
- Docker 客户端 29.2.1，Docker Compose v5.1.0。
- Dockerfile 基础镜像为 `python:3.11-slim`；本次 API 验证使用本机隔离环境，并未声称已验证容器内运行。

API 脚本在导入 `app.py` **之前**将 `DATA_DIR` 指向临时目录；应用只在临时目录初始化演示账号和测试数据，执行结束后清理。未读取原项目任何 `.env` 文件，也没有打开真实用户数据、登录资料或部署压缩包。

前端脚本通过 Node.js VM 加载项目真实内联脚本，跳过页面初始化，只调用导入、标准化和判题函数。它不使用真实浏览器存储、不加载 CDN，也不模拟完整页面交互。

## 复现

从项目根目录、使用已安装 Flask/Flask-Cors 的 Python 环境运行：

```bash
python scripts/verify_api.py
node scripts/verify_frontend.cjs
```

Compose 检查可在自己准备好部署配置后运行 `docker compose config --quiet`。原 Compose 文件保留了旧式 `version: '3'`，新版 Compose 会提示该字段已过时并忽略它；检查仍成功。

## 未覆盖的范围

- 本机 Docker 引擎未运行，没有执行镜像构建或容器启动。
- 没有执行真实浏览器端到端点击、移动端布局和完整多标签页交互验证。
- 没有实际导入二进制 Word/Excel/PDF 文件；测试了题目文本解析和 Excel 表头映射，未验证 CDN 可用性或解析库对所有文档排版的表现。
- 没有进行并发写入、性能、渗透或数据恢复测试。JSON 文件读写和演示级认证的边界见 README。

## 本次交付范围

- 重写中文 README，明确本地版与部署版的入口、存储、账号、导入格式和部署方法。
- 新增架构 PNG/SVG 及标准库绘图脚本。
- 新增五题演示文本和可复现的 API/前端验证脚本。
- 新增 Git 与 Docker 忽略规则，排除本地数据、环境文件、缓存、IDE/助手配置、压缩包及 Word 文档。
- 保留原 `app.py`、两份 HTML、Dockerfile、Compose 和部署脚本的业务与运行逻辑。

公开副本不包含 `刷题通使用说明.doc`、`shuati-deploy.tar.gz`、`.claude/` 或运行数据。原 README 已在发布工作区私下备份。
