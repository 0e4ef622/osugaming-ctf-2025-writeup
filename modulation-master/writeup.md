In this challenge, you are given an image of a matplotlib plot and you have 2 seconds to figure out
what ascii character it represents.

![Modulation master screenshot](./imgs/modulation-master-screenshot.png)

One look at this image and a quick google search tells us that basically, each section of the plot
represents a bit and we just need to figure out for each section whether it's a 0 or 1. Since it's
always an **ASCII letter**, that means the first two bits are always 0 and 1, so we have an
easy reference to compare against.

Decoding
========

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
| 0 | Score: 1934.87<br>![](./imgs/diffs/diff2_0.png) | Score: 1934.69<br>![](./imgs/diffs/diff3_0.png) | Score: 1934.11<br>![](./imgs/diffs/diff4_0.png) | Score: **961.08**<br>![](./imgs/diffs/diff5_0.png) | Score: **1145.86**<br>![](./imgs/diffs/diff6_0.png) | Score: **1314.66**<br>![](./imgs/diffs/diff7_0.png) |
| 1 | Score: **192.31**<br>![](./imgs/diffs/diff2_1.png) | Score: **384.91**<br>![](./imgs/diffs/diff3_1.png) | Score: **577.03**<br>![](./imgs/diffs/diff4_1.png) | Score: 1932.62<br>![](./imgs/diffs/diff5_1.png) | Score: 1932.71<br>![](./imgs/diffs/diff6_1.png) | Score: 1933.55<br>![](./imgs/diffs/diff7_1.png) |

