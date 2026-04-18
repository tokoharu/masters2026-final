#include <bits/stdc++.h>
using namespace std;

struct Action {
    int type;
    int k;
    int a;
    int b;
    int c;
    int d;
};

struct Segment {
    int fixed;
    int start;
    int len;
    bool vertical;
};

struct Block {
    int left;
    int right;
    vector<int> color_positions;
};

struct CopyPlacement {
    int r;
    int di;
    int dj;
};

struct LinePlan {
    int fixed;
    int left;
    int right;
    int cost;
    bool vertical;
    vector<Segment> segments;
};

static const int DR[4] = {-1, 1, 0, 0};
static const int DC[4] = {0, 0, -1, 1};

struct DinicEdge {
    int to;
    int rev;
    int cap;
};

struct Dinic {
    int n;
    vector<vector<DinicEdge>> g;
    vector<int> level;
    vector<int> it;

    explicit Dinic(int n) : n(n), g(n), level(n), it(n) {}

    void add_edge(int fr, int to, int cap) {
        DinicEdge fwd{to, static_cast<int>(g[to].size()), cap};
        DinicEdge rev{fr, static_cast<int>(g[fr].size()), 0};
        g[fr].push_back(fwd);
        g[to].push_back(rev);
    }

    bool bfs(int s, int t) {
        fill(level.begin(), level.end(), -1);
        queue<int> q;
        level[s] = 0;
        q.push(s);
        while (!q.empty()) {
            int v = q.front();
            q.pop();
            for (const auto& e : g[v]) {
                if (e.cap <= 0 || level[e.to] != -1) {
                    continue;
                }
                level[e.to] = level[v] + 1;
                q.push(e.to);
            }
        }
        return level[t] != -1;
    }

    int dfs(int v, int t, int f) {
        if (v == t) {
            return f;
        }
        for (int& i = it[v]; i < static_cast<int>(g[v].size()); ++i) {
            DinicEdge& e = g[v][i];
            if (e.cap <= 0 || level[v] >= level[e.to]) {
                continue;
            }
            int pushed = dfs(e.to, t, min(f, e.cap));
            if (pushed == 0) {
                continue;
            }
            e.cap -= pushed;
            g[e.to][e.rev].cap += pushed;
            return pushed;
        }
        return 0;
    }

    int max_flow(int s, int t) {
        int flow = 0;
        const int inf = 1e9;
        while (bfs(s, t)) {
            fill(it.begin(), it.end(), 0);
            while (true) {
                int pushed = dfs(s, t, inf);
                if (pushed == 0) {
                    break;
                }
                flow += pushed;
            }
        }
        return flow;
    }

    vector<char> reachable_from(int s) {
        vector<char> seen(n, 0);
        queue<int> q;
        q.push(s);
        seen[s] = 1;
        while (!q.empty()) {
            int v = q.front();
            q.pop();
            for (const auto& e : g[v]) {
                if (e.cap <= 0 || seen[e.to]) {
                    continue;
                }
                seen[e.to] = 1;
                q.push(e.to);
            }
        }
        return seen;
    }
};

static vector<Action> build_naive(const vector<vector<int>>& target) {
    int n = static_cast<int>(target.size());
    vector<Action> actions;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (target[i][j] != 0) {
                actions.push_back({0, 0, i, j, target[i][j], 0});
            }
        }
    }
    return actions;
}

static vector<int> used_colors(const vector<vector<int>>& target, int color_count) {
    vector<int> seen(color_count + 1, 0);
    for (const auto& row : target) {
        for (int value : row) {
            if (value != 0) {
                seen[value] = 1;
            }
        }
    }
    vector<int> colors;
    for (int color = 1; color <= color_count; ++color) {
        if (seen[color]) {
            colors.push_back(color);
        }
    }
    return colors;
}

static vector<Segment> solve_blocks(const vector<Block>& blocks, int fixed, bool vertical) {
    vector<Segment> segments;
    for (const auto& block : blocks) {
        if (block.color_positions.empty()) {
            continue;
        }
        int m = static_cast<int>(block.color_positions.size());
        const int inf = 1e9;
        vector<int> dp(m + 1, inf);
        vector<int> next_index(m, -1);
        vector<int> best_right(m, -1);
        dp[m] = 0;
        for (int idx = m - 1; idx >= 0; --idx) {
            int start = block.color_positions[idx];
            for (int end = start; end <= block.right; ++end) {
                int covered = upper_bound(block.color_positions.begin(), block.color_positions.end(), end) - block.color_positions.begin();
                int cost = __builtin_popcount(static_cast<unsigned>(end - start + 1)) + dp[covered];
                if (cost < dp[idx]) {
                    dp[idx] = cost;
                    next_index[idx] = covered;
                    best_right[idx] = end;
                }
            }
        }

        int idx = 0;
        while (idx < m) {
            int start = block.color_positions[idx];
            int end = best_right[idx];
            segments.push_back({fixed, start, end - start + 1, vertical});
            idx = next_index[idx];
        }
    }
    return segments;
}

