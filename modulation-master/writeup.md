In this challenge, you are given an image of a matplotlib plot and you have 2 seconds to figure out
what ascii character it represents.

![Modulation master screenshot](./imgs/modulation-master-screenshot.png)

One look at this image and a quick google search tells us that basically, each section of the plot
represents a bit and we just need to figure out for each section whether it's a 0 or 1. Since it's
always an **ASCII letter**, that means the first two bits are always 0 and 1, so we have an
easy reference to compare against.

Let's start by figuring out where each bit is (I just used GIMP for this), and chopping them out.

```py
import skimage as ski
import numpy as np

bottom_coord = 417
top_coord = 32
left_coord = 60
bit_width = 302 - 60

def decode(file: str, *, debug: bool = False) -> str:
    im: np.ndarray = ski.io.imread(file, as_gray=True)

    bit_slices = [
        im[
            top_coord + 2 : bottom_coord - 1,
            left_coord + i * bit_width + 2 : left_coord + (i + 1) * bit_width - 1,
        ]
        for i in range(8)
    ]

    if debug:
        for i, s in enumerate(bit_slices):
            ski.io.imsave(f"chunks/{i}.png", ski.util.img_as_ubyte(s))

```

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - | - |
| ![chunk 0](./imgs/chunks/0.png) | ![chunk 1](./imgs/chunks/1.png) | ![chunk 2](./imgs/chunks/2.png) | ![chunk 3](./imgs/chunks/3.png) | ![chunk 4](./imgs/chunks/4.png) | ![chunk 5](./imgs/chunks/5.png) | ![chunk 6](./imgs/chunks/6.png) | ![chunk 7](./imgs/chunks/7.png) |

Next step is to somehow compare each image against the first and second image. A quick and easy way
to do this is to just subtract the images, take the absolute value, and then sum all the pixels to
get a score. The lower the score, the better they match.

```py
    for i, s in enumerate(bit_slices[2:]):
        i += 2
        diff0 = abs(s - bit_slices[0])
        diff1 = abs(s - bit_slices[1])
        score0 = np.sum(diff0)
        score1 = np.sum(diff1)
        if debug:
            print(score0, score1)
            ski.io.imsave(f"chunks/diff{i}_0.png", ski.util.img_as_ubyte(diff0))
            ski.io.imsave(f"chunks/diff{i}_1.png", ski.util.img_as_ubyte(diff1))
```

|   | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - |
| 0 | Score: 0<br>![diff2_0](./imgs/diffs/diff2_0.png) | Score: 0<br>![diff3_0](./imgs/diffs/diff3_0.png) | Score: 2153.38<br>![diff4_0](./imgs/diffs/diff4_0.png) | Score: 0<br>![diff5_0](./imgs/diffs/diff5_0.png) | Score: 0<br>![diff6_0](./imgs/diffs/diff6_0.png) | Score: 2152.44<br>![diff7_0](./imgs/diffs/diff7_0.png) |
| 1 | Score: 2153.72<br>![diff2_1](./imgs/diffs/diff2_1.png) | Score: 2153.72<br>![diff3_1](./imgs/diffs/diff3_1.png) | Score: 1154.24<br>![diff4_1](./imgs/diffs/diff4_1.png) | Score: 2153.72<br>![diff5_1](./imgs/diffs/diff5_1.png) | Score: 2153.72<br>![diff6_1](./imgs/diffs/diff6_1.png) | Score: 2289.86<br>![diff7_1](./imgs/diffs/diff7_1.png) |
