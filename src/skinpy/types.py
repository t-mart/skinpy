from typing import Literal, Union
from pathlib import Path

import numpy as np

# x, y, color
ImageColor = np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]

# (x, y, z)
R3 = tuple[int, int, int]

# (x, y)
R2 = tuple[int, int]

# (r, g, b, a)
RGBA = tuple[int, int, int, int]

# face identifiers
XFaceId = Literal["left", "right"]
YFaceId = Literal["front", "back"]
ZFaceId = Literal["up", "down"]
FaceId = Union[XFaceId, YFaceId, ZFaceId]

# body part names
BodyPartId = Literal[
    "head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"
]

PolygonPoints = tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
]

StrPath = Union[str, Path]
