import sys

import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def create_animated_figure(figures, width = 600, height = 600):
    """
    figures: list of (trace, shape)
        複数の Figure をスライダーで切り替えて表示する新しい Figure を作成
    
    return: plotly.graph_objects.Figure
        スライダー付きの新しい Figure
    """
    
    # 最初の figure を表示するために、初期状態のデータを取得
    initial_data, _ = figures[0]
    
    # frames の作成: 各 figure に対応する frame を作成
    frames = [
        go.Frame(
            data=data,
            layout={"shapes": shapes},
            name=f"t = {i}"
        )
        for i, (data,shapes) in enumerate(figures)
    ]
    
    # スライダーのステップを作成
    steps = [
        dict(
            args=[[f"t = {i}"], {"frame": {"duration": 30, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
            label=f"t = {i}",
            method="animate"
        )
        for i in range(len(figures))
    ]
    
    # レイアウトの設定
    layout = go.Layout(
        width=width,
        height=height,
        updatemenus=[dict(
            type='buttons',
            showactive=False,
            buttons=[dict(
                label="Play",
                method="animate",
                args=[None, dict(frame=dict(duration=30, redraw=True), fromcurrent=True)]
            )]
        )],
        sliders=[dict(
            active=0,
            pad=dict(b=10),
            steps=steps  # スライダーのステップを設定
        )],
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False, autorange="reversed")
    
    )
    
    # 新しい figure の作成
    new_fig = go.Figure(
        data=initial_data,  # 初期状態で最初の figure のデータを表示
        layout=layout,
        frames=frames  # スライダーで切り替えられるフレーム
    )
    
    return new_fig

def make_trace(state, cx, cy, dd, anax, anay):
    a = [[dd[item] for item in line] for line in state]
    traces = [go.Heatmap(z=a)]
    shapes = []
    for x,y in zip(anax, anay):
        shapes.append(go.layout.Shape(
                type='rect',
                x0=y-0.5, x1=y+1-0.5, y0=x-0.5, y1=x+1-0.5,
                xref='x', yref='y',
                line_color='cyan'
            )
        )
    shapes.append(go.layout.Shape(
            type='circle',
            x0=cy-0.5, x1=cy+1-0.5, y0=cx-0.5, y1=cx+1-0.5,
            xref='x', yref='y',
            line_color='red'
        )
    )
    return traces, shapes

# def make_fig(state, cx, cy, dd, anax, anay):
#     a = [[dd[item] for item in line] for line in state]
#     fig = px.imshow(a)
#     fig = go.Figure()
#     fig.add_trace(
#         go.Heatmap(z=a)
#     )
#     for x,y in zip(anax, anay):
#         fig.add_shape(
#             type='rect',
#             x0=y-0.5, x1=y+1-0.5, y0=x-0.5, y1=x+1-0.5,
#             xref='x', yref='y',
#             line_color='cyan'
#         )
#     fig.add_shape(
#         type='circle',
#         x0=cy-0.5, x1=cy+1-0.5, y0=cx-0.5, y1=cx+1-0.5,
#         xref='x', yref='y',
#         line_color='red'
#     )
#     return fig

def animation(input_file, output_file):
    input = (lambda : (yield from map(str.rstrip, open(input_file))))().__next__
    write = lambda x: sys.stdout.write(x+"\n"); writef = lambda x: print("{:.12f}".format(x))
    debug = lambda x: sys.stderr.write(x+"\n")
    YES="Yes"; NO="No"; pans = lambda v: print(YES if v else NO); INF=10**18
    LI = lambda v=0: list(map(lambda i: int(i)-v, input().split())); II=lambda : int(input()); SI=lambda : [ord(c)-ord("a") for c in input()]


    n,m = LI()
    dd = {
        "." : 0,
        "A" : 1,
        "B" : 2,
        "C" : 3,
        "a" : 1,
        "b" : 2,
        "c" : 3,
        "@" : 5,
    }
    dxy = {
        "U": (-1,0),
        "D": (1,0),
        "R": (0,1),
        "L": (0,-1)
    }
    anax = []
    anay = []
    nokori = {"a": 0, "b": 0, "c": 0}
    state = [["."]*n for _ in range(n)]
    for i in range(n):
        s = input()
        for j in range(n):
            state[i][j] = s[j]
            if s[j] in "ABC":
                anax.append(i)
                anay.append(j)
            if s[j] in "abc":
                nokori[s[j]] += 1
            if s[j]=="A":
                cx,cy = (i,j)
    input = (lambda : (yield from map(str.rstrip, open(output_file))))().__next__
    figs = [make_trace(state, cx, cy, dd, anax, anay)]
    while 1:
        try:
            s = input()
        except StopIteration:
            break
        a,d = s.split()
        a = int(a)
        dx,dy = dxy[d]
        if a==1:
            cx += dx
            cy += dy
            assert 0<=cx<n and 0<=cy<n
        elif a==2:
            # 移動させる
            assert state[cx][cy] in "abc@"
            t = state[cx][cy]
            nx = cx + dx
            ny = cy + dy
            assert 0<=nx<n and 0<=ny<n
            if state[nx][ny] not in ".ABC":
                return create_animated_figure(figs)
            assert state[nx][ny] in ".ABC"
            state[cx][cy] = "."
            if t.upper()==state[cx][cy]:
                nokori[t] -= 1
            if state[nx][ny]==".":
                state[nx][ny] = t
            cx = nx
            cy = ny
        else:
            assert a==3
            # 転がす
            if not (state[cx][cy] in "abc@"):
                return create_animated_figure(figs)
            assert state[cx][cy] in "abc@"
            i = 0
            while 1:
                nx = cx + dx*(i+1)
                ny = cy + dy*(i+1)
                if not (0<=nx<n and 0<=ny<n and state[nx][ny]=="."):
                    break
                i += 1
            if 0<=nx<n and 0<=ny<n:
                if state[nx][ny] in "ABC":
                    # 穴に落ちる
                    if state[nx][ny]==state[cx][cy].upper():
                        nokori[state[cx][cy]] -= 1
                    state[cx][cy] = "."
                elif i>0:
                    state[cx+dx*i][cy+dy*i] = state[cx][cy]
                    state[cx][cy] = "."
        figs.append(make_trace(state, cx, cy, dd, anax, anay))
        # figs.append(make_fig(state, cx, cy, dd, anax, anay))

    # return figs
    return create_animated_figure(figs)