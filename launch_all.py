"""一键启动所有宠物: python launch_all.py
格式: (图片文件名, 屏幕编号, 动物类型, 大小px)
动物类型: cat / dog / generic
"""
import subprocess, sys, os

pets = [
    ("pet.png",  0, "dog",     100),
    ("cat1.png", 1, "cat",     100),
    ("cat2.png", 2, "cat",     100),
]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for img, screen, ptype, size in pets:
    if os.path.exists(img):
        subprocess.Popen([sys.executable, "main.py", img, str(screen), ptype, str(size)])
        print(f"started: {img} -> screen {screen} | type={ptype} | size={size}px")
    else:
        print(f"skip (not found): {img}")
