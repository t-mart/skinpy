from pathlib import Path

from PIL import Image, ImageOps, ImageDraw, ImageFont
from mc_skin import Skin, Perspective

FONT_SIZE = SCALING_FACTOR = 40
FONT = ImageFont.truetype("courbd.ttf", FONT_SIZE)  # Courier New
TEXT_COLOR = (211, 54, 130, 255)  # magenta
BACKGROUND_COLOR = (255, 255, 255, 255)  # white
SOURCE_PATH = Path(__file__).parent / "steve.png"
DEST_PATH = Path(__file__).parent / "render/steve-index.gif"
PERSPECTIVE = Perspective.new(
    x="left",
    y="front",
    z="up",
    scaling_factor=SCALING_FACTOR,
)

if __name__ == "__main__":
    skin = Skin.from_path(SOURCE_PATH)
    frames: list[Image.Image] = []

    for (x, y, z), body_part_id, face_id, color in skin.enumerate_color():
        # don't highlight pixels we can't see for demo
        if (
            face_id not in PERSPECTIVE.visible_faces
            or (body_part_id == "right_arm" and face_id == "left")
            or (body_part_id == "torso" and face_id in ("left", "up"))
            or (body_part_id == "left_leg" and face_id == "up")
            or (body_part_id == "right_leg" and face_id in ("left", "up"))
        ):
            continue
        old_color = color.copy()
        old_color_hex = f"#{old_color[0]:02x}{old_color[1]:02x}{old_color[2]:02x}"
        color[:3] = 255 - color[:3]
        frame = skin.to_isometric_image(
            perspective=PERSPECTIVE, background_color=BACKGROUND_COLOR
        )

        body_part = skin.get_body_part_for_id(body_part_id)
        body_part_coord = (
            x - body_part.model_origin[0],
            y - body_part.model_origin[1],
            z - body_part.model_origin[2],
        )

        face = body_part.get_face_for_id(face_id)
        if face_id in ("up", "down"):
            face_coord = (body_part_coord[0], body_part_coord[1])
        elif face_id in ("left", "right"):
            face_coord = (body_part_coord[1], body_part_coord[2])
        else:
            face_coord = (body_part_coord[0], body_part_coord[2])

        lines = [
            f"skin.get_color({x}, {y}, {z}, {face_id})",
            (
                f"skin.{body_part_id}."
                f"get_color({body_part_coord[0]}, {body_part_coord[1]}, "
                f"{body_part_coord[2]}, {face_id})"
            ),
            (
                f"skin.{body_part_id}.{face_id}."
                f"get_color({face_coord[0]}, {face_coord[1]})"
            ),
            f"color = {old_color_hex}",
        ]

        # space for each line with space between
        line_height = int(FONT_SIZE * 1.25)
        bottom_border_sz = line_height * len(lines)

        def get_line_width(line: str) -> int:
            return FONT.getbbox(line)[2]  # type: ignore

        # find the longest line, and roughly 1em to each side
        # max_line_width = (
        #     max(get_line_width(line) for line in lines) + 2 * FONT_SIZE
        # )

        # worst case scenario
        max_line_width = get_line_width(
            "skin.left_arm.get_color(10, 10, 10, 'front')"
        ) + 2 * FONT_SIZE
        x_border_sz = max((max_line_width - frame.width) // 2, 0)

        # resize to make space
        frame = ImageOps.expand(
            frame,
            border=(x_border_sz, 0, x_border_sz, bottom_border_sz),
            fill=BACKGROUND_COLOR,
        )
        image_width, image_height = frame.size
        draw = ImageDraw.Draw(frame)

        for i, line in enumerate(lines):
            line_pos = (FONT_SIZE, image_height - line_height * (len(lines) - i))
            draw.text(line_pos, line, fill=TEXT_COLOR, font=FONT)  # type: ignore
            if line.startswith("color"):
                line_width = get_line_width(line)
                draw.rectangle(
                    (
                        line_pos[0] + line_width + FONT_SIZE,
                        line_pos[1] + 0,
                        line_pos[0] + line_width + 2 * FONT_SIZE,
                        line_pos[1] + FONT_SIZE,
                    ),
                    fill=tuple(old_color.tolist()),  # type: ignore
                    outline=(255, 255, 255),
                )

        frames.append(frame)
        color[:] = old_color

    DEST_PATH.parent.mkdir(exist_ok=True, parents=True)

    frames[0].save(
        DEST_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        include_color_table=True,
        loop=0,
    )