static LinePlan plan_block(const Block& block, int fixed, bool vertical) {
    int m = static_cast<int>(block.color_positions.size());
    const int inf = 1e9;
    vector<int> dp(m + 1, inf);
    vector<int> next_index(m, -1);
    vector<int> best_right(m, -1);
    dp[m] = 0;
    for (int idx = m - 1; idx >= 0; --idx) {
        int start = block.color_positions[idx];
        for (int end = start; end <= block.right; ++end) {
            int covered = upper_bound(block.color_positions.begin(), block.color_positions.end(), end) - block.color_positions.begin();
            int cost = __builtin_popcount(static_cast<unsigned>(end - start + 1)) + dp[covered];
            if (cost < dp[idx]) {
                dp[idx] = cost;
                next_index[idx] = covered;
                best_right[idx] = end;
            }
        }
    }

    vector<Segment> segments;
    int idx = 0;
    while (idx < m) {
        int start = block.color_positions[idx];
        int end = best_right[idx];
        segments.push_back({fixed, start, end - start + 1, vertical});
        idx = next_index[idx];
    }
    return {fixed, block.left, block.right, dp[0], vertical, segments};
}

static vector<vector<char>> build_active_mask(
    const vector<vector<int>>& target,
    const vector<int>& order,
    int step_index
) {
    int n = static_cast<int>(target.size());
    vector<int> fixed_big(16, 0);
    for (int idx = 0; idx < step_index; ++idx) {
        int prev_color = order[idx];
        if (prev_color >= static_cast<int>(fixed_big.size())) {
            fixed_big.resize(prev_color + 1, 0);
        }
        fixed_big[prev_color] = 1;
    }

    vector<vector<char>> active(n, vector<char>(n, 0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            int value = target[i][j];
            if (value == 0) {
                continue;
            }
            if (value < static_cast<int>(fixed_big.size()) && fixed_big[value]) {
                continue;
            }
            active[i][j] = 1;
        }
    }
    return active;
}

static vector<Segment> collect_segments_from_mask(
    const vector<vector<int>>& target,
    const vector<vector<char>>& active,
    int color,
    bool vertical
) {
    int n = static_cast<int>(target.size());

    vector<Segment> segments;
    for (int fixed = 0; fixed < n; ++fixed) {
        int pos = 0;
        vector<Block> blocks;
        while (pos < n) {
            while (pos < n) {
                int row = vertical ? pos : fixed;
                int col = vertical ? fixed : pos;
                if (active[row][col]) {
                    break;
                }
                ++pos;
            }
            if (pos >= n) {
                break;
            }
            int left = pos;
            vector<int> color_positions;
            while (pos < n) {
                int row = vertical ? pos : fixed;
                int col = vertical ? fixed : pos;
                if (!active[row][col]) {
                    break;
                }
                if (target[row][col] == color) {
                    color_positions.push_back(pos);
                }
                ++pos;
            }
            int right = pos;
            if (!color_positions.empty()) {
                blocks.push_back({left, right - 1, color_positions});
            }
        }

        vector<Segment> line_segments = solve_blocks(blocks, fixed, vertical);
        for (const auto& segment : line_segments) {
            segments.push_back(segment);
        }
    }
    return segments;
}

static vector<LinePlan> collect_line_plans_from_mask(
    const vector<vector<int>>& target,
    const vector<vector<char>>& active,
    int color,
    bool vertical,
    vector<vector<int>>& plan_id
) {
    int n = static_cast<int>(target.size());
    vector<LinePlan> plans;
    for (int fixed = 0; fixed < n; ++fixed) {
        int pos = 0;
        while (pos < n) {
            while (pos < n) {
                int row = vertical ? pos : fixed;
                int col = vertical ? fixed : pos;
                if (active[row][col]) {
                    break;
                }
                ++pos;
            }
            if (pos >= n) {
                break;
            }

            int left = pos;
            vector<int> color_positions;
            while (pos < n) {
                int row = vertical ? pos : fixed;
                int col = vertical ? fixed : pos;
                if (!active[row][col]) {
                    break;
                }
                if (target[row][col] == color) {
                    color_positions.push_back(pos);
                }
                ++pos;
            }
            if (color_positions.empty()) {
                continue;
            }

            Block block{left, pos - 1, color_positions};
            int id = static_cast<int>(plans.size());
            plans.push_back(plan_block(block, fixed, vertical));
            for (int line_pos : color_positions) {
                int row = vertical ? line_pos : fixed;
                int col = vertical ? fixed : line_pos;
                plan_id[row][col] = id;
            }
        }
    }
    return plans;
}

