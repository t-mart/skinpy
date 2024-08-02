from typing import Literal, Union, TypeAlias
from pathlib import Path

import numpy as np

# x, y, color
ImageColor: TypeAlias = np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]

# (x, y, z)
R3: TypeAlias = tuple[int, int, int]

# (x, y)
R2: TypeAlias = tuple[int, int]

# (r, g, b, a)
RGBA: TypeAlias = tuple[int, int, int, int]

# face identifiers
XFaceId: TypeAlias = Literal["left", "right"]
YFaceId: TypeAlias = Literal["front", "back"]
ZFaceId: TypeAlias = Literal["up", "down"]
FaceId: TypeAlias = Union[XFaceId, YFaceId, ZFaceId]

# body part names
BodyPartId: TypeAlias = Literal["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]

PolygonPoints: TypeAlias = tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
]

StrPath: TypeAlias = Union[str, Path]
