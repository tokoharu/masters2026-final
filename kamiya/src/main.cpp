#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, K, C;
    cin >> N >> K >> C;
    vector<vector<int>> g(N, vector<int>(N));
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            cin >> g[i][j];
        }
    }

    // Greedy baseline: directly paint all non-zero target cells on layer 0.
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            if (g[i][j] != 0) {
                cout << 0 << ' ' << 0 << ' ' << i << ' ' << j << ' ' << g[i][j] << '\n';
            }
        }
    }

    return 0;
}