static vector<Segment> build_mixed_segments(
    const vector<vector<int>>& target,
    const vector<vector<char>>& active,
    int color,
    int row_bias,
    int col_bias
) {
    int n = static_cast<int>(target.size());
    vector<vector<int>> row_id(n, vector<int>(n, -1));
    vector<vector<int>> col_id(n, vector<int>(n, -1));
    vector<LinePlan> row_plans = collect_line_plans_from_mask(target, active, color, false, row_id);
    vector<LinePlan> col_plans = collect_line_plans_from_mask(target, active, color, true, col_id);

    int left_count = static_cast<int>(row_plans.size());
    int right_count = static_cast<int>(col_plans.size());
    if (left_count == 0 || right_count == 0) {
        vector<Segment> fallback;
        for (const auto& plan : row_plans) {
            fallback.insert(fallback.end(), plan.segments.begin(), plan.segments.end());
        }
        if (fallback.empty()) {
            for (const auto& plan : col_plans) {
                fallback.insert(fallback.end(), plan.segments.begin(), plan.segments.end());
            }
        }
        return fallback;
    }

    int source = left_count + right_count;
    int sink = source + 1;
    Dinic dinic(sink + 1);
    for (int i = 0; i < left_count; ++i) {
        dinic.add_edge(source, i, row_plans[i].cost + row_bias);
    }
    for (int j = 0; j < right_count; ++j) {
        dinic.add_edge(left_count + j, sink, col_plans[j].cost + col_bias);
    }

    const int inf = 1e9;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (!active[i][j] || target[i][j] != color) {
                continue;
            }
            int rid = row_id[i][j];
            int cid = col_id[i][j];
            if (rid == -1 || cid == -1) {
                continue;
            }
            dinic.add_edge(rid, left_count + cid, inf);
        }
    }

    dinic.max_flow(source, sink);
    vector<char> reach = dinic.reachable_from(source);
    vector<Segment> mixed;
    for (int i = 0; i < left_count; ++i) {
        if (!reach[i]) {
            mixed.insert(mixed.end(), row_plans[i].segments.begin(), row_plans[i].segments.end());
        }
    }
    for (int j = 0; j < right_count; ++j) {
        if (reach[left_count + j]) {
            mixed.insert(mixed.end(), col_plans[j].segments.begin(), col_plans[j].segments.end());
        }
    }
    return mixed;
}

static vector<vector<CopyPlacement>> collect_placements(const vector<Segment>& segments, int n) {
    vector<vector<CopyPlacement>> placements(6);
    for (const auto& segment : segments) {
        int cursor = segment.start;
        for (int bit = 0; bit < 6; ++bit) {
            if (((segment.len >> bit) & 1) == 0) {
                continue;
            }
            if (segment.vertical) {
                placements[bit].push_back({1, cursor, segment.fixed - (n - 1)});
            } else {
                placements[bit].push_back({0, segment.fixed, cursor});
            }
            cursor += 1 << bit;
        }
    }

    return placements;
}

static vector<pair<int, int>> split_bits_into_batches(const vector<int>& used_bits, int workspace_count) {
    int m = static_cast<int>(used_bits.size());
    const int inf = 1e9;
    vector<int> dp(m + 1, inf);
    vector<int> next_index(m + 1, -1);
    dp[m] = 0;
    for (int i = m - 1; i >= 0; --i) {
        for (int j = i; j < m && j < i + workspace_count; ++j) {
            int batch_size = j - i + 1;
            int batch_cost = 2 + used_bits[j] + 2 * (batch_size - 1);
            if (batch_cost + dp[j + 1] < dp[i]) {
                dp[i] = batch_cost + dp[j + 1];
                next_index[i] = j + 1;
            }
        }
    }

    vector<pair<int, int>> batches;
    for (int i = 0; i < m; i = next_index[i]) {
        batches.push_back({i, next_index[i]});
    }
    return batches;
}

