from mc_skin.skin import Skin

if __name__ == "__main__":
    examples = [
        ("blank", Skin.new()),
        ("white", Skin.white()),
        ("grayscale_gradient", Skin.grayscale_gradient()),
        ("lab", Skin.lab()),
        ("cubehelix", Skin.cubehelix()),
        ("hsv", Skin.hsv()),
    ]

    for name, skin in examples:
        skin.to_image().save(f"examples/{name}.png")
        print(f"Saved {name}.png")
