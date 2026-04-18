
using namespace std;
#include<bits/stdc++.h>
#include<fstream>
#include <iostream>
#include <cstdlib>
#include <dirent.h>

string cur_file; // 現在実行中の入力ファイル名

#define rep(i,n) for(ll (i)=0;(i)<(ll)(n);i++)
#define rrep(i,n) for(ll (i)=(ll)(n)-1;(i)>=0;i--)
#define range(i,start,end,step) for(ll (i)=start;(i)<(ll)(end);(i)+=(step))
#define rrange(i,start,end,step) for(ll (i)=start;(i)>(ll)(end);(i)+=(step))

#define dump(x)  cerr << "Line " << __LINE__ << ": " <<  #x << " = " << (x) << "\n";
#define spa << " " <<
#define cma << "," <<
#define fi first
#define se second
#define all(a)  (a).begin(),(a).end()
#define allr(a)  (a).rbegin(),(a).rend()

using ld = long double;
using ll = long long;
using ull = unsigned long long;
using pii = pair<int, int>;
using pll = pair<ll, ll>;
using pdd = pair<ld, ld>;
 
template<typename T> using V = vector<T>;
template<typename T> using VV = V<V<T>>;
template<typename T, typename T2> using P = pair<T, T2>;
template<typename T, typename T2> using M = map<T, T2>;
template<typename T> using S = set<T>;
template<typename T, typename T2> using UM = unordered_map<T, T2>;
template<typename T> using PQ = priority_queue<T, V<T>, greater<T>>;
template<typename T> using rPQ = priority_queue<T, V<T>, less<T>>;
template<class T>vector<T> make_vec(size_t a){return vector<T>(a);}
template<class T, class... Ts>auto make_vec(size_t a, Ts... ts){return vector<decltype(make_vec<T>(ts...))>(a, make_vec<T>(ts...));}
template<class SS, class T> ostream& operator << (ostream& os, const pair<SS, T> v){os << "(" << v.first << ", " << v.second << ")"; return os;}
template<typename T> ostream& operator<<(ostream &os, const vector<T> &v) { for (auto &e : v) os << e << ' '; return os; }
template<class T> ostream& operator<<(ostream& os, const vector<vector<T>> &v){ for(auto &e : v){os << e << "\n";} return os;}
struct fast_ios { fast_ios(){ cin.tie(nullptr); ios::sync_with_stdio(false); cout << fixed << setprecision(20); }; } fast_ios_;
 
template <class T> void UNIQUE(vector<T> &x) {sort(all(x));x.erase(unique(all(x)), x.end());}
template<class T> bool chmax(T &a, const T &b) { if (a<b) { a=b; return 1; } return 0; }
template<class T> bool chmin(T &a, const T &b) { if (a>b) { a=b; return 1; } return 0; }
void fail() { cout << -1 << '\n'; exit(0); }
inline int popcount(const int x) { return __builtin_popcount(x); }
inline int popcount(const ll x) { return __builtin_popcountll(x); }
template<typename T> void debug(vector<vector<T>>&v){for(ll i=0;i<v.size();i++)
{cerr<<v[i][0];for(ll j=1;j<v[i].size();j++)cerr spa v[i][j];cerr<<"\n";}};
template<typename T> void debug(vector<T>&v){if(v.size()!=0)cerr<<v[0];
for(ll i=1;i<v.size();i++)cerr spa v[i];
cerr<<"\n";};
template<typename T> void debug(priority_queue<T>&v){V<T> vals; while(!v.empty()) {cerr << v.top() << " "; vals.push_back(v.top()); v.pop();} cerr<<"\n"; for(auto val: vals) v.push(val);}
template<typename T, typename T2> void debug(map<T,T2>&v){for(auto [k,v]: v) cerr << k spa v << "\n"; cerr<<"\n";}
template<typename T, typename T2> void debug(unordered_map<T,T2>&v){for(auto [k,v]: v) cerr << k spa v << "\n";cerr<<"\n";}
V<int> listrange(int n) {V<int> res(n); rep(i,n) res[i]=i; return res;}

