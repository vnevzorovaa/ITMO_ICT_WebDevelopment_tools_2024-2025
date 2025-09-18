import time
from multiprocessing import Process, Manager

MAX_N = 10**8
NUM_WORKERS = 4

def calculate_sum(start: int, end: int) -> int:
    s = 0
    for i in range(start, end + 1):
        s += i
    return s


def worker(start: int, end: int, results: list, idx: int):
    results[idx] = calculate_sum(start, end)


def main():
    segment = MAX_N // NUM_WORKERS
    with Manager() as manager:
        results = manager.list([0] * NUM_WORKERS)
        procs = []

        t0 = time.perf_counter()
        for i in range(NUM_WORKERS):
            lo = i * segment + 1
            hi = (i + 1) * segment if i < NUM_WORKERS - 1 else MAX_N
            p = Process(target=worker, args=(lo, hi, results, i))
            procs.append(p)
            p.start()

        for p in procs:
            p.join()

        total = sum(results)
        elapsed = time.perf_counter() - t0
        print(f"[multiprocessing] Sum= {total}, Time= {elapsed:.3f}s")

if __name__ == '__main__':
    main()