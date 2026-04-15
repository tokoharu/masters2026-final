/********状態をそのまま持つビームサーチの雛形*******/
// ビームに状態を保持
// 各状態に対して操作を探索し、上位 B 個の (gain, 状態, 操作) を保持 ← この時点では次状態を丸々計算はしないで gain のみを計算するのがミソ
// 保持した (状態, 操作) から次のビームを作成. この際、ハッシュにより重複状態を排除


/******User Code******/
#include <queue>
#include <vector>
#include <algorithm>
#include <utility>
#include <cassert>

// K が小さいトップ n 個を保持する（Rust版 BoundedSortedList 相当）
// - can_insert(k): まだ空きがある or 現在の最悪(k最大)より良い(kが小さい)なら true
// - insert(k, v): 条件を満たすときだけ保持（満杯なら最悪要素を置換）
// - list(): (k, v) を k 昇順で返す（Rust: into_sorted_vec と同じイメージ）
template <class K, class V>
struct BoundedSortedList {
    struct Entry {
        K k;
        V v;
        // std::priority_queue は「最大」を top にするので、
        // k が大きい（=最悪）ものが top になるようにする
        bool operator<(Entry const& other) const {
            return k < other.k;
        }
    };

    std::priority_queue<Entry> que;
    std::size_t size;

    explicit BoundedSortedList(std::size_t size_) : size(size_) {}

    std::size_t len() const { return que.size(); }

    bool can_insert(K const& k) const {
        return que.size() < size || que.top().k > k;
    }

    // Rust版と同様に、満杯なら top(=最悪) を直接置き換える
    void insert(K const& k, V const& v) {
        if (size == 0) return;
        if (que.size() < size) {
            que.push(Entry{k, v});
        } else if (que.top().k > k) {
            que.pop();
            que.push(Entry{k, v});
        }
    }

    // (k, v) を k 昇順で返す
    std::vector<std::pair<K, V>> list() const {
        auto tmp = que; // コピーして破壊的に取り出す
        std::vector<std::pair<K, V>> out;
        out.reserve(tmp.size());
        while (!tmp.empty()) {
            out.emplace_back(tmp.top().k, tmp.top().v);
            tmp.pop();
        }
        std::reverse(out.begin(), out.end()); // 最大ヒープから取ると降順→反転で昇順
        return out;
    }
};

constexpr size_t BEAM_WIDTH = 1000;

struct SimpleBeamSearch {
    struct Action {
        // beam 内のどれに何をする、という情報
        int beam_ind;
    };
    struct State {
        int log_id; // この状態に至る操作のログID
        ll hash;
        State() : log_id(-1), hash(0) {}
        State(int log_id, ll hash) : log_id(log_id), hash(hash) {}
        void apply(Action const& action) {
            // action を実行して hash や cost (保持している場合) を更新
        }
        // コピーコンストラクタ
        State(State const& other) : log_id(other.log_id), hash(other.hash) {}
    };
    struct Log {
        int parent_id;
        Action action;
    };
    void search () {
        V<Log> logs;
        State init;
        V<State> beam;
        beam.push_back(init);
        
        rep(turn, N-1) {
            BoundedSortedList<ll, Action> next_bsl(BEAM_WIDTH); // (評価値(cost), 操作)
            int beam_ind = 0;
            for (auto &state : beam) {
                // action を探索
                Action a(beam_ind);
                ll cost = 0;
                if (next_bsl.can_insert(cost)) {
                    next_bsl.insert(cost, a);
                }
                beam_ind++;
            }
            V<State> nbeam;
            unordered_set<ll> used_hashes;
            for (auto [cost, a] : next_bsl.list()) {
                // 上位 BEAM_WIDTH 個の action を実行
                State &state = beam[a.beam_ind];
                State nstate = state;
                nstate.log_id = logs.size();
                nstate.apply(a);
                if (used_hashes.insert(hash).second == false) {
                    continue;
                }
                nbeam.emplace_back(nstate);
                logs.push_back(Log{state.log_id, a});
            }
            swap(beam, nbeam);
        }
        auto final_state = beam[0]; // TODO : 最も良い状態を選択
        // 復元
        V<Action> actions;
        int cur_id = final_state.log_id;
        while (cur_id != -1) {
            Log &log = logs[cur_id];
            actions.emplace_back(log.action);
            cur_id = log.parent_id;
        }
        reverse(all(actions));
        // 出力
    }
};

ll Main()
{
    return 0;
}


int main(int argc, char* argv[]){
    std::cin.tie(nullptr);
	std::ios_base::sync_with_stdio(false);
    Main();
    return 0;
}

