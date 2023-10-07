from typing import Literal
from pathlib import Path

import numpy as np

# x, y, color
type ImageColor = np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]

# (x, y, z)
type R3 = tuple[int, int, int]

# (x, y)
type R2 = tuple[int, int]

# (r, g, b, a)
type RGBA = tuple[int, int, int, int]

# face identifiers
type XFaceId = Literal["left", "right"]
type YFaceId = Literal["front", "back"]
type ZFaceId = Literal["up", "down"]
type FaceId = XFaceId | YFaceId | ZFaceId

# body part names
type BodyPartId = Literal[
    "head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"
]

type PolygonPoints = tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
]

type StrPath = str | Path
