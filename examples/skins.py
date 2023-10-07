"""
Generate some example skins
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal, ClassVar, cast, Any

from attr import frozen
import numpy as np
from colorspacious import cspace_convert  # type: ignore
from matplotlib import colors

from skinpy import Skin, FaceId, RGBA, Perspective

SKINS_PATH = Path(__file__).parent / "skins"
RENDER_PATH = Path(__file__).parent / "render"

PERSPECTIVE = Perspective(
    x="left",
    y="front",
    z="up",
    scaling_factor=40,
)


# collect all the functions that generate images with the @collect decorator
type ImgGenFn = Callable[[], None]
img_gen_fns: list[ImgGenFn] = []


def collect(func: ImgGenFn) -> ImgGenFn:
    img_gen_fns.append(func)
    return func


type Axis = Literal["x", "y", "z"]


@frozen
class FencedSpace:
    """
    A FencedSpace is similar to np.linspace, but each value is "fenced" by the
    edges on either side of it. For example, for a FencedSpace with of size n=3,
    the space would be:

    [
        0, # starting edge
        1, # 0th face
        2, # edge between 0th and 1st face
        3, # 1st face
        4, # edge between 1st and 2nd face
        5, # 2nd face
        6, # ending edge
    ]

    This is a space with 2n + 1 samples.

    This is kinda hard to explain, just roll with it. The idea is that we don't
    want the two faces at an edge (or the 3 faces at a corner) to have the same
    color. This gives our skins more color depth because we've increased the
    domain that we can sample from. Otherwise, all faces of a voxel at
    coordinate x, y, and z would have the same color.
    """

    space: np.ndarray[tuple[int], np.dtype[np.float16]]
    axis: Axis

    FACE_ID_MAP: ClassVar[dict[Axis, dict[FaceId, int]]] = {
        "x": {"left": -1, "right": 1},
        "y": {"front": -1, "back": 1},
        "z": {"down": -1, "up": 1},
    }

    @classmethod
    def new(cls, space_minmax: tuple[int, int], num: int, axis: Axis) -> FencedSpace:
        return cls(
            space=np.linspace(*space_minmax, num * 2 + 1),
            axis=axis,
        )

    def sample(self, i: int, face_id: FaceId) -> float:
        face_offset_map = self.FACE_ID_MAP.get(self.axis)
        base = i * 2 + 1
        if face_offset_map is not None and face_id in face_offset_map:
            offset = face_offset_map[face_id]
            return self.space[base + offset]
        return self.space[base]


def round_and_clip(arr: np.ndarray[Any, Any]) -> tuple[int, int, int]:
    return cast(
        tuple[int, int, int],
        tuple(arr.round().clip(0, 255).astype(np.uint8).tolist()),
    )


def convert(
    from_color: tuple[float, float, float],
    from_space: str,
    to_space: str,
) -> RGBA:
    """Helper for cspace_convert. Also rounds and clips the result."""
    r, g, b = cast(
        tuple[int, int, int],
        round_and_clip(
            cspace_convert(  # type: ignore
                from_color,
                from_space,
                to_space,
            )
        ),
    )
    return (r, g, b, 255)


@collect
def generate_white():
    skin = Skin.filled((255, 255, 255, 255))
    skin.to_image().save(SKINS_PATH / "white.png")


def generate_gradient(shape_idx: int, axis: Axis, file_name: str):
    skin = Skin.new()
    gradient = FencedSpace.new((0, 100), skin.shape[shape_idx] + 1, axis)
    for (x, y, z), _, face_id, _ in skin.enumerate_color():
        if axis == "x":
            sample = gradient.sample(x, face_id)
        elif axis == "y":
            sample = gradient.sample(y, face_id)
        else:
            sample = gradient.sample(z, face_id)

        # use CIELAB Lightness as the gradient. RGB is not perceptually uniform.
        lab = (
            sample,
            0,  # no chroma
            0,  # no chroma
        )

        rgba = convert(lab, "CIELab", "sRGB255")
        skin.set_color(x, y, z, face_id, rgba)
    skin.to_image().save(SKINS_PATH / file_name)
    skin.to_isometric_image(PERSPECTIVE).save(RENDER_PATH / file_name)


@collect
def generate_lr_gradient():
    generate_gradient(0, "x", "lr_gradient.png")


@collect
def generate_fb_gradient():
    generate_gradient(1, "y", "fb_gradient.png")


@collect
def generate_ud_gradient():
    generate_gradient(2, "z", "ud_gradient.png")


@collect
def generate_hsv_space():
    skin = Skin.new()

    x_max, y_max, z_max = skin.shape[:3]
    center = np.array([x_max / 2, y_max / 2])
    dist_max = max(x_max, y_max) / 2

    for (x, y, z), _, face_id, _ in skin.enumerate_color():
        hue = (np.arctan2(y - center[1], x - center[0]) + np.pi) / (2 * np.pi)

        saturation = (
            np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2) / dist_max
        ).clip(0, 1)

        value = z / z_max

        r, g, b = round_and_clip(
            colors.hsv_to_rgb(  # type: ignore
                [
                    hue,
                    saturation,
                    value,
                ]
            )
            * 255
        )
        skin.set_color(x, y, z, face_id, (r, g, b, 255))

    file_name = "hsv_space.png"
    skin.to_image().save(SKINS_PATH / file_name)
    skin.to_isometric_image(PERSPECTIVE).save(RENDER_PATH / file_name)


@collect
def generate_lab_space():
    """
    Map the LAB color spaces onto a skin. The components for L, A, and B come
    from the z, x, and y dimensions of each voxel, respectively.
    """
    skin = Skin.new()

    x_max, y_max, z_max = skin.shape[:3]

    l_space = FencedSpace.new((0, 100), z_max + 1, "z")
    a_space = FencedSpace.new((-128, 127), x_max + 1, "x")
    b_space = FencedSpace.new((127, -128), y_max + 1, "y")

    for (x, y, z), _, face_id, _ in skin.enumerate_color():
        lab = (
            l_space.sample(z, face_id),
            a_space.sample(x, face_id),
            b_space.sample(y, face_id),
        )

        rgba = convert(lab, "CIELab", "sRGB255")
        skin.set_color(x, y, z, face_id, rgba)

    file_name = "lab_space.png"
    skin.to_image().save(SKINS_PATH / file_name)
    skin.to_isometric_image(PERSPECTIVE).save(RENDER_PATH / file_name)


@collect
def generate_xyz100_space():
    skin = Skin.new()

    x_max, y_max, z_max = skin.shape[:3]

    x_space = FencedSpace.new((0, 100), x_max + 1, "x")
    y_space = FencedSpace.new((0, 100), y_max + 1, "y")
    z_space = FencedSpace.new((0, 100), z_max + 1, "z")

    for (x, y, z), _, face_id, _ in skin.enumerate_color():
        xyz = (
            x_space.sample(x, face_id),
            y_space.sample(y, face_id),
            z_space.sample(z, face_id),
        )

        rgba = convert(xyz, "XYZ100", "sRGB255")
        skin.set_color(x, y, z, face_id, rgba)

    file_name = "xyz100_space.png"
    skin.to_image().save(SKINS_PATH / file_name)
    skin.to_isometric_image(PERSPECTIVE).save(RENDER_PATH / file_name)


if __name__ == "__main__":
    SKINS_PATH.mkdir(exist_ok=True, parents=True)
    RENDER_PATH.mkdir(exist_ok=True, parents=True)

    for file in SKINS_PATH.glob("*.png"):
        file.unlink()

    for func in img_gen_fns:
        print(f"{func.__name__}...")
        func()

    print("Done!")
