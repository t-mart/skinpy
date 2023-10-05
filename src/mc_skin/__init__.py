# We use "Foo as Foo" syntax here intentionally:
# > This tells type checkers and other tools that Thing is not meant to be a
# > private internal usage within the file but instead is meant to be a public
# > re-export of the symbol.
# See https://github.com/microsoft/pylance-release/issues/856#issuecomment-763793949
from mc_skin.skin import (
    Skin as Skin,
    BodyPart as BodyPart,
    Face as Face,
    FaceId as FaceId,
)