template<typename T> P<T,T> divmod(T a, T b) {return make_pair(a/b, a%b);}
template<typename T> T SUM(V<T> a){T val(0); for (auto v : a) val += v; return val;}


const ll INF = (1ll<<62);
// const ld EPS   = 1e-10;
// const ld PI    = acos(-1.0);

static unsigned int xxx=123456789,yyy=362436069,zzz=521288629,www=88675123;
unsigned int randxor()
{
    unsigned int t;
    t=(xxx^(xxx<<11));xxx=yyy;yyy=zzz;zzz=www; return( www=(www^(www>>19))^(t^(t>>8)) );
}
V<unsigned int> _rs;
const int RAND_SIZE = 100000;
int _rs_ind = 0;
inline unsigned int randint() {
    ++_rs_ind;
    if (_rs_ind==RAND_SIZE) _rs_ind = 0;
    return _rs[_rs_ind];
}

int random_select(V<ll> &vals) {
    // vals の重みで [0, vals.size()) からサンプリング
    ll s = 0;
    for (auto v : vals) s += v;
    ll val = randint()%s;
    rep(i, vals.size()) {val -= vals[i]; if (val<=0) return i;}
    return vals.size()-1;
}
const int BUNBO = 1e9;
double uniform_rand () {
    return double(randxor()%BUNBO+1) / double(BUNBO);
}

V<double> TIME_LIST;
auto _START_TIME = chrono::system_clock::now();
double current_time() {
    return chrono::duration_cast<chrono::microseconds>(chrono::system_clock::now() - _START_TIME).count() * 1e-6;
}

// ソルバークラスのひな型

const double T_START = 5000;
const double T_FINAL = 1;
const double T_RATE = T_FINAL / T_START;
const double TIME_LIMIT = 1.9;
const bool SA = 0;

struct Board {
    // 焼きなましの雛形
    inline double temp(double t_now, double tl, double t0) {
        // 指数減衰
        return T_START * pow(T_RATE, ((t_now - t0) / (tl - t0)));
    }
    int try_update_0(double thred) {
        // スコア差分 thred より良ければ内部状態を更新する
        // 更新したかの 0/1 を返す
        return 0;
    }
    int try_update_1(double thred) {
        // スコア差分 thred より良ければ内部状態を更新する
        // 更新したかの 0/1 を返す
        return 0;
    }
    void sa(double tl) {
        // 時間制限 tl まで実行する
        int rc = 0;
        int suc = 0;
        V<int> suc_lst(5); // 各近傍の成功数のカウント
        V<int> rc_lst(5); // 各近傍の成功数のカウント
        double t_now;
        double t0 = current_time();
        while (true) {
            if ((t_now=current_time())>=tl) break;
            double thred;
            if (SA) thred = log(uniform_rand()) * temp(t_now, tl, t0);
            else thred = 0;
            int r = randint()%100;
            P<int,int> res; // {近傍種類, 成否}
            if (r<15) res = {0, try_update_0(thred)};
            else res = {1, try_update_1(thred)};
            if (res.second) {
                suc_lst[res.first]++;
                suc++;
            }
            rc_lst[res.first]++;
            rc++;
        }
        debug(rc_lst);
        debug(suc_lst);
    }
};


ll Main() {
    // スコアを返す
    rep(i,RAND_SIZE) {
        _rs.emplace_back(randxor());
    }
    
    int n,t;
    cin >> n >> t;
    cout << n spa t << endl;

    // ofstream writer("out/result.csv", ios::app);
    // writer << n cma t << endl;
    return 0;
}

int main(int argc, char* argv[]){
    std::cin.tie(nullptr);
	std::ios_base::sync_with_stdio(false);
    Main();
    return 0;
}