import sys
import time
import asyncio
from websockets.asyncio.client import ClientConnection, connect as ws_connect
import skimage as ski
import numpy as np

URL = "wss://modulation-master-a2badbcff92a.instancer.sekai.team/echo"
bottom_coord = 417
top_coord = 32
left_coord = 60
bit_width = 302 - 60


def decode(file: str, *, debug: bool = False) -> str:
    im: np.ndarray = ski.io.imread(file, as_gray=True)
    im = ski.filters.gaussian(im, sigma=3)  # apply blur

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