Although plots get misaligned for the later bits, the scores look good so we'll keep going for now.
(I wasn't looking at these difference images when solving at the time).

Computing the final ASCII letter and putting it all together, we have our full `decode`
function below. It takes about 1 second to run, which is well within the 2 second timeout.

```py
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

    value = 0b01
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
        if score0 < score1:
            value *= 2
        else:
            value = 2 * value + 1

    return chr(value)
```

Interacting with the website
============================

Playing the game with the Network tab of the browser DevTools open, we can see that the entire
game happens through a websocket. The client sends the answer, and the server responds with a
message and the next image.

![DevTools screenshot](./imgs/network.png)

So we just have to hook up our `decode` function to this websocket.

```py
import asyncio
from websockets.asyncio.client import ClientConnection, connect as ws_connect

URL = "wss://modulation-master-48f4721712c6.instancer.sekai.team/echo"


async def run(ws: ClientConnection):
    await ws.send("start")

    i = 0
    while True:
        msg = await ws.recv()
        if isinstance(msg, str):
            print(f"Got message {msg!r}")
            continue

        print(f"got img")
        with open(f"imgs/{i}.png", "wb") as f:
            f.write(msg)
        resp = decode(f"imgs/{i}.png")
        print("Sending", resp)
        await ws.send(resp)
        i += 1


async def main():
    async with ws_connect(URL) as ws:
        await run(ws)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        asyncio.run(main())
    else:
        start = time.perf_counter()
        print(decode(sys.argv[1], debug=True))
        end = time.perf_counter()
        print(f"Took {end - start}")
```

And this is good enough to pass the challenge and get the flag!

```
Got message 'You have got 96/100 correct (+1), 8/10 wrong.'
got img
Sending L
Got message 'You have got 97/100 correct (+1), 8/10 wrong.'
got img
Sending r
Got message 'You have got 98/100 correct (+1), 8/10 wrong.'
got img
Sending J
Got message 'You have got 99/100 correct (+1), 8/10 wrong.'
got img
Sending D
Got message 'You have got 100/100 correct (+1), 8/10 wrong.'
Got message "Congratulations! Here's your flag: osu{I_h0p3_y0u_d1dn't_u53_LLM_2_s0Lv3_7H1S}"
Traceback (most recent call last):
  File "/home/_/osu-ctf-2025/ppc/modulation-master/a.py", line 78, in <module>
    asyncio.run(main())
    ~~~~~~~~~~~^^^^^^^^
  File "/usr/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "/usr/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "/home/_/osu-ctf-2025/ppc/modulation-master/a.py", line 73, in main
    await run(ws)
  File "/home/_/osu-ctf-2025/ppc/modulation-master/a.py", line 57, in run
    msg = await ws.recv()
          ^^^^^^^^^^^^^^^
  File "/home/_/osu-ctf-2025/ppc/modulation-master/.venv/lib/python3.13/site-packages/websockets/asyncio/connection.py", line 322, in recv
    raise self.protocol.close_exc from self.recv_exc
websockets.exceptions.ConnectionClosedOK: received 1000 (OK); then sent 1000 (OK)
```

Perfecting the solution
=======================

Ok, so we got the flag, but our solution isn't perfect. We still got 8 out of 10 wrong! What gives?

## Image size

First of all, not all of the images are the same size! Here's an example:

![Bigger plot](./imgs/funny.png)

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - | - |
| ![chunk 0](./imgs/funnychunks/0.png) | ![chunk 1](./imgs/funnychunks/1.png) | ![chunk 2](./imgs/funnychunks/2.png) | ![chunk 3](./imgs/funnychunks/3.png) | ![chunk 4](./imgs/funnychunks/4.png) | ![chunk 5](./imgs/funnychunks/5.png) | ![chunk 6](./imgs/funnychunks/6.png) | ![chunk 7](./imgs/funnychunks/7.png) |

|   | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - |
| 0 | Score: **1694.0843**<br>![](./imgs/funnydiffs/diff2_0.png) | Score: 5643.0391<br>![](./imgs/funnydiffs/diff3_0.png) | Score: **2775.7705**<br>![](./imgs/funnydiffs/diff4_0.png) | Score: **3311.6662**<br>![](./imgs/funnydiffs/diff5_0.png) | Score: 5644.8464<br>![](./imgs/funnydiffs/diff6_0.png) | Score: 5638.2059<br>![](./imgs/funnydiffs/diff7_0.png)
| 1 | Score: 5402.6928<br>![](./imgs/funnydiffs/diff2_1.png) | Score: **1155.0264**<br>![](./imgs/funnydiffs/diff3_1.png) | Score: 5408.5432<br>![](./imgs/funnydiffs/diff4_1.png) | Score: 5186.7628<br>![](./imgs/funnydiffs/diff5_1.png) | Score: **2882.4253**<br>![](./imgs/funnydiffs/diff6_1.png) | Score: **3595.7317**<br>![](./imgs/funnydiffs/diff7_1.png)

Funnily enough, the spacing between each bit is still the same and the bits aren't shifted by much
so our `decode` function still works.

## Alignment

I mentioned earlier that the images get misaligned the further right we go. It turns out that this
is just enough to sometimes confuse our `decode` function. This is the main source of wrong answers.
Here's an example:

![Bad example](./imgs/evil.png)

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - | - |
| ![chunk 0](./imgs/evilchunks/0.png) | ![chunk 1](./imgs/evilchunks/1.png) | ![chunk 2](./imgs/evilchunks/2.png) | ![chunk 3](./imgs/evilchunks/3.png) | ![chunk 4](./imgs/evilchunks/4.png) | ![chunk 5](./imgs/evilchunks/5.png) | ![chunk 6](./imgs/evilchunks/6.png) | ![chunk 7](./imgs/evilchunks/7.png) |

|   | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - |
| 0 | Score: 3059.2261<br>![](./imgs/evildiffs/diff2_0.png) | Score: **0.0000**<br>![](./imgs/evildiffs/diff3_0.png) | Score: **0.0000**<br>![](./imgs/evildiffs/diff4_0.png) | Score: 3059.0292<br>![](./imgs/evildiffs/diff5_0.png) | Score: **0.0000**<br>![](./imgs/evildiffs/diff6_0.png) | Score: **3057.7494(!)**<br>![](./imgs/evildiffs/diff7_0.png)
| 1 | Score: **577.1133**<br>![](./imgs/evildiffs/diff2_1.png) | Score: 3058.8163<br>![](./imgs/evildiffs/diff3_1.png) | Score: 3058.8163<br>![](./imgs/evildiffs/diff4_1.png) | Score: **2307.7155**<br>![](./imgs/evildiffs/diff5_1.png) | Score: 3058.8163<br>![](./imgs/evildiffs/diff6_1.png) | Score: 3431.3129<br>![](./imgs/evildiffs/diff7_1.png)

The last bit is wrong, it should be a 1 but 0 has the lower score. We could try fixing this by
manually specifying where each bit starts, instead of first bit and width, but here's a dumber
idea: just blur the image.

```py
def decode(file: str, *, debug: bool = False) -> str:
    im: np.ndarray = ski.io.imread(file, as_gray=True)
    im = ski.filters.gaussian(im, sigma=3)  # apply blur
    ...
```

Now we can tolerate the slight misalignment and still get the right answer, 100% of the time!

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - | - |
| ![chunk 0](./imgs/fixedchunks/0.png) | ![chunk 1](./imgs/fixedchunks/1.png) | ![chunk 2](./imgs/fixedchunks/2.png) | ![chunk 3](./imgs/fixedchunks/3.png) | ![chunk 4](./imgs/fixedchunks/4.png) | ![chunk 5](./imgs/fixedchunks/5.png) | ![chunk 6](./imgs/fixedchunks/6.png) | ![chunk 7](./imgs/fixedchunks/7.png) |

|   | 2 | 3 | 4 | 5 | 6 | 7 |
| - | - | - | - | - | - | - |
| 0 | Score: 2976.0589<br>![](./imgs/fixeddiffs/diff2_0.png) | Score: **136.8701**<br>![](./imgs/fixeddiffs/diff3_0.png) | Score: **137.0971**<br>![](./imgs/fixeddiffs/diff4_0.png) | Score: 2988.5142<br>![](./imgs/fixeddiffs/diff5_0.png) | Score: **126.7435**<br>![](./imgs/fixeddiffs/diff6_0.png) | Score: 3051.0989<br>![](./imgs/fixeddiffs/diff7_0.png)
| 1 | Score: **167.7059**<br>![](./imgs/fixeddiffs/diff2_1.png) | Score: 2939.6763<br>![](./imgs/fixeddiffs/diff3_1.png) | Score: 2923.9143<br>![](./imgs/fixeddiffs/diff4_1.png) | Score: **601.8918**<br>![](./imgs/fixeddiffs/diff5_1.png) | Score: 2937.7294<br>![](./imgs/fixeddiffs/diff6_1.png) | Score: **943.9358**<br>![](./imgs/fixeddiffs/diff7_1.png)
