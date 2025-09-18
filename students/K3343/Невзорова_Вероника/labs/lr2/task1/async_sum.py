import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

MAX_N = 10**8
NUM_WORKERS = 4


def calculate_sum(start: int, end: int) -> int:
    s = 0
    for i in range(start, end + 1):
        s += i
    return s

async def main():
    loop = asyncio.get_running_loop()
    seg = MAX_N // NUM_WORKERS

    tasks = []
    for i in range(NUM_WORKERS):
        lo = i * seg + 1
        hi = (i + 1) * seg if i < NUM_WORKERS - 1 else MAX_N
        tasks.append(loop.run_in_executor(None, calculate_sum, lo, hi))

    t0 = time.perf_counter()
    results = await asyncio.gather(*tasks)
    total = sum(results)
    elapsed = time.perf_counter() - t0
    print(f"[asyncio] Sum= {total}, Time= {elapsed:.3f}s")

if __name__ == '__main__':
    asyncio.run(main())