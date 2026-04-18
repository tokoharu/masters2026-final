from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

N = 32
K = 2
C = 4
REGION = 16


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    return [[grid[n - 1 - i][j] for i in range(n)] for j in range(n)]


def rotate(grid: list[list[int]], r: int) -> list[list[int]]:
    r %= 4
    res = [row[:] for row in grid]
    for _ in range(r):
        res = rotate_cw(res)
    return res


def apply_paint(layer: list[list[int]], i: int, j: int, x: int) -> None:
    layer[i][j] = x


def apply_copy(layer: list[list[int]], r: int, di: int, dj: int) -> None:
    n = len(layer)
    src = rotate(layer, r)
    updates: list[tuple[int, int, int]] = []
    for i in range(n):
        for j in range(n):
            v = src[i][j]
            if v == 0:
                continue
            ti = di + i
            tj = dj + j
            if not (0 <= ti < n and 0 <= tj < n):
                raise ValueError(f"copy out of range: ({ti}, {tj})")
            updates.append((ti, tj, v))
    for ti, tj, v in updates:
        layer[ti][tj] = v


def count_nonzero(layer: list[list[int]]) -> int:
    return sum(1 for row in layer for v in row if v != 0)


def random_legal_self_copy(layer: list[list[int]], rng: random.Random) -> tuple[int, int, int]:
    n = len(layer)
    r = rng.randint(0, 3)
    src = rotate(layer, r)

    pts = [(i, j) for i in range(n) for j in range(n) if src[i][j] != 0]
    if not pts:
        return r, 0, 0

    min_i = min(i for i, _ in pts)
    max_i = max(i for i, _ in pts)
    min_j = min(j for _, j in pts)
    max_j = max(j for _, j in pts)

    di_lo = -min_i
    di_hi = n - 1 - max_i
    dj_lo = -min_j
    dj_hi = n - 1 - max_j

    di = rng.randint(di_lo, di_hi)
    dj = rng.randint(dj_lo, dj_hi)
    return r, di, dj


def generate(seed: int):
    rng = random.Random(seed)
    layer0 = [[0] * N for _ in range(N)]
    ops: list[list[int]] = []

    # Shift the 16x16 active area. Top-left is randomized in [1, 10].
    si = rng.randint(1, 10)
    sj = rng.randint(1, 10)

    # Initial 2x2 = [ [1,2], [3,4] ]
    initial = [
        (si + 0, sj + 0, 1),
        (si + 0, sj + 1, 2),
        (si + 1, sj + 0, 3),
        (si + 1, sj + 1, 4),
    ]
    for i, j, x in initial:
        apply_paint(layer0, i, j, x)
        ops.append([0, 0, i, j, x])

    # Horizontal doublings: 2x2 -> 2x4 -> 2x8 -> 2x16
    w = 2
    while w < REGION:
        r = rng.choice([0, 2])
        if r == 0:
            di, dj = 0, w
        else:
            # Active rows are [si,si+1], cols [sj,sj+w-1].
            # After 180-rotation on 32x32, they become
            # rows [30-si,31-si], cols [32-sj-w,31-sj].
            # Shift to [si,si+1] x [sj+w,sj+2w-1].
            di = 2 * si - 30
            dj = 2 * sj + 2 * w - N
        apply_copy(layer0, r, di, dj)
        ops.append([1, 0, 0, r, di, dj])
        w *= 2

    # Vertical doublings: 2x16 -> 4x16 -> 8x16 -> 16x16
    h = 2
    while h < REGION:
        r = rng.choice([0, 2])
        if r == 0:
            di, dj = h, 0
        else:
            # Active rows are [si, si+h-1], cols [sj, sj+REGION-1].
            # After 180-rotation on 32x32, they become
            # rows [32-si-h, 31-si], cols [32-sj-REGION, 31-sj].
            # Shift to [si+h, si+2h-1] x [sj, sj+REGION-1].
            di = 2 * si + 2 * h - N
            dj = 2 * sj + REGION - N
        apply_copy(layer0, r, di, dj)
        ops.append([1, 0, 0, r, di, dj])
        h *= 2

    # Random rewrite of the active region top-left (must be different).
    cur = layer0[si][sj]
    cand = [x for x in range(1, C + 1) if x != cur]
    final_color = rng.choice(cand)
    apply_paint(layer0, si, sj, final_color)
    ops.append([0, 0, si, sj, final_color])

    # Add exactly two random self-copy operations.
    # Retry until the final board has more than half non-transparent cells.
    while True:
        layer_tmp = [row[:] for row in layer0]
        extra_ops: list[list[int]] = []
        for _ in range(2):
            r, di, dj = random_legal_self_copy(layer_tmp, rng)
            apply_copy(layer_tmp, r, di, dj)
            extra_ops.append([1, 0, 0, r, di, dj])
        if count_nonzero(layer_tmp) > (N * N) // 2:
            layer0 = layer_tmp
            ops.extend(extra_ops)
            break

    return layer0, ops, si, sj


def fnv1a64(grid: list[list[int]]) -> int:
    h = 1469598103934665603
    for row in grid:
        for v in row:
            h ^= v + 0x9E3779B97F4A7C15
            h &= (1 << 64) - 1
            h = (h * 1099511628211) & ((1 << 64) - 1)
    return h


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-seed", type=int, default=20260418)
    parser.add_argument("--count", type=int, default=4)
    args = parser.parse_args()

    cases_dir = Path("b_cases")
    tools_in = Path("tools/in")
    cases_dir.mkdir(parents=True, exist_ok=True)
    tools_in.mkdir(parents=True, exist_ok=True)

    all_case_texts: list[str] = []
    meta = []

    for idx in range(args.count):
        seed = args.base_seed + idx * 10007
        g, ops, si, sj = generate(seed)
        h = fnv1a64(g)

        case_name = f"case_{idx:02d}.txt"
        ops_name = f"case_{idx:02d}_true_ops.txt"
        seed_name = f"{100 + idx:04d}.txt"
        case_path = cases_dir / case_name
        ops_path = cases_dir / ops_name
        tools_path = tools_in / seed_name

        lines = [f"{N} {K} {C}"]
        for i in range(N):
            lines.append(" ".join(map(str, g[i])))
        case_text = "\n".join(lines) + "\n"

        case_path.write_text(case_text, encoding="utf-8")
        tools_path.write_text(case_text, encoding="utf-8")

        with ops_path.open("w", encoding="utf-8") as f:
            for op in ops:
                f.write(" ".join(map(str, op)) + "\n")

        all_case_texts.append(case_text)
        meta.append(
            {
                "index": idx,
                "seed": seed,
                "input_seed_file": seed_name,
                "shift": [si, sj],
                "hash": f"0x{h:016x}",
                "ops": len(ops),
                "case_file": str(case_path),
                "ops_file": str(ops_path),
            }
        )
        print(
            f"idx={idx} seed={seed} file={seed_name} hash=0x{h:016x} "
            f"shift=({si},{sj}) ops={len(ops)}"
        )

    Path("B.txt").write_text("".join(all_case_texts), encoding="utf-8")
    Path("b_cases/meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote: B.txt")
    print("wrote: b_cases/meta.json")


if __name__ == "__main__":
    main()
