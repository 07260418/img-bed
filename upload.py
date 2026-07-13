#!/usr/bin/env python3
"""
GitHub 图床上传脚本
功能：自动压缩、重命名、按年月分类存放、git 推送、复制 CDN 链接到剪贴板

用法:
    python3 upload.py <图片路径> [图片路径...]
    python3 upload.py screenshot.png
    python3 upload.py img1.png img2.jpg img3.gif

选项:
    --no-compress    不压缩图片，直接上传原图
    --no-push        不自动 git push（仅本地提交）
    --raw            复制 raw.githubusercontent 链接（默认复制 jsDelivr CDN 链接）
"""

import os
import sys
import hashlib
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# ==================== 配置区 ====================
# 也可以不填，脚本会自动从 git remote 检测
GITHUB_USERNAME = "07260418"  # 你的 GitHub 用户名
REPO_NAME = "img-bed"  # 仓库名
BRANCH = "main"        # 分支名
# ================================================

# 支持的图片格式
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

# 压缩参数
MAX_WIDTH = 1920        # 最大宽度（px），超过则等比缩放
JPEG_QUALITY = 85       # JPEG 压缩质量 (1-100)
PNG_OPTIMIZE = True     # 是否优化 PNG


def get_github_username():
    """从 git remote 自动检测 GitHub 用户名"""
    global GITHUB_USERNAME
    if GITHUB_USERNAME:
        return GITHUB_USERNAME
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        url = result.result.strip() if hasattr(result, 'result') else result.stdout.strip()
        # https://github.com/USERNAME/REPO.git  或  git@github.com:USERNAME/REPO.git
        if "github.com" in url:
            if url.startswith("https"):
                # https://github.com/USERNAME/REPO.git
                parts = url.replace("https://github.com/", "").split("/")
                if len(parts) >= 1:
                    GITHUB_USERNAME = parts[0]
            elif url.startswith("git@"):
                # git@github.com:USERNAME/REPO.git
                parts = url.split(":")[1].split("/")
                if len(parts) >= 1:
                    GITHUB_USERNAME = parts[0]
    except Exception:
        pass
    return GITHUB_USERNAME


def compress_image(src_path, dst_path):
    """压缩图片，返回压缩后的路径"""
    try:
        from PIL import Image
    except ImportError:
        print("  ⚠️  未安装 Pillow，跳过压缩（pip install Pillow 可启用压缩）")
        import shutil
        shutil.copy2(src_path, dst_path)
        return

    img = Image.open(src_path)

    # 处理 EXIF 旋转
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # 等比缩放
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    ext = Path(dst_path).suffix.lower()

    if ext in (".jpg", ".jpeg"):
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(dst_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    elif ext == ".png":
        img.save(dst_path, "PNG", optimize=PNG_OPTIMIZE)
    elif ext == ".webp":
        img.save(dst_path, "WEBP", quality=JPEG_QUALITY)
    elif ext == ".gif":
        # GIF 保留动图，不压缩
        import shutil
        shutil.copy2(src_path, dst_path)
    elif ext == ".bmp":
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(dst_path, "BMP")
    elif ext == ".svg":
        # SVG 是文本格式，直接复制
        import shutil
        shutil.copy2(src_path, dst_path)
    else:
        img.save(dst_path)

    # 比较压缩前后大小
    orig_size = os.path.getsize(src_path)
    new_size = os.path.getsize(dst_path)
    saved = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
    print(f"  📦 压缩: {format_size(orig_size)} → {format_size(new_size)} (节省 {saved:.1f}%)")


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f}MB"


def generate_filename(src_path):
    """生成唯一文件名：时间戳 + 文件内容hash前6位"""
    ext = Path(src_path).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 用文件内容生成短 hash
    hash_str = "000000"
    try:
        with open(src_path, "rb") as f:
            hash_str = hashlib.md5(f.read()).hexdigest()[:6]
    except Exception:
        pass

    return f"{timestamp}_{hash_str}{ext}"


def get_target_dir():
    """获取目标目录：images/YYYY-MM/"""
    year_month = datetime.now().strftime("%Y-%m")
    script_dir = Path(__file__).parent
    target_dir = script_dir / "images" / year_month
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def copy_to_clipboard(text):
    """复制文本到剪贴板（macOS）"""
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


