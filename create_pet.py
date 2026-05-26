"""Run this once to generate the placeholder pet image: python create_pet.py"""
import math
from PIL import Image, ImageDraw


def create_cat_image(filename="pet.png", size=128):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    orange     = (255, 150,  40, 255)
    dark_or    = (190, 100,  10, 255)
    ear_pink   = (255, 200, 200, 255)
    eye_green  = ( 80, 210,  90, 255)
    pupil      = ( 20,  20,  20, 255)
    shine      = (255, 255, 255, 180)
    nose_pink  = (255, 140, 160, 255)

    def s(v):
        return int(v * size / 128)

    # Body
    draw.ellipse([s(28), s(72), s(100), s(120)], fill=orange, outline=dark_or, width=1)

    # Head
    draw.ellipse([s(12), s(12), s(116), s(90)], fill=orange, outline=dark_or, width=1)

    # Left ear
    draw.polygon([(s(12), s(42)), (s(4), s(4)), (s(50), s(20))], fill=orange)
    draw.polygon([(s(15), s(38)), (s(10), s(10)), (s(46), s(22))], fill=ear_pink)

    # Right ear
    draw.polygon([(s(116), s(42)), (s(124), s(4)), (s(78), s(20))], fill=orange)
    draw.polygon([(s(113), s(38)), (s(118), s(10)), (s(82), s(22))], fill=ear_pink)

    # Left eye
    draw.ellipse([s(26), s(36), s(56), s(62)], fill=eye_green)
    draw.ellipse([s(33), s(42), s(49), s(56)], fill=pupil)
    draw.ellipse([s(35), s(44), s(42), s(51)], fill=shine)

    # Right eye
    draw.ellipse([s(72), s(36), s(102), s(62)], fill=eye_green)
    draw.ellipse([s(79), s(42), s(95), s(56)], fill=pupil)
    draw.ellipse([s(81), s(44), s(88), s(51)], fill=shine)

    # Nose
    draw.polygon([(s(64), s(65)), (s(57), s(73)), (s(71), s(73))], fill=nose_pink)

    # Mouth
    draw.line([(s(64), s(73)), (s(55), s(80))], fill=dark_or, width=max(1, s(2)))
    draw.line([(s(64), s(73)), (s(73), s(80))], fill=dark_or, width=max(1, s(2)))

    # Whiskers
    draw.line([(s(14), s(67)), (s(56), s(69))], fill=dark_or, width=1)
    draw.line([(s(14), s(74)), (s(56), s(73))], fill=dark_or, width=1)
    draw.line([(s(114), s(67)), (s(72), s(69))], fill=dark_or, width=1)
    draw.line([(s(114), s(74)), (s(72), s(73))], fill=dark_or, width=1)

    # Paws
    draw.ellipse([s(30), s(110), s(58), s(127)], fill=orange, outline=dark_or, width=1)
    draw.ellipse([s(70), s(110), s(98), s(127)], fill=orange, outline=dark_or, width=1)
    for ox in [s(8), s(13)]:
        draw.line([(s(30)+ox, s(113)), (s(30)+ox, s(124))], fill=dark_or, width=1)
        draw.line([(s(70)+ox, s(113)), (s(70)+ox, s(124))], fill=dark_or, width=1)

    # Tail
    for i in range(55):
        t = i / 55.0
        tx = s(100 + 24 * math.sin(t * math.pi * 1.4))
        ty = s(82 + 44 * t)
        r = max(1, s(6 - 4 * t))
        if 0 <= tx < size and 0 <= ty < size:
            draw.ellipse([tx - r, ty - r, tx + r, ty + r], fill=orange)

    # Tabby stripes on body
    for ys in [s(80), s(88), s(96)]:
        draw.arc([s(34), ys - s(4), s(94), ys + s(4)], 180, 0, fill=dark_or, width=max(1, s(2)))

    img.save(filename)
    print(f"Saved {filename} ({size}x{size})")


if __name__ == "__main__":
    create_cat_image()
