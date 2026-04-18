#include <bits/stdc++.h>
#include "solution.hpp"
using namespace std;

static const int B = 4;  // 小盤面サイズ

struct Input {
    int K, C;
    int g[N][N];  // g[i][j]: 0=透明, 1..C=色

    void read() {
        int n;
        cin >> n >> K >> C;
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                cin >> g[i][j];
    }
};

uint64_t zobrist[B * B][5];

void init_zobrist() {
    mt19937_64 rng(20260418ULL);
    for (int pos = 0; pos < B * B; pos++)
        for (int c = 1; c <= 4; c++)
            zobrist[pos][c] = rng();
}

using Block = array<array<int, B>, B>;

Block rotate90(const Block& src) {
    Block dst{};
    for (int i = 0; i < B; i++)
        for (int j = 0; j < B; j++)
            dst[j][B - 1 - i] = src[i][j];
    return dst;
}

uint64_t hash_block(const Block& b) {
    uint64_t h = 0;
    for (int i = 0; i < B; i++)
        for (int j = 0; j < B; j++)
            if (b[i][j] != 0)
                h ^= zobrist[i * B + j][b[i][j]];
    return h;
}

bool all_transparent(const Block& b) {
    for (int i = 0; i < B; i++)
        for (int j = 0; j < B; j++)
            if (b[i][j] != 0) return false;
    return true;
}

struct BlockInfo {
    int si, sj;
    Block blk;
    array<uint64_t, 4> rot_hashes;  // rot_hashes[r] = hash(rotate(blk, r))
};

// copy(k, h, r, di, dj) の操作パラメータ
struct Transform {
    int di, dj, r;
    bool operator<(const Transform& o) const {
        return tie(di, dj, r) < tie(o.di, o.dj, o.r);
    }
};

// src ブロックを r 回転して copy したとき dst に一致するペア
struct MatchedPair {
    int src_si, src_sj;
    int dst_si, dst_sj;
};

struct TransformResult {
    Transform t;
    int count;
    vector<MatchedPair> pairs;
};

// セル (i, j) を回転 r・オフセット (di, dj) で変換した dst を返す。範囲外は (-1,-1)
pair<int,int> cell_transform(int i, int j, int r, int di, int dj) {
    int ri, rj;
    switch (r) {
        case 0: ri = i;       rj = j;         break;
        case 1: ri = j;       rj = N-1-i;     break;
        case 2: ri = N-1-i;   rj = N-1-j;     break;
        case 3: ri = N-1-j;   rj = i;         break;
        default: return {-1,-1};
    }
    ri += di; rj += dj;
    if (ri < 0 || ri >= N || rj < 0 || rj >= N) return {-1,-1};
    return {ri, rj};
}

struct AdoptedPair {
    int src_i, src_j;
    int dst_i, dst_j;
    bool type_a;  // g[src]==g[dst]
};

struct PrevStateResult {
    vector<AdoptedPair> pairs;
    int saving;  // |D \ S| - |Sb| - 1
};