def git_commit_and_push(file_path, auto_push=True):
    """git add, commit, push"""
    script_dir = Path(__file__).parent
    cmds = [
        ["git", "add", str(file_path)],
        ["git", "commit", "-m", f"upload: {Path(file_path).name}"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️  Git 命令失败: {' '.join(cmd)}")
            if result.stderr:
                print(f"     {result.stderr.strip()}")
            return False

    if auto_push:
        print("  🚀 推送到 GitHub...")
        result = subprocess.run(
            ["git", "push", "origin", BRANCH],
            cwd=script_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ⚠️  Git push 失败: {result.stderr.strip()}")
            return False

    return True


def build_urls(filename, relative_path):
    """构建 CDN 和 raw 链接"""
    username = get_github_username()
    if not username:
        print("  ⚠️  无法检测 GitHub 用户名，请在脚本顶部配置 GITHUB_USERNAME")
        return None, None

    path_in_repo = f"images/{datetime.now().strftime('%Y-%m')}/{filename}"

    # jsDelivr CDN
    cdn_url = f"https://cdn.jsdelivr.net/gh/{username}/{REPO_NAME}@{BRANCH}/{path_in_repo}"
    # raw.githubusercontent
    raw_url = f"https://raw.githubusercontent.com/{username}/{REPO_NAME}/{BRANCH}/{path_in_repo}"

    return cdn_url, raw_url


def upload_image(src_path, compress=True, auto_push=True):
    """上传单张图片"""
    src = Path(src_path).expanduser().resolve()

    # 验证文件
    if not src.exists():
        print(f"❌ 文件不存在: {src}")
        return None

    if src.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"❌ 不支持的格式: {src.suffix}（支持: {', '.join(SUPPORTED_FORMATS)}）")
        return None

    print(f"\n📎 处理: {src.name}")

    # 生成唯一文件名
    new_filename = generate_filename(str(src))
    target_dir = get_target_dir()
    target_path = target_dir / new_filename

    # 压缩或直接复制
    if compress and src.suffix.lower() not in (".svg", ".gif"):
        compress_image(str(src), str(target_path))
    else:
        import shutil
        shutil.copy2(str(src), str(target_path))
        print(f"  📦 大小: {format_size(os.path.getsize(target_path))}")

    # git 提交推送
    success = git_commit_and_push(str(target_path), auto_push)
    if not success:
        print("  ⚠️  Git 操作未完全成功，文件已保存到本地")

    # 构建链接
    cdn_url, raw_url = build_urls(new_filename, str(target_path))

    return {
        "filename": new_filename,
        "local_path": str(target_path),
        "cdn_url": cdn_url,
        "raw_url": raw_url,
        "markdown_cdn": f"![{src.stem}]({cdn_url})" if cdn_url else None,
        "markdown_raw": f"![{src.stem}]({raw_url})" if raw_url else None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="GitHub 图床上传工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 upload.py screenshot.png
  python3 upload.py img1.png img2.jpg
  python3 upload.py photo.jpg --no-compress
  python3 upload.py photo.jpg --raw
        """
    )
    parser.add_argument("images", nargs="+", help="图片文件路径")
    parser.add_argument("--no-compress", action="store_true", help="不压缩图片")
    parser.add_argument("--no-push", action="store_true", help="不自动 git push")
    parser.add_argument("--raw", action="store_true", help="复制 raw 链接（默认 CDN）")

    args = parser.parse_args()

    print("=" * 60)
    print("  🖼️  GitHub 图床上传工具")
    print("=" * 60)

    results = []
    for img_path in args.images:
        result = upload_image(
            img_path,
            compress=not args.no_compress,
            auto_push=not args.no_push,
        )
        if result:
            results.append(result)

    if not results:
        print("\n❌ 没有图片上传成功")
        sys.exit(1)

    # 输出结果
    print("\n" + "=" * 60)
    print("  ✅ 上传完成！")
    print("=" * 60)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['filename']}")
        print(f"    CDN:  {r['cdn_url']}")
        print(f"    Raw:  {r['raw_url']}")
        print(f"    MD:   {r['markdown_cdn']}")

    # 复制第一个链接到剪贴板
    if results:
        link_type = "raw" if args.raw else "cdn"
        clipboard_url = results[0]["raw_url"] if args.raw else results[0]["cdn_url"]
        clipboard_md = results[0]["markdown_raw"] if args.raw else results[0]["markdown_cdn"]

        if copy_to_clipboard(clipboard_md):
            print(f"\n📋 已复制 Markdown 链接到剪贴板 ({link_type}):")
            print(f"   {clipboard_md}")
        else:
            print(f"\n📋 请手动复制链接:")
            print(f"   {clipboard_url}")


if __name__ == "__main__":
    main()
