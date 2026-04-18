import argparse
import json
from pathlib import Path


def parse_input(path: Path):
        with path.open("r", encoding="utf-8") as f:
                vals = list(map(int, f.read().split()))
        if len(vals) < 3:
                raise ValueError("input is too short")
        n, k, c = vals[0], vals[1], vals[2]
        need = 3 + n * n
        if len(vals) < need:
                raise ValueError(f"input grid is too short: need {need} ints, got {len(vals)}")
        g = []
        p = 3
        for _ in range(n):
                g.append(vals[p : p + n])
                p += n
        return n, k, c, g


def rotate_cw(i: int, j: int, n: int, r: int):
        r %= 4
        if r == 0:
                return i, j
        if r == 1:
                return j, n - 1 - i
        if r == 2:
                return n - 1 - i, n - 1 - j
        return n - 1 - j, i


def simulate(n: int, k: int, output_path: Path):
        layers = [[[0 for _ in range(n)] for _ in range(n)] for _ in range(k)]
        steps = []

        with output_path.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line:
                                continue
                        tok = line.split()
                        try:
                                op = int(tok[0])
                        except ValueError as e:
                                steps.append(
                                        {
                                                "op": line,
                                                "changes": [],
                                                "error": f"line {line_no}: invalid op type ({e})",
                                        }
                                )
                                break

                        changes = []
                        error = None

                        if op == 0:
                                if len(tok) != 5:
                                        error = f"line {line_no}: paint must have 5 tokens"
                                else:
                                        kk, i, j, x = map(int, tok[1:])
                                        if not (0 <= kk < k and 0 <= i < n and 0 <= j < n):
                                                error = f"line {line_no}: paint index out of range"
                                        else:
                                                old = layers[kk][i][j]
                                                if old != x:
                                                        layers[kk][i][j] = x
                                                        changes.append([kk, i, j, old, x])

                        elif op == 1:
                                if len(tok) != 6:
                                        error = f"line {line_no}: copy must have 6 tokens"
                                else:
                                        kk, h, r, di, dj = map(int, tok[1:])
                                        if not (0 <= kk < k and 0 <= h < k):
                                                error = f"line {line_no}: copy layer index out of range"
                                        elif r not in (0, 1, 2, 3):
                                                error = f"line {line_no}: copy rotation out of range"
                                        else:
                                                updates = []
                                                for i in range(n):
                                                        for j in range(n):
                                                                si, sj = rotate_cw(i, j, n, (4 - r) % 4)
                                                                val = layers[h][si][sj]
                                                                if val == 0:
                                                                        continue
                                                                ti = di + i
                                                                tj = dj + j
                                                                if not (0 <= ti < n and 0 <= tj < n):
                                                                        error = (
                                                                                f"line {line_no}: copy paints outside board "
                                                                                f"at ({ti},{tj})"
                                                                        )
                                                                        break
                                                                updates.append((ti, tj, val))
                                                        if error is not None:
                                                                break

                                                if error is None:
                                                        seen = set()
                                                        for ti, tj, val in updates:
                                                                if (ti, tj) in seen:
                                                                        continue
                                                                seen.add((ti, tj))
                                                                old = layers[kk][ti][tj]
                                                                if old != val:
                                                                        layers[kk][ti][tj] = val
                                                                        changes.append([kk, ti, tj, old, val])

                        elif op == 2:
                                if len(tok) != 2:
                                        error = f"line {line_no}: clear must have 2 tokens"
                                else:
                                        kk = int(tok[1])
                                        if not (0 <= kk < k):
                                                error = f"line {line_no}: clear layer index out of range"
                                        else:
                                                for i in range(n):
                                                        for j in range(n):
                                                                old = layers[kk][i][j]
                                                                if old != 0:
                                                                        layers[kk][i][j] = 0
                                                                        changes.append([kk, i, j, old, 0])

                        else:
                                error = f"line {line_no}: unknown op type {op}"

                        steps.append({"op": line, "changes": changes, "error": error})
                        if error is not None:
                                break

        return steps