// find_copy_transforms 上位候補の Transform に対して
// type-a (色一致) をシードに 0-1 BFS 拡張し saving を返す
// type-b (色不一致) は近傍の橋渡しとして後回しに追加
// saving = |D \ S| - |Sb| - 1
PrevStateResult find_best_prev_state(const Input& inp, Transform t) {
    vector<bool> adopted(N * N, false);
    vector<AdoptedPair> pairs;

    deque<pair<int,int>> bfs;  // 0-1 BFS: type-a→front, type-b→back

    auto try_add = [&](int si, int sj) {
        if (si < 0 || si >= N || sj < 0 || sj >= N) return;
        auto [di_, dj_] = cell_transform(si, sj, t.r, t.di, t.dj);
        if (di_ < 0) return;
        if (inp.g[si][sj] == 0 || inp.g[di_][dj_] == 0) return;
        if (adopted[si * N + sj] && adopted[di_ * N + dj_]) return;
        bool is_a = (inp.g[si][sj] == inp.g[di_][dj_]);
        adopted[si * N + sj] = true;
        adopted[di_ * N + dj_] = true;
        pairs.push_back({si, sj, di_, dj_, is_a});
        if (is_a) bfs.push_front({si, sj});
        else       bfs.push_back({si, sj});
    };

    // シード: type-a のみ先にキューへ
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            auto [di_, dj_] = cell_transform(i, j, t.r, t.di, t.dj);
            if (di_ < 0) continue;
            if (inp.g[i][j] == 0 || inp.g[di_][dj_] == 0) continue;
            if (inp.g[i][j] != inp.g[di_][dj_]) continue;  // type-b はスキップ
            if (adopted[i * N + j] && adopted[di_ * N + dj_]) continue;
            adopted[i * N + j] = true;
            adopted[di_ * N + dj_] = true;
            pairs.push_back({i, j, di_, dj_, true});
            bfs.push_back({i, j});
        }

    // 0-1 BFS で隣接セルを拡張（type-a→front, type-b→back）
    const int di4[] = {-1, 1, 0, 0};
    const int dj4[] = {0, 0, -1, 1};
    while (!bfs.empty()) {
        auto [si, sj] = bfs.front(); bfs.pop_front();
        for (int d = 0; d < 4; d++)
            try_add(si + di4[d], sj + dj4[d]);
    }

    // saving = |D \ S| - |Sb| - 1
    set<pair<int,int>> S;
    for (auto& p : pairs) S.insert({p.src_i, p.src_j});
    int d_minus_s = 0, nb = 0;
    for (auto& p : pairs) {
        if (!S.count({p.dst_i, p.dst_j})) d_minus_s++;
        if (!p.type_a) nb++;
    }

    return {pairs, d_minus_s - nb - 1};
}

// ブロックペア (src→dst, rotation r) から実際の copy 操作パラメータを計算
// rotate(src_layer, r) を (di, dj) に配置すると dst 位置に src ブロックが貼られる
pair<int,int> block_to_copy_params(int si_a, int sj_a, int si_b, int sj_b, int r) {
    switch (r) {
        case 0: return {si_b - si_a,           sj_b - sj_a};
        case 1: return {si_b - sj_a,           sj_b + si_a - (N - B)};
        case 2: return {si_b + si_a - (N - B), sj_b + sj_a - (N - B)};
        case 3: return {si_b + sj_a - (N - B), sj_b - si_a};
        default: return {INT_MIN, INT_MIN};
    }
}

// 盤面 g の全 4×4 スライディングウィンドウを対象に
// copy(k, h, r, di, dj) でまとめて再現できるブロックペアを集計し
// ペア数の多い順に返す
vector<TransformResult> find_copy_transforms(const Input& inp) {
    static const int SLIDE = N - B + 1;  // = 29

    // 全ブロックを列挙し 4 回転分のハッシュを計算
    vector<BlockInfo> blocks;
    for (int si = 0; si < SLIDE; si++) {
        for (int sj = 0; sj < SLIDE; sj++) {
            Block blk{};
            for (int i = 0; i < B; i++)
                for (int j = 0; j < B; j++)
                    blk[i][j] = inp.g[si + i][sj + j];
            if (all_transparent(blk)) continue;

            BlockInfo bi;
            bi.si = si; bi.sj = sj; bi.blk = blk;
            Block cur = blk;
            for (int r = 0; r < 4; r++) {
                bi.rot_hashes[r] = hash_block(cur);
                cur = rotate90(cur);
            }
            blocks.push_back(bi);
        }
    }

    // rot_index[r][h] : rot_hashes[r] == h のブロックインデックス列
    array<unordered_map<uint64_t, vector<int>>, 4> rot_index;
    for (int idx = 0; idx < (int)blocks.size(); idx++)
        for (int r = 0; r < 4; r++)
            rot_index[r][blocks[idx].rot_hashes[r]].push_back(idx);

    // rotate(A, r) == B  ⟺  A.rot_hashes[r] == B.rot_hashes[0]
    map<Transform, vector<MatchedPair>> transform_pairs;
    for (int a = 0; a < (int)blocks.size(); a++) {
        const auto& A = blocks[a];
        for (int r = 0; r < 4; r++) {
            auto it = rot_index[0].find(A.rot_hashes[r]);
            if (it == rot_index[0].end()) continue;
            for (int b : it->second) {
                if (b == a) continue;
                const auto& Bk = blocks[b];
                auto [cdi, cdj] = block_to_copy_params(
                    A.si, A.sj, Bk.si, Bk.sj, r);
                transform_pairs[{cdi, cdj, r}].push_back(
                    {A.si, A.sj, Bk.si, Bk.sj});
            }
        }
    }

    // ペア数の多い順にソートして返す
    vector<TransformResult> results;
    for (auto& [t, pairs] : transform_pairs)
        results.push_back({t, (int)pairs.size(), move(pairs)});
    sort(results.begin(), results.end(),
         [](const TransformResult& a, const TransformResult& b) {
             return a.count > b.count;
         });
    return results;
}

