#pragma once
#include <bits/stdc++.h>
using namespace std;

static const int N = 32;

struct Op {
    int type;  // 0=paint, 1=copy, 2=clear
    // paint: k i j x
    // copy:  k h r di dj
    // clear: k
    int k, i, j, x;
    int h, r, di, dj;

    static Op make_paint(int k, int i, int j, int x) {
        Op o{}; o.type=0; o.k=k; o.i=i; o.j=j; o.x=x; return o;
    }
    static Op make_copy(int k, int h, int r, int di, int dj) {
        Op o{}; o.type=1; o.k=k; o.h=h; o.r=r; o.di=di; o.dj=dj; return o;
    }
    static Op make_clear(int k) {
        Op o{}; o.type=2; o.k=k; return o;
    }

    void print() const {
        if (type == 0) cout << "0 " << k << " " << i << " " << j << " " << x << "\n";
        else if (type == 1) cout << "1 " << k << " " << h << " " << r << " " << di << " " << dj << "\n";
        else cout << "2 " << k << "\n";
    }
};

// N×N グリッドを時計回り90°回転
static void rotate90_grid(int src[N][N], int dst[N][N]) {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            dst[j][N - 1 - i] = src[i][j];
}

struct Input;  // forward decl

class Solution {
    int K_, C_;
    int layer_[5][N][N];
    vector<Op> ops_;

public:
    Solution(int K, int C) : K_(K), C_(C) {
        memset(layer_, 0, sizeof(layer_));
    }

    void paint(int k, int i, int j, int x) {
        layer_[k][i][j] = x;
        ops_.push_back(Op::make_paint(k, i, j, x));
    }

    // 範囲外の非透明ピクセルがある場合 false を返す（操作は実行しない）
    bool copy_layer(int k, int h, int r, int di, int dj) {
        // layer[h] を r 回 90° 回転したバッファを作る
        int buf[N][N], tmp[N][N];
        memcpy(buf, layer_[h], sizeof(buf));
        for (int rot = 0; rot < r; rot++) {
            rotate90_grid(buf, tmp);
            memcpy(buf, tmp, sizeof(buf));
        }

        // 範囲チェック（非透明ピクセルが [0,N)×[0,N) 外に出ないか）
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                if (buf[i][j] == 0) continue;
                int ni = i + di, nj = j + dj;
                if (ni < 0 || ni >= N || nj < 0 || nj >= N) return false;
            }
        }

        // 書き込み（k==h の場合も buf 経由なので安全）
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (buf[i][j] != 0)
                    layer_[k][i + di][j + dj] = buf[i][j];

        ops_.push_back(Op::make_copy(k, h, r, di, dj));
        return true;
    }

    void clear(int k) {
        memset(layer_[k], 0, sizeof(layer_[k]));
        ops_.push_back(Op::make_clear(k));
    }

    int get(int k, int i, int j) const { return layer_[k][i][j]; }
    int op_count() const { return (int)ops_.size(); }

    void print_ops() const {
        // cout << ops_.size() << "\n";
        for (auto& op : ops_) op.print();
    }

    // layer[0] と目標 g の一致具合を評価
    int matching_pixels(const int g[N][N]) const {
        int cnt = 0;
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (layer_[0][i][j] == g[i][j] && g[i][j] != 0) cnt++;
        return cnt;
    }

    // 目標の全非透明ピクセルが layer[0] と一致しているか
    bool is_complete(const int g[N][N]) const {
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (g[i][j] != 0 && layer_[0][i][j] != g[i][j]) return false;
        return true;
    }

    double score(const int g[N][N]) const {
        int U = 0;
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                if (g[i][j] != 0) U++;
        int T = (int)ops_.size();
        if (T == 0) return 0.0;
        return round(1e6 * (1.0 + log2((double)U / T)));
    }
};
