#!/usr/bin/env python3
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class InputData:
    n: int
    k: int
    c: int
    g: List[List[int]]


@dataclass
class Action:
    kind: int
    k: int
    i: int = 0
    j: int = 0
    c: int = 0
    h: int = 0
    r: int = 0
    di: int = 0
    dj: int = 0


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_input(path: str) -> InputData:
    with open(path, "r", encoding="utf-8") as f:
        tokens = f.read().split()

    it = iter(tokens)
    n = int(next(it))
    k = int(next(it))
    c = int(next(it))
    g = [[int(next(it)) for _ in range(n)] for _ in range(n)]
    return InputData(n=n, k=k, c=c, g=g)


def read_bounded_int(token: str, lo: int, hi: int, name: str) -> int:
    v = int(token)
    if v < lo or v > hi:
        raise ValueError(f"{name} out of range: {v}, expected [{lo}, {hi}]")
    return v


def parse_output(inp: InputData, path: str) -> List[Action]:
    actions: List[Action] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            parts = s.split()

            ty = read_bounded_int(parts[0], 0, 2, f"type at line {line_no}")
            if ty == 0:
                if len(parts) != 5:
                    raise ValueError(f"invalid token count at line {line_no}: expected 5")
                k = read_bounded_int(parts[1], 0, inp.k - 1, f"k at line {line_no}")
                i = read_bounded_int(parts[2], 0, inp.n - 1, f"i at line {line_no}")
                j = read_bounded_int(parts[3], 0, inp.n - 1, f"j at line {line_no}")
                c = read_bounded_int(parts[4], 0, inp.c, f"c at line {line_no}")
                actions.append(Action(kind=0, k=k, i=i, j=j, c=c))
            elif ty == 1:
                if len(parts) != 6:
                    raise ValueError(f"invalid token count at line {line_no}: expected 6")
                k = read_bounded_int(parts[1], 0, inp.k - 1, f"k at line {line_no}")
                h = read_bounded_int(parts[2], 0, inp.k - 1, f"h at line {line_no}")
                r = read_bounded_int(parts[3], 0, 3, f"r at line {line_no}")
                di = read_bounded_int(parts[4], -(inp.n - 1), inp.n - 1, f"di at line {line_no}")
                dj = read_bounded_int(parts[5], -(inp.n - 1), inp.n - 1, f"dj at line {line_no}")
                actions.append(Action(kind=1, k=k, h=h, r=r, di=di, dj=dj))
            else:
                if len(parts) != 2:
                    raise ValueError(f"invalid token count at line {line_no}: expected 2")
                k = read_bounded_int(parts[1], 0, inp.k - 1, f"k at line {line_no}")
                actions.append(Action(kind=2, k=k))

    if len(actions) > inp.n * inp.n:
        raise ValueError("Too many actions")

    return actions


def rotate(grid: List[List[int]], r: int) -> List[List[int]]:
    n = len(grid)
    out = [row[:] for row in grid]
    for _ in range(r):
        nxt = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                nxt[i][j] = out[n - 1 - j][i]
        out = nxt
    return out


def copy_layer(dst: List[List[int]], src: List[List[int]], di: int, dj: int) -> Tuple[bool, List[List[int]]]:
    n = len(dst)
    out = [row[:] for row in dst]
    for i in range(n):
        for j in range(n):
            if src[i][j] == 0:
                continue
            ni = i + di
            nj = j + dj
            if ni < 0 or ni >= n or nj < 0 or nj >= n:
                return False, out
            out[ni][nj] = src[i][j]
    return True, out


def score_from_state(inp: InputData, actions: List[Action], layers: List[List[List[int]]]) -> Tuple[int, str]:
    if layers[0] != inp.g:
        return 0, "Not finished"

    u = sum(1 for row in inp.g for v in row if v != 0)
    x = len(actions)
    if x <= 0:
        return 0, "No actions"

    score = 1_000_000.0 * (1.0 + math.log2(u / x))
    return int(round(score)), ""


def simulate(inp: InputData, actions: List[Action]) -> Tuple[int, str, List[List[List[int]]], List[List[List[List[int]]]]]:
    layers = [[[0 for _ in range(inp.n)] for _ in range(inp.n)] for _ in range(inp.k)]
    frames = [[[row[:] for row in layer] for layer in layers]]

    for a in actions:
        if a.kind == 0:
            layers[a.k][a.i][a.j] = a.c
        elif a.kind == 1:
            src = rotate(layers[a.h], a.r)
            ok, copied = copy_layer(layers[a.k], src, a.di, a.dj)
            if not ok:
                return 0, (
                    f"Invalid copy: k={a.k}, h={a.h}, r={a.r}, di={a.di}, dj={a.dj}"
                ), layers, frames
            layers[a.k] = copied
        else:
            layers[a.k] = [[0 for _ in range(inp.n)] for _ in range(inp.n)]

        frames.append([[row[:] for row in layer] for layer in layers])

    score, err = score_from_state(inp, actions, layers)
    return score, err, layers, frames


