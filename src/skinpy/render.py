from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Sequence

from PIL import ImageDraw, Image
import numpy as np
from attrs import frozen


if TYPE_CHECKING:
    from skinpy.types import (
        RGBA,
        XFaceId,
        YFaceId,
        ZFaceId,
        FaceId,
        R3,
        PolygonPoints,
        ImageColor,
    )


@frozen
class Polygon:
    points: PolygonPoints
    color: RGBA

    def draw(self, draw: ImageDraw.ImageDraw) -> None:
        draw.polygon(
            xy=[tuple(p) for p in self.points],  # type: ignore
            fill=tuple(self.color),  # type: ignore
        )

    def with_offset(self, offset: tuple[int, int]) -> Polygon:
        offsetted = (
            (self.points[0][0] + offset[0], self.points[0][1] + offset[1]),
            (self.points[1][0] + offset[0], self.points[1][1] + offset[1]),
            (self.points[2][0] + offset[0], self.points[2][1] + offset[1]),
            (self.points[3][0] + offset[0], self.points[3][1] + offset[1]),
        )
        return Polygon(
            offsetted,
            self.color,
        )

    @property
    def min_x(self) -> int:
        return min(p[0] for p in self.points)

    @property
    def max_x(self) -> int:
        return max(p[0] for p in self.points)

    @property
    def min_y(self) -> int:
        return min(p[1] for p in self.points)

    @property
    def max_y(self) -> int:
        return max(p[1] for p in self.points)


COS_30 = np.cos(np.pi / 6)


@frozen(kw_only=True)
class Perspective:
    x: XFaceId
    y: YFaceId
    z: ZFaceId
    scaling_factor: int = 10

    @classmethod
    def new(
        cls,
        *,
        x: XFaceId,
        y: YFaceId,
        z: ZFaceId,
        scaling_factor: int = 10,
    ) -> Perspective:
        return cls(
            x=x,
            y=y,
            z=z,
            scaling_factor=scaling_factor,
        )

    @property
    def x_dir(self) -> int:
        return 1 if self.x == "left" else -1

    @property
    def y_dir(self) -> int:
        return 1 if self.y == "front" else -1

    @property
    def z_dir(self) -> int:
        return 1 if self.z == "up" else -1

    def map_iso(self, x: int, y: int, z: int) -> tuple[int, int]:
        # "p" for projected, i guess
        xp = x * self.x_dir * self.scaling_factor
        yp = y * self.y_dir * self.scaling_factor
        zp = z * self.z_dir * self.scaling_factor

        iso_x = (xp - yp) * COS_30
        iso_y = -(((xp + yp) / 2) + zp)

        points = tuple(np.array((iso_x, iso_y)).round().astype(int).tolist())

        return (points[0], points[1])

    def make_polygon(
        self,
        x: int,
        y: int,
        z: int,
        face_id: FaceId,
        color: RGBA,
    ) -> Polygon:
        if face_id in ("front", "back"):
            if face_id == "front":
                y_offset = y
            else:
                y_offset = y + 1
            points = (
                self.map_iso(x, y_offset, z),
                self.map_iso(x + 1, y_offset, z),
                self.map_iso(x + 1, y_offset, z + 1),
                self.map_iso(x, y_offset, z + 1),
            )
        elif face_id in ("left", "right"):
            if face_id == "left":
                x_offset = x
            else:
                x_offset = x + 1
            points = (
                self.map_iso(x_offset, y, z),
                self.map_iso(x_offset, y + 1, z),
                self.map_iso(x_offset, y + 1, z + 1),
                self.map_iso(x_offset, y, z + 1),
            )
        else:
            if face_id == "down":
                z_offset = z
            else:  # down
                z_offset = z + 1
            points = (
                self.map_iso(x, y, z_offset),
                self.map_iso(x + 1, y, z_offset),
                self.map_iso(x + 1, y + 1, z_offset),
                self.map_iso(x, y + 1, z_offset),
            )

        return Polygon(
            points,
            color,
        )

    @property
    def visible_faces(self) -> tuple[FaceId, FaceId, FaceId]:
        return (self.x, self.y, self.z)


def get_iso_polys(
    enumerator: Iterable[tuple[R3, FaceId, ImageColor]],
    perspective: Perspective | None = None,
) -> Iterable[Polygon]:
    if perspective is None:
        perspective = Perspective.new(
            x="left",
            y="front",
            z="up",
            scaling_factor=10,
        )

    # Collect the polygons for each face
    for (x, y, z), face_id, color in enumerator:
        if face_id in perspective.visible_faces:
            color_t = (
                color[0],
                color[1],
                color[2],
                color[3],
            )
            poly = perspective.make_polygon(
                x,
                y,
                z,
                face_id,
                color_t,
            )
            yield poly


def render_isometric(
    polys: Sequence[Polygon],
    background_color: tuple[int, int, int, int] | None = None,
) -> Image.Image:
    # get bounding box
    min_x = min(poly.min_x for poly in polys)
    max_x = max(poly.max_x for poly in polys)
    min_y = min(poly.min_y for poly in polys)
    max_y = max(poly.max_y for poly in polys)
    img_width = max_x - min_x
    img_height = max_y - min_y

    img = Image.new(
        "RGBA",
        (img_width, img_height),
        color=background_color,  # type: ignore
    )
    draw = ImageDraw.Draw(img)

    for poly in polys:
        offset_poly = poly.with_offset((-min_x, -min_y))
        offset_poly.draw(draw)

    return img