int solve_toko() {
    Input inp;
    inp.read();
    init_zobrist();

    // --- copy 変換候補の探索 ---
    auto results = find_copy_transforms(inp);
    // --- 上位 top_n 候補の saving を計算し最大を選択 ---
    int best_saving = -1;
    PrevStateResult best_ps;
    Transform best_t{};
    int top_n = min((int)results.size(), 10);
    for (int z = 0; z < top_n; z++) {
        auto ps = find_best_prev_state(inp, results[z].t);
        if (!results.empty() && z == 0) {
            cerr << "=== 上位候補 saving ===\n";
        }
        cerr << "  di=" << setw(4) << results[z].t.di
             << " dj=" << setw(4) << results[z].t.dj
             << " r=" << results[z].t.r
             << "  saving=" << ps.saving
             << "  pairs=" << ps.pairs.size() << "\n";
        if (ps.saving > best_saving) {
            best_saving = ps.saving;
            best_ps = ps;
            best_t = results[z].t;
        }
    }

    Solution sol(inp.K, inp.C);

    if (best_saving > 0) {
        // Step 1: src を layer 0 にペイント
        //   type-a: h[src] = g[src] (= g[dst])
        //   type-b: h[src] = g[dst]  → copy 後に dst が正しくなる
        for (auto& p : best_ps.pairs) {
            int paint_color = p.type_a ? inp.g[p.src_i][p.src_j]
                                       : inp.g[p.dst_i][p.dst_j];
            sol.paint(0, p.src_i, p.src_j, paint_color);
        }

        // Step 2: self-copy → dst に正しい色が転写される
        sol.copy_layer(0, 0, best_t.r, best_t.di, best_t.dj);

        // Step 3: type-b の src を g[src] で上書き（copy 後は h[src]=g[dst] のまま）
        for (auto& p : best_ps.pairs) {
            if (!p.type_a)
                sol.paint(0, p.src_i, p.src_j, inp.g[p.src_i][p.src_j]);
        }

        // Step 4: 残りの g マスをペイント
        set<pair<int,int>> covered;
        for (auto& p : best_ps.pairs) {
            covered.insert({p.src_i, p.src_j});
            covered.insert({p.dst_i, p.dst_j});
        }
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (inp.g[i][j] != 0 && !covered.count({i, j}))
                    sol.paint(0, i, j, inp.g[i][j]);

        cerr << "copy strategy: saving=" << best_saving
             << " di=" << best_t.di << " dj=" << best_t.dj << " r=" << best_t.r << "\n";
    } else {
        // ベースライン：全 paint
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (inp.g[i][j] != 0)
                    sol.paint(0, i, j, inp.g[i][j]);
        cerr << "baseline (no useful copy found)\n";
    }

    cerr << "ops=" << sol.op_count()
         << " complete=" << sol.is_complete(inp.g)
         << " score=" << (int)sol.score(inp.g) << "\n";

    sol.print_ops();
    return 0;
}

int main(){

    solve_toko();
}