def build_html(n: int, k: int, c: int, target, steps):
        data = {
                "n": n,
                "k": k,
                "c": c,
                "target": target,
                "steps": steps,
        }
        js_data = json.dumps(data, ensure_ascii=False)

        return f"""<!doctype html>
<html lang=\"ja\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Copy-Paste Painting Visualizer</title>
    <style>
        :root {{
            --bg: #f3efe7;
            --panel: #fffdf8;
            --ink: #2d2a26;
            --muted: #746d62;
            --accent: #d95f02;
            --grid: #cfc6b8;
            --highlight: #ffcc00;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
            background: radial-gradient(circle at 20% 20%, #fffdf8 0%, var(--bg) 52%, #e7dece 100%);
            color: var(--ink);
        }}
        .wrap {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        .toolbar {{
            position: sticky;
            top: 0;
            z-index: 20;
            background: color-mix(in srgb, var(--panel) 86%, white 14%);
            border: 1px solid #e3d9c9;
            border-radius: 14px;
            padding: 12px;
            display: grid;
            gap: 10px;
            backdrop-filter: blur(6px);
        }}
        .row {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }}
        button {{
            border: 1px solid #c5b59f;
            background: #fff;
            color: var(--ink);
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        button:hover {{ border-color: var(--accent); }}
        input[type=\"range\"] {{ width: min(760px, 92vw); }}
        .meta {{ color: var(--muted); font-size: 14px; }}
        .current-op {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            background: #fff;
            border: 1px solid #eadfce;
            border-radius: 8px;
            padding: 8px;
            min-height: 36px;
        }}
        .layers {{
            margin-top: 16px;
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }}
        .card {{
            background: var(--panel);
            border: 1px solid #e4dacb;
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 4px 18px rgba(64, 44, 11, 0.08);
        }}
        .card h3 {{ margin: 0 0 8px 0; font-size: 16px; }}
        canvas {{
            width: 100%;
            height: auto;
            image-rendering: pixelated;
            border: 1px solid #d8ccb8;
            border-radius: 8px;
            background: #ffffff;
        }}
        .legend {{
            margin-top: 6px;
            font-size: 12px;
            color: var(--muted);
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .swatch {{
            width: 12px;
            height: 12px;
            display: inline-block;
            border: 1px solid #888;
            margin-right: 4px;
            vertical-align: -2px;
        }}
        .err {{ color: #b42318; font-weight: 700; }}
    </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"toolbar\">
            <div class=\"row\">
                <button id=\"prev\">Prev</button>
                <button id=\"next\">Next</button>
                <button id=\"play\">Play</button>
                <button id=\"pause\">Pause</button>
                <label>Interval(ms): <input id=\"interval\" type=\"number\" min=\"20\" step=\"20\" value=\"120\" style=\"width:90px\"></label>
            </div>
            <div class=\"row\">
                <input id=\"slider\" type=\"range\" min=\"0\" value=\"0\" />
                <span id=\"stepLabel\" class=\"meta\"></span>
            </div>
            <div id=\"opText\" class=\"current-op\"></div>
            <div id=\"errText\" class=\"meta err\"></div>
        </div>
        <div id=\"layers\" class=\"layers\"></div>
    </div>

    <script>
        const DATA = {js_data};
        const n = DATA.n;
        const k = DATA.k;
        const steps = DATA.steps;
        const maxStep = steps.length;

        const palette = [
            '#ffffff', '#0072B2', '#D55E00', '#009E73', '#CC79A7',
            '#F0E442', '#56B4E9', '#E69F00', '#999999'
        ];

        const slider = document.getElementById('slider');
        const stepLabel = document.getElementById('stepLabel');
        const opText = document.getElementById('opText');
        const errText = document.getElementById('errText');
        const layersDiv = document.getElementById('layers');
        slider.max = String(maxStep);

        const state = Array.from({{length: k}}, () =>
            Array.from({{length: n}}, () => Array(n).fill(0))
        );
        const canvases = [];
        let curStep = 0;
        let timer = null;

        function colorOf(v) {{
            if (v < palette.length) return palette[v];
            const hue = (v * 47) % 360;
            return `hsl(${{hue}} 70% 55%)`;
        }}

        function buildLayers() {{
            const legendBits = ['<span><span class="swatch" style="background:#fff"></span>0(transparent)</span>'];
            for (let col = 1; col <= DATA.c; col++) {{
                legendBits.push(`<span><span class="swatch" style="background:${{colorOf(col)}}"></span>${{col}}</span>`);
            }}

            for (let layer = 0; layer < k; layer++) {{
                const card = document.createElement('div');
                card.className = 'card';
                const title = document.createElement('h3');
                title.textContent = `Layer ${{layer}}`;
                const canvas = document.createElement('canvas');
                canvas.width = n * 14;
                canvas.height = n * 14;
                const legend = document.createElement('div');
                legend.className = 'legend';
                legend.innerHTML = legendBits.join('');
                card.appendChild(title);
                card.appendChild(canvas);
                card.appendChild(legend);
                layersDiv.appendChild(card);
                canvases.push(canvas);
            }}
        }}

        function applyStep(s) {{
            const rec = steps[s - 1];
            for (const ch of rec.changes) {{
                const [ly, i, j, _old, nv] = ch;
                state[ly][i][j] = nv;
            }}
        }}

        function revertStep(s) {{
            const rec = steps[s - 1];
            for (let idx = rec.changes.length - 1; idx >= 0; idx--) {{
                const ch = rec.changes[idx];
                const [ly, i, j, ov] = ch;
                state[ly][i][j] = ov;
            }}
        }}

        function setStep(target) {{
            target = Math.max(0, Math.min(maxStep, target));
            while (curStep < target) {{
                curStep++;
                applyStep(curStep);
            }}
            while (curStep > target) {{
                revertStep(curStep);
                curStep--;
            }}
            draw();
        }}

        function drawLayer(layerIdx, highlights) {{
            const canvas = canvases[layerIdx];
            const ctx = canvas.getContext('2d');
            const cw = canvas.width / n;
            const ch = canvas.height / n;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (let i = 0; i < n; i++) {{
                for (let j = 0; j < n; j++) {{
                    ctx.fillStyle = colorOf(state[layerIdx][i][j]);
                    ctx.fillRect(j * cw, i * ch, cw, ch);
                }}
            }}

            ctx.strokeStyle = '#cfc6b8';
            ctx.lineWidth = 1;
            for (let t = 0; t <= n; t++) {{
                ctx.beginPath();
                ctx.moveTo(0, t * ch);
                ctx.lineTo(canvas.width, t * ch);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(t * cw, 0);
                ctx.lineTo(t * cw, canvas.height);
                ctx.stroke();
            }}

            ctx.strokeStyle = '#ffcc00';
            ctx.lineWidth = 2;
            for (const [i, j] of highlights) {{
                ctx.strokeRect(j * cw + 1, i * ch + 1, cw - 2, ch - 2);
            }}
        }}

        function draw() {{
            slider.value = String(curStep);
            stepLabel.textContent = `Step ${{curStep}} / ${{maxStep}}`;

            let curOp = 'Initial state';
            let curErr = '';
            const hmap = Array.from({{length: k}}, () => []);
            if (curStep > 0) {{
                const rec = steps[curStep - 1];
                curOp = rec.op;
                if (rec.error) curErr = rec.error;
                for (const ch of rec.changes) {{
                    const [ly, i, j] = ch;
                    hmap[ly].push([i, j]);
                }}
            }}

            opText.textContent = curOp;
            errText.textContent = curErr;
            for (let ly = 0; ly < k; ly++) drawLayer(ly, hmap[ly]);
        }}

        function play() {{
            if (timer !== null) return;
            const iv = Math.max(20, Number(document.getElementById('interval').value) || 120);
            timer = setInterval(() => {{
                if (curStep >= maxStep) {{
                    pause();
                    return;
                }}
                setStep(curStep + 1);
            }}, iv);
        }}

        function pause() {{
            if (timer !== null) {{
                clearInterval(timer);
                timer = null;
            }}
        }}

        document.getElementById('prev').addEventListener('click', () => setStep(curStep - 1));
        document.getElementById('next').addEventListener('click', () => setStep(curStep + 1));
        document.getElementById('play').addEventListener('click', play);
        document.getElementById('pause').addEventListener('click', pause);
        slider.addEventListener('input', (e) => setStep(Number(e.target.value)));

        buildLayers();
        draw();
    </script>
</body>
</html>
"""


def main():
        parser = argparse.ArgumentParser(
                description="Generate static HTML visualizer for Copy-Paste Painting."
        )
        parser.add_argument("input", help="input file path")
        parser.add_argument("output", help="solver output file path")
        parser.add_argument("-o", "--html", default="visualizer.html", help="output HTML path")
        args = parser.parse_args()

        in_path = Path(args.input)
        out_path = Path(args.output)
        html_path = Path(args.html)

        n, k, c, g = parse_input(in_path)
        steps = simulate(n, k, out_path)
        html = build_html(n, k, c, g, steps)
        html_path.write_text(html, encoding="utf-8")
        print(f"wrote: {html_path}")
        print(f"steps: {len(steps)}")


if __name__ == "__main__":
        main()