static vector<Action> build_actions_for_segments(
    const vector<Segment>& segments,
    int layer_count,
    int color,
    int n
) {
    vector<Action> actions;
    int workspace_count = max(1, layer_count - 1);
    vector<vector<CopyPlacement>> placements = collect_placements(segments, n);
    vector<int> used_bits;
    for (int bit = 0; bit < 6; ++bit) {
        if (!placements[bit].empty()) {
            used_bits.push_back(bit);
        }
    }

    vector<pair<int, int>> batches = split_bits_into_batches(used_bits, workspace_count);
    for (const auto& [left, right] : batches) {
        int batch_size = right - left;
        int current_layer = batch_size;
        vector<int> layer_for_bit(6, -1);

        actions.push_back({2, current_layer, 0, 0, 0, 0});
        actions.push_back({0, current_layer, 0, 0, color, 0});

        int current_bit = 0;
        int current_len = 1;
        for (int idx = 0; idx < batch_size; ++idx) {
            int bit = used_bits[left + idx];
            while (current_bit < bit) {
                actions.push_back({1, current_layer, current_layer, 0, 0, current_len});
                current_len <<= 1;
                ++current_bit;
            }

            if (idx + 1 < batch_size) {
                int preserved_layer = idx + 1;
                actions.push_back({2, preserved_layer, 0, 0, 0, 0});
                actions.push_back({1, preserved_layer, current_layer, 0, 0, 0});
                layer_for_bit[bit] = preserved_layer;
            } else {
                layer_for_bit[bit] = current_layer;
            }
        }

        for (int idx = 0; idx < batch_size; ++idx) {
            int bit = used_bits[left + idx];
            int src_layer = layer_for_bit[bit];
            for (const auto& placement : placements[bit]) {
                actions.push_back({1, 0, src_layer, placement.r, placement.di, placement.dj});
            }
        }
    }

    return actions;
}

static vector<Action> build_direct_paint_actions(
    const vector<vector<int>>& target,
    const vector<vector<char>>& active,
    int color
) {
    int n = static_cast<int>(target.size());
    vector<Action> actions;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (active[i][j] && target[i][j] == color) {
                actions.push_back({0, 0, i, j, color, 0});
            }
        }
    }
    return actions;
}

static vector<Action> build_for_order(
    const vector<vector<int>>& target,
    int layer_count,
    const vector<int>& order
) {
    vector<Action> actions;
    if (layer_count <= 1 || order.empty()) {
        return build_naive(target);
    }

    for (int step_index = 0; step_index < static_cast<int>(order.size()); ++step_index) {
        int color = order[step_index];
        vector<vector<char>> active = build_active_mask(target, order, step_index);
        vector<Action> direct_actions = build_direct_paint_actions(target, active, color);
        vector<Segment> row_segments = collect_segments_from_mask(target, active, color, false);
        if (row_segments.empty()) {
            continue;
        }
        vector<Segment> col_segments = collect_segments_from_mask(target, active, color, true);
        int n = static_cast<int>(target.size());
        vector<Action> row_actions = build_actions_for_segments(row_segments, layer_count, color, n);
        vector<Action> col_actions = build_actions_for_segments(col_segments, layer_count, color, n);
        const vector<Action>* best = &direct_actions;
        if (row_actions.size() < best->size()) {
            best = &row_actions;
        }
        if (col_actions.size() < best->size()) {
            best = &col_actions;
        }

        static const int biases[] = {0, 1, 2, 3, 4};
        vector<Action> best_mixed_actions;
        for (int row_bias : biases) {
            for (int col_bias : biases) {
                vector<Segment> mixed_segments = build_mixed_segments(target, active, color, row_bias, col_bias);
                vector<Action> mixed_actions = build_actions_for_segments(mixed_segments, layer_count, color, n);
                if (!mixed_actions.empty() && (best_mixed_actions.empty() || mixed_actions.size() < best_mixed_actions.size())) {
                    best_mixed_actions = std::move(mixed_actions);
                }
            }
        }
        if (!best_mixed_actions.empty() && best_mixed_actions.size() < best->size()) {
            best = &best_mixed_actions;
        }
        actions.insert(actions.end(), best->begin(), best->end());
    }

    return actions;
}

static void print_actions(const vector<Action>& actions) {
    for (const auto& action : actions) {
        if (action.type == 0) {
            cout << 0 << ' ' << action.k << ' ' << action.a << ' ' << action.b << ' ' << action.c << '\n';
        } else if (action.type == 1) {
            cout << 1 << ' ' << action.k << ' ' << action.a << ' ' << action.b << ' ' << action.c << ' ' << action.d << '\n';
        } else {
            cout << 2 << ' ' << action.k << '\n';
        }
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k, c;
    cin >> n >> k >> c;
    vector<vector<int>> target(n, vector<int>(n));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            cin >> target[i][j];
        }
    }

    vector<Action> best_actions = build_naive(target);
    vector<int> colors = used_colors(target, c);
    if (!colors.empty()) {
        sort(colors.begin(), colors.end());
        do {
            vector<Action> candidate = build_for_order(target, k, colors);
            if (candidate.size() <= static_cast<size_t>(n * n) && candidate.size() < best_actions.size()) {
                best_actions = std::move(candidate);
            }
        } while (next_permutation(colors.begin(), colors.end()));
    }

    print_actions(best_actions);
    return 0;
}
