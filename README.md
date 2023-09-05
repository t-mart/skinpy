# mc-skin

![lab color skin](./docs/lab.png)

A Python modeler for Minecraft skins. Knows how to translate a skin image to a
3D space and vice versa. Once in 3D, you can apply all sorts of cool
mathematical functions with color spaces.

The above image was generated with the following code:

```python
import numpy as np
import skimage.color

from mc_skin.skin import Skin

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

    skin.get_pil_image().save("lab_space.png")
```

You can grab this skin for use (and others) by looking in
[examples/skins](examples/skins).
