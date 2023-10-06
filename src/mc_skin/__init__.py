# We use "Thing as Thing" syntax here intentionally:
# > This tells type checkers and other tools that Thing is not meant to be a
# > private internal usage within the file but instead is meant to be a public
# > re-export of the symbol.
# See https://github.com/microsoft/pylance-release/issues/856#issuecomment-763793949

from mc_skin.skin import (
    Skin as Skin,
    BodyPart as BodyPart,
    Face as Face,
    UnmappedVoxelError as UnmappedVoxelError,
)

from mc_skin.render import (
    Perspective as Perspective,
)

from mc_skin.types import (
    ImageColor as ImageColor,
    R3 as R3,
    R2 as R2,
    RGBA as RGBA,
    XFaceId as XFaceId,
    YFaceId as YFaceId,
    ZFaceId as ZFaceId,
    FaceId as FaceId,
    BodyPartId as BodyPartId,
    PolygonPoints as PolygonPoints,
    StrPath as StrPath,
)
