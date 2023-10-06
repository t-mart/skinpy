# mc-skin

<p align="center">
  <img src="./examples/render/lab_space.png" alt="isometric render" height=300>
</p>

A Python library for Minecraft skins.

- Lets you use 3D coordinates to get/set skin pixel color
- Generates skin images for use in-game
- Produces isometric renderings of your skin

## Quickstart

### Creating/Loading/Saving a skin

```python
from pathlib import Path
from mc_skin import Skin

# make a new skin
new_skin = Skin.new()
new_skin.to_image().save("blank.png")

# or load a skin from disk
loaded_skin = Skin.from_path(Path("my_skin.png"))
loaded_skin.to_image().save("copy.png")
```

### Rendering Isometric Images

```python
from pathlib import Path
from mc_skin import Skin, Perspective

skin = Skin.from_path(Path("steve.png"))

# create a perspective from which to view the render
perspective = Perspective(
  x="left",
  y="front",
  z="up",
  scaling_factor=5, # bigger numbers mean bigger image
)

# save the render
skin.to_isometric_image(perspective).save("render.png")
```

Outputted file:

![outputted file](./docs/steve-render.png)

### Pixel Indexing

```python
from pathlib import Path
from mc_skin import Skin

skin = Skin.from_path(Path("steve.png"))
magenta = (211, 54, 130, 255)  # RGBA

# get/set using entire skin's 3D coordinates
color = skin.get_color(4, 2, 0, "front") # somewhere on steve's right foot
print(f"Skin pixel at (4, 2, 0, 'front') was {color}")
skin.set_color(4, 2, 0, "front", magenta)

# get/set on just a head. coordinates become relative to just that part
color = skin.head.get_color(0, 1, 2, "left")
print(f"Head pixel at (0, 1, 2, 'left') was {color}")
skin.head.set_color(0, 1, 2, "left", magenta)

# or finally, just on one face. faces only have two dimensions
# NOTE: Face does not necessarily mean just a character's face! It just
# refers to the side of a cubiod, which all body parts are in Minecraft
color = skin.left_arm.up.get_color(5, 5)
print(f"Left arm up pixel at (5, 5) was {color}")
skin.head.set_color(0, 1, 2, "left", magenta)

skin.to_image().save("some_magenta.png")
```

Here's an animated visualization of equivalent ways to access a certain pixel:

![indexing](examples/render/steve-index.gif)

(This image was made with `examples/index.py`.)

### Pixel Enumeration

```python
from pathlib import Path
from mc_skin import Skin

skin = Skin.from_path(Path("steve.png"))

for (x, y, z), body_part_id, face_id, color in skin.enumerate_color():
  print(f"{x=}, {y=}, {z=}, {body_part_id=}, {face_id=}, {color=}")

for (x, y, z), face_id, color in skin.torso.enumerate_color():
  print(f"{x=}, {y=}, {z=}, {face_id=}, {color=}")

for (x, y), face_id, color in skin.torso.back.enumerate_color():
  print(f"{x=}, {y=}, {color=}")
```

## Coordinate system

mc-skin uses a coordinate system with the origin at the left-down-front of the
skin **from the perspective of an observer looking at the skin**.

![coordinate system](./docs/coordsys.png)

## `FaceId`

In some methods, a `FaceId` type is asked for or provided. These are string literals:

- `up`
- `down`
- `left`
- `right`
- `front`
- `back`

## `BodyPartId`

Similarly, body parts are string literals under `BodyPartId`:

- `head`
- `torso`
- `right_arm`
- `left_arm`
- `right_leg`
- `left_leg`

Body parts that are "left" or "right" follow the same perspective as before: from the observer's point of view.

## Examples

You can find the skins/renders, and the code to produced them, in
[examples](./examples).
