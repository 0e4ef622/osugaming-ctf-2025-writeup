# Original solution code

import sys
import time
import asyncio
from websockets.asyncio.client import ClientConnection, connect as ws_connect
import skimage as ski
import numpy as np

URL = "wss://modulation-master-36589c905cdd.instancer.sekai.team/echo"

bottom_coord = 417
top_coord = 32
left_coord = 60
bit_width = 302 - 60

def decode(file: str) -> str:
    im: np.ndarray = ski.io.imread(file)
    im = ski.color.rgba2rgb(im)
    im = ski.color.rgb2gray(im)

    bit_slices = [im[top_coord + 2 : bottom_coord - 1, left_coord + i*bit_width + 2 : left_coord + (i+1)*bit_width - 1] for i in range(8)]

    value = 0b01
    for s in bit_slices[2:]:
        diff0 = np.sum(abs(s - bit_slices[0]))
        diff1 = np.sum(abs(s - bit_slices[1]))
        if diff0 < diff1:
            value *= 2
        else:
            value = 2*value + 1

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
    asyncio.run(main())
    # start = time.perf_counter()
    # print(decode(sys.argv[1]))
    # end = time.perf_counter()
    # print(f"Took {end - start}")
