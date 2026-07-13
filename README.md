# 🖼️ GitHub 图床

使用 GitHub 仓库作为免费图床，通过 jsDelivr CDN 加速访问。

## ✨ 特性

- 🆓 完全免费，无流量限制
- ⚡ jsDelivr CDN 全球加速
- 🗂️ 按年月自动分类存放
- 📦 自动压缩图片（Pillow）
- 📋 一键复制 Markdown 链接
- 🔒 稳定可靠，GitHub 背书

## 📁 目录结构

```
img-bed/
├── README.md           # 说明文档
├── upload.py           # 上传脚本
├── .gitignore
└── images/             # 图片存放目录
    ├── 2026-07/
    │   ├── 20260713114500_a1b2c3.png
    │   └── ...
    ├── 2026-08/
    │   └── ...
    └── ...
```

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/img-bed.git
cd img-bed
```

### 2. 安装依赖（可选，用于图片压缩）

```bash
pip install Pillow
```

> 不安装 Pillow 也能用，只是不会自动压缩图片。

### 3. 上传图片

```bash
# 上传单张图片
python3 upload.py screenshot.png

# 上传多张图片
python3 upload.py img1.png img2.jpg img3.gif

# 不压缩，上传原图
python3 upload.py photo.jpg --no-compress

# 复制 raw.githubusercontent 链接（默认是 jsDelivr CDN 链接）
python3 upload.py photo.jpg --raw
```

上传成功后，Markdown 链接会自动复制到剪贴板，直接粘贴即可使用。

## 🔗 链接格式

### jsDelivr CDN（推荐，速度快）

```
https://cdn.jsdelivr.net/gh/用户名/img-bed@main/images/2026-07/图片名.png
```

### raw.githubusercontent（备用）

```
https://raw.githubusercontent.com/用户名/img-bed/main/images/2026-07/图片名.png
```

### Markdown 引用

```markdown
![图片描述](https://cdn.jsdelivr.net/gh/用户名/img-bed@main/images/2026-07/图片名.png)
```

## ⚙️ 配置

编辑 `upload.py` 顶部的配置区：

```python
GITHUB_USERNAME = "你的用户名"  # 留空则自动从 git remote 检测
REPO_NAME = "img-bed"
BRANCH = "main"
```

## 📝 压缩说明

| 格式   | 压缩策略                          |
|--------|-----------------------------------|
| JPEG   | 质量压缩至 85，自动优化           |
| PNG    | 优化压缩                           |
| WebP   | 质量压缩至 85                      |
| GIF    | 不压缩（保留动图）                 |
| SVG    | 不压缩（矢量格式）                 |
| BMP    | 直接保存                           |

所有图片宽度超过 1920px 时会等比缩放。

## 🌟 图床使用场景

- Markdown 笔记 / 博客配图
- README 项目截图
- Issue / PR 附图
- 论坛 / 社区分享图片

## 📜 License

MIT
