"""
Generate some example skins
"""
from pathlib import Path

from mc_skin import Skin
import numpy as np
import skimage.color

# we want generate the skins to the test input path
OUTPUT_PATH = Path(__file__).parent / "skins"


def generate_white():
    skin = Skin.new()
    for _, _, _, color in skin.enumerate_color():
        color[:] = 255
    skin.get_pil_image().save(OUTPUT_PATH / "white.png")


def generate_lr_gradient():
    skin = Skin.new()
    gradient = np.linspace(0, 255, skin.shape[0])
    for (x, _, _), _, _, color in skin.enumerate_color():
        color[:3] = gradient[x]
        color[3] = 255
    skin.get_pil_image().save(OUTPUT_PATH / "lr_gradient.png")


def generate_tb_gradient():
    skin = Skin.new()
    gradient = np.linspace(0, 255, skin.shape[2])
    for (_, _, z), _, _, color in skin.enumerate_color():
        color[:3] = gradient[z]
        color[3] = 255
    skin.get_pil_image().save(OUTPUT_PATH / "tb_gradient.png")


def generate_fb_gradient():
    skin = Skin.new()
    gradient = np.linspace(0, 255, skin.shape[1])
    for (_, y, _), _, _, color in skin.enumerate_color():
        color[:3] = gradient[y]
        color[3] = 255
    skin.get_pil_image().save(OUTPUT_PATH / "fb_gradient.png")


def generate_hsv_space():
    skin = Skin.new()

    x_max, y_max, z_max = skin.shape[:3]
    center = np.array([x_max / 2, y_max / 2])
    dist_max = max(x_max, y_max) / 2

    for (x, y, z), _, _, color in skin.enumerate_color():
        hue = (np.arctan2(y - center[1], x - center[0]) + np.pi) / (2 * np.pi)

        saturation = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) / dist_max
        saturation = np.clip(saturation, 0, 1)  # floating point error fix

        value = z / z_max

        r, g, b = skimage.color.hsv2rgb([hue, saturation, value]) * 255  # type: ignore
        color[:3] = (r, g, b)
        color[3] = 255

    skin.get_pil_image().save(OUTPUT_PATH / "hsv_space.png")


def generate_lab_space():
    """
    Map the LAB color spaces onto a skin. The components for L, A, and B come
    from the z, x, and y dimensions of each voxel, respectively.
    """
    skin = Skin.new()

    x_max, y_max, z_max = skin.shape[:3]

    l_space = np.linspace(0, 100, z_max)
    a_space = np.linspace(-128, 127, x_max)
    b_space = np.linspace(127, -128, y_max)

    for (x, y, z), _, _, color in skin.enumerate_color():
        lab = [l_space[z], a_space[x], b_space[y]]

        rgb = skimage.color.lab2rgb([lab]) * 255  # type: ignore
        color[:3] = rgb
        color[3] = 255

    skin.get_pil_image().save(OUTPUT_PATH / "lab_space.png")


def generate_luv_space():
    skin = Skin.new()

    l_space, u_space, v_space = [
        np.linspace(20, 100, skin.shape[2]),  # there's some weirdness at low L
        np.linspace(-128, 127, skin.shape[0]),
        np.linspace(-128, 127, skin.shape[1]),
    ]

    for (x, y, z), _, _, color in skin.enumerate_color():
        luv = [l_space[z], u_space[x], v_space[y]]
        rgb: np.ndarray = (skimage.color.luv2rgb([luv]) * 255)[0]  # type: ignore
        color[:3] = rgb
        color[3] = 255

    skin.get_pil_image().save(OUTPUT_PATH / "luv_space.png")


def generate_xyz_space():
    skin = Skin.new()

    x_space, y_space, z_space = [np.linspace(0, 1, dim) for dim in skin.shape[:3]]

    for (x, y, z), _, _, color in skin.enumerate_color():
        xyz = [x_space[x], y_space[y], z_space[z]]
        rgb = skimage.color.xyz2rgb([xyz])  # type: ignore
        color[:3] = rgb[0] * 255
        color[3] = 255

    skin.get_pil_image().save(OUTPUT_PATH / "xyz_space.png")


if __name__ == "__main__":
    for file in OUTPUT_PATH.glob("*.png"):
        file.unlink()

    funcs = [
        generate_white,
        generate_lr_gradient,
        generate_tb_gradient,
        generate_fb_gradient,
        generate_hsv_space,
        generate_lab_space,
        generate_luv_space,
        generate_xyz_space,
    ]

    for func in funcs:
        print(f"{func.__name__}...")
        func()

    print("Done!")

