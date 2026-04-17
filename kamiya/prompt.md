heur/ahc063 内の環境構築をしたい。
./problem.pdf をよく読んで、./pahcer_config.toml, ../visualizer.py を整えて。
必要に応じ、../../masters2026-qual を参考にして。

visualizer は以下の要件を満たす。
- Python 言語
- run.sh を実行すると、pahcer run 内で visualizer が実行される。
- tools/vis/ 以下に HTML ファイルとして出力する。
- pahcer run でスコアが出せる。
- コマンドライン引数は以下のとおり。
  - 問題の入力ファイル（例：tools/in/0000.txt）
  - 問題の出力ファイル（例：tools/out/0000.txt）
  - 可視化の出力 HTML ファイル（例：tools/vis/0000.txt）
- ディレクトリがない場合は、作成する。
- スライダーを用いたアニメーション。
- 用途としては、可視化結果を確認して、アルゴリズムの改良を考察する。

---

heur/ahc063 内の環境構築をしたい。
src 以下に、貪欲法ベースのシンプルな解法を実装して。
run.sh で実行できるようにしたい。