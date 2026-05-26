"""
把任意照片变成透明背景宠物图：
    python make_pet_from_photo.py 你的照片.jpg
生成 pet.png 后重启 main.py 即可看到新形象。
"""
import sys
from pathlib import Path
from PIL import Image
from rembg import remove


def process(src: str, out: str = "pet.png", size: int = 128):
    print(f"正在去除背景：{src}")
    with open(src, "rb") as f:
        result = remove(f.read())

    import io
    img = Image.open(io.BytesIO(result)).convert("RGBA")

    # 裁剪成正方形（居中）
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top  = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    img = img.resize((size, size), Image.LANCZOS)
    img.save(out)
    print(f"已保存 {out}  ({size}x{size})，重启程序即可看到新宠物！")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python make_pet_from_photo.py 照片路径.jpg [输出文件名.png]")
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "pet.png"
    process(src, out)