def color_palette(max_c: int) -> List[str]:
    base = [
        "#f8fafc",  # 0
        "#2563eb",
        "#16a34a",
        "#dc2626",
        "#d97706",
        "#9333ea",
        "#0891b2",
        "#be123c",
        "#0f766e",
    ]
    if max_c + 1 <= len(base):
        return base[: max_c + 1]
    out = base[:]
    for i in range(len(base), max_c + 1):
        h = int((360 * i) / (max_c + 2))
        out.append(f"hsl({h}, 70%, 45%)")
    return out


def write_html(
    html_path: str,
    inp: InputData,
    actions: List[Action],
    score: int,
    err: str,
    frames: List[List[List[List[int]]]],
) -> None:
    ensure_parent(html_path)

    payload = {
        "n": inp.n,
        "k": inp.k,
        "c": inp.c,
        "g": inp.g,
        "frames": frames,
        "actions": [a.__dict__ for a in actions],
        "palette": color_palette(inp.c),
    }

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>masters2026-final visualizer</title>
  <style>
    :root {{
      --bg: #f3f4f6;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --line: #cbd5e1;
      --ok: #15803d;
      --ng: #b91c1c;
      --btn: #0ea5e9;
      --btnh: #0284c7;
    }}
    body {{ margin: 0; font-family: "Segoe UI", "Hiragino Sans", sans-serif; color: var(--text); background: radial-gradient(circle at 0% 0%, #ffffff 0%, var(--bg) 60%); }}
    .wrap {{ max-width: 1360px; margin: 0 auto; padding: 18px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; box-shadow: 0 8px 20px rgba(15,23,42,0.08); }}
    .title {{ margin: 0 0 6px 0; font-size: 24px; }}
    .score {{ font-size: 30px; font-weight: 700; color: {"var(--ok)" if not err else "var(--ng)"}; }}
    .sub {{ color: var(--muted); margin: 6px 0 14px 0; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }}
    .stat {{ background: #f8fafc; border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; }}
    .stat .k {{ color: var(--muted); font-size: 12px; }}
    .stat .v {{ font-size: 20px; font-weight: 600; }}
    .controls {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 10px; }}
    button {{ border: 0; border-radius: 8px; padding: 8px 12px; color: #fff; background: var(--btn); cursor: pointer; }}
    button:hover {{ background: var(--btnh); }}
    input[type=range] {{ min-width: 280px; flex: 1; }}
    .canvas-row {{ display: grid; grid-template-columns: 1fr; gap: 12px; align-items: start; }}
    .layers-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }}
    .layer-card {{ border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 6px; }}
    .layer-title {{ color: var(--muted); font-size: 13px; margin: 0 0 4px 0; }}
    .layer-canvas {{ width: 100%; height: auto; border: 1px solid var(--line); border-radius: 6px; background: #fff; display: block; }}
    .layer-card.hl-paint {{ border-color: #16a34a; box-shadow: inset 0 0 0 2px rgba(22,163,74,0.16); }}
    .layer-card.hl-clear {{ border-color: #dc2626; box-shadow: inset 0 0 0 2px rgba(220,38,38,0.14); }}
    .layer-card.hl-copy-src {{ border-color: #f59e0b; box-shadow: inset 0 0 0 2px rgba(245,158,11,0.18); }}
    .layer-card.hl-copy-dst {{ border-color: #2563eb; box-shadow: inset 0 0 0 2px rgba(37,99,235,0.16); }}
    .legend {{ margin-top: 10px; color: var(--muted); font-size: 13px; }}
    .action {{ margin-top: 6px; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"card\">
      <h1 class=\"title\">masters2026-final Visualizer</h1>
      <div class=\"score\">Score: {score}</div>
      <div class=\"sub\">{err if err else "Feasible output"}</div>

      <div class=\"stats\">
        <div class=\"stat\"><div class=\"k\">N</div><div class=\"v\">{inp.n}</div></div>
        <div class=\"stat\"><div class=\"k\">K (layers)</div><div class=\"v\">{inp.k}</div></div>
        <div class=\"stat\"><div class=\"k\">C (colors)</div><div class=\"v\">{inp.c}</div></div>
        <div class=\"stat\"><div class=\"k\">Actions</div><div class=\"v\">{len(actions)}</div></div>
      </div>

      <div class=\"controls\">
        <button id=\"play\">Play</button>
        <button id=\"prev\">Prev</button>
        <button id=\"next\">Next</button>
        <input id=\"slider\" type=\"range\" min=\"0\" max=\"{len(frames)-1}\" value=\"0\" step=\"1\" />
        <span id=\"step\">0 / {len(frames)-1}</span>
      </div>

      <div class=\"canvas-row\">
        <div>
          <div class=\"sub\">All Layers</div>
          <div id=\"layers\" class=\"layers-grid\">
            <div class=\"layer-card\">
              <div class=\"layer-title\">target (g)</div>
              <canvas id=\"target\" class=\"layer-canvas\"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div id=\"action\" class=\"action\"></div>
      <div class=\"legend\">Paint: green, Clear: red, Copy source: amber, Copy destination: blue. Copy overlays show source/destination ranges.</div>
    </div>
  </div>

<script>
const DATA = {json.dumps(payload)};
let step = 0;
let playing = false;
let timer = null;

const slider = document.getElementById('slider');
const stepLabel = document.getElementById('step');
const actionLabel = document.getElementById('action');
const layersRoot = document.getElementById('layers');
const tgtCanvas = document.getElementById('target');
const tgtCtx = tgtCanvas.getContext('2d');

const cell = Math.max(6, Math.min(16, Math.floor(280 / DATA.n)));
const pad = 10;
const side = DATA.n * cell + pad * 2;
tgtCanvas.width = side;
tgtCanvas.height = side;

const layerCanvases = [];
const layerCards = [];
for (let i = 0; i < DATA.k; i++) {{
  const card = document.createElement('div');
  card.className = 'layer-card';

  const title = document.createElement('div');
  title.className = 'layer-title';
  title.textContent = `layer ${{i}}`;

  const canvas = document.createElement('canvas');
  canvas.className = 'layer-canvas';
  canvas.width = side;
  canvas.height = side;

  card.appendChild(title);
  card.appendChild(canvas);
  layersRoot.appendChild(card);
  layerCanvases.push(canvas);
  layerCards.push(card);
}}

function colorOf(v) {{
  return DATA.palette[Math.min(v, DATA.palette.length - 1)];
}}

function drawGrid(ctx, grid, overlay = null) {{
  ctx.clearRect(0, 0, side, side);
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, side, side);

  for (let i = 0; i < DATA.n; i++) {{
    for (let j = 0; j < DATA.n; j++) {{
      ctx.fillStyle = colorOf(grid[i][j]);
      ctx.fillRect(pad + j * cell, pad + i * cell, cell, cell);
    }}
  }}

  ctx.strokeStyle = '#e2e8f0';
  ctx.lineWidth = 1;
  for (let i = 0; i <= DATA.n; i++) {{
    ctx.beginPath();
    ctx.moveTo(pad, pad + i * cell);
    ctx.lineTo(pad + DATA.n * cell, pad + i * cell);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(pad + i * cell, pad);
    ctx.lineTo(pad + i * cell, pad + DATA.n * cell);
    ctx.stroke();
  }}

  ctx.strokeStyle = '#111827';
  ctx.lineWidth = 2;
  ctx.strokeRect(pad, pad, DATA.n * cell, DATA.n * cell);

  if (!overlay) return;

  if (overlay.rects) {{
    for (const r of overlay.rects) {{
      const x = pad + r.j0 * cell;
      const y = pad + r.i0 * cell;
      const w = (r.j1 - r.j0 + 1) * cell;
      const h = (r.i1 - r.i0 + 1) * cell;
      ctx.save();
      ctx.strokeStyle = r.color;
      ctx.lineWidth = 3;
      if (r.dashed) ctx.setLineDash([8, 4]);
      ctx.strokeRect(x + 1, y + 1, Math.max(0, w - 2), Math.max(0, h - 2));
      ctx.restore();
    }}
  }}

  if (overlay.cell) {{
    const i = overlay.cell.i;
    const j = overlay.cell.j;
    const x = pad + j * cell;
    const y = pad + i * cell;
    ctx.save();
    ctx.strokeStyle = overlay.cell.color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x + 2, y + 2, Math.max(0, cell - 4), Math.max(0, cell - 4));
    ctx.restore();
  }}
}}

function bboxNonZero(grid) {{
  let minI = DATA.n, maxI = -1, minJ = DATA.n, maxJ = -1;
  for (let i = 0; i < DATA.n; i++) {{
    for (let j = 0; j < DATA.n; j++) {{
      if (grid[i][j] !== 0) {{
        if (i < minI) minI = i;
        if (i > maxI) maxI = i;
        if (j < minJ) minJ = j;
        if (j > maxJ) maxJ = j;
      }}
    }}
  }}
  if (maxI < 0) return null;
  return {{ i0: minI, i1: maxI, j0: minJ, j1: maxJ }};
}}

function rotateGrid(grid, r) {{
  let out = grid.map(row => row.slice());
  for (let t = 0; t < r; t++) {{
    const nxt = Array.from({{ length: DATA.n }}, () => Array(DATA.n).fill(0));
    for (let i = 0; i < DATA.n; i++) {{
      for (let j = 0; j < DATA.n; j++) {{
        nxt[i][j] = out[DATA.n - 1 - j][i];
      }}
    }}
    out = nxt;
  }}
  return out;
}}

function actionText(a) {{
  if (!a) return '初期状態';
  if (a.kind === 1) return `【コピー】 レイヤ ${{a.h}} → レイヤ ${{a.k}}、回転 ${{a.r}}、平行移動 (${{a.di >= 0 ? '+' : ''}}${{a.di}}, ${{a.dj >= 0 ? '+' : ''}}${{a.dj}})`;
  if (a.kind === 2) return `【クリア】レイヤ ${{a.k}}`;
  return `【ペイント】対象レイヤ ${{a.k}}、座標 (${{a.i}}, ${{a.j}})、色 ${{a.c}}`;
}}

function render() {{
  for (const card of layerCards) {{
    card.classList.remove('hl-paint', 'hl-clear', 'hl-copy-src', 'hl-copy-dst');
  }}

  const overlays = Array.from({{ length: DATA.k }}, () => null);
  const a = step === 0 ? null : DATA.actions[step - 1];
  if (a) {{
    if (a.kind === 0) {{
      layerCards[a.k].classList.add('hl-paint');
      overlays[a.k] = {{ cell: {{ i: a.i, j: a.j, color: '#16a34a' }} }};
    }} else if (a.kind === 2) {{
      layerCards[a.k].classList.add('hl-clear');
    }} else if (a.kind === 1) {{
      layerCards[a.h].classList.add('hl-copy-src');
      layerCards[a.k].classList.add('hl-copy-dst');

      const srcPrev = DATA.frames[step - 1][a.h];
      const srcBox = bboxNonZero(srcPrev);
      if (srcBox) {{
        overlays[a.h] = {{ rects: [{{ ...srcBox, color: '#f59e0b', dashed: false }}] }};
      }}

      const rot = rotateGrid(srcPrev, a.r);
      const rotBox = bboxNonZero(rot);
      if (rotBox) {{
        overlays[a.k] = {{
          rects: [{{
            i0: rotBox.i0 + a.di,
            i1: rotBox.i1 + a.di,
            j0: rotBox.j0 + a.dj,
            j1: rotBox.j1 + a.dj,
            color: '#2563eb',
            dashed: true,
          }}],
        }};
      }}
    }}
  }}

  for (let i = 0; i < DATA.k; i++) {{
    const ctx = layerCanvases[i].getContext('2d');
    drawGrid(ctx, DATA.frames[step][i], overlays[i]);
  }}
  drawGrid(tgtCtx, DATA.g);
  stepLabel.textContent = `${{step}} / ${{DATA.frames.length - 1}}`;
  slider.value = String(step);
  actionLabel.textContent = actionText(a);
}}

function setStep(v) {{
  step = Math.max(0, Math.min(DATA.frames.length - 1, v));
  render();
}}

document.getElementById('prev').addEventListener('click', () => setStep(step - 1));
document.getElementById('next').addEventListener('click', () => setStep(step + 1));
slider.addEventListener('input', e => setStep(parseInt(e.target.value, 10)));

document.getElementById('play').addEventListener('click', () => {{
  playing = !playing;
  const btn = document.getElementById('play');
  btn.textContent = playing ? 'Pause' : 'Play';
  if (playing) {{
    timer = setInterval(() => {{
      if (step >= DATA.frames.length - 1) step = 0;
      else step += 1;
      render();
    }}, 140);
  }} else if (timer) {{
    clearInterval(timer);
    timer = null;
  }}
}});

render();
</script>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def write_error_html(html_path: str, msg: str) -> None:
    ensure_parent(html_path)
    esc = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(
            "<!doctype html><html><head><meta charset='utf-8'><title>Visualizer Error</title></head>"
            "<body><h1>Visualizer Error</h1><pre>" + esc + "</pre></body></html>"
        )


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python3 visualizer.py <input_file> <output_file> <html_file>")
        print("Score = 0")
        return 1

    in_path, out_path, html_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        inp = parse_input(in_path)
        actions = parse_output(inp, out_path)
        score, err, _, frames = simulate(inp, actions)
        write_html(html_path, inp, actions, score, err, frames)

        if err:
            print(err)
            print("Score = 0")
        else:
            print(f"Score = {score}")
        return 0
    except Exception as e:
        write_error_html(html_path, str(e))
        print(str(e))
        print("Score = 0")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
