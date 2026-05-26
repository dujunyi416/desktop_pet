import sys
import os
from PyQt5.QtWidgets import QApplication


def main():
    # 用法: python main.py [图片] [屏幕编号] [pet_type] [大小px] [名字]
    image_file = sys.argv[1] if len(sys.argv) > 1 else "pet.png"
    screen_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    pet_type   = sys.argv[3] if len(sys.argv) > 3 else None
    pet_size   = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    pet_name   = sys.argv[5] if len(sys.argv) > 5 else ""
    spawn_x    = int(sys.argv[6]) if len(sys.argv) > 6 else -1

    if not os.path.exists(image_file):
        print(f"not found: {image_file}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from pet import PetWidget
    pet = PetWidget(image_file, screen_idx, pet_type, pet_size, pet_name, spawn_x)
    pet.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
