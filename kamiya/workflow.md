### コンテスト前

- template をコピペ

### コンテスト開始

/kamiya で以下を実施：
- 問題ページから以下をダウンロードして配置
  - problem.pdf（問題ページそのもの）
  - tools（ローカル版）
- Pahcer を初期化
  ```bash
  # AHC039 （非インタラクティブ問題、スコア最大化）でC++を使用
  pahcer init -p ahc039 -o max -l cpp
  
  # AHC030 （インタラクティブ問題、スコア最小化）でPythonを使用
  pahcer init -p ahc030 -o min -l python -i
  ```
- prompt.md を参考に以下を実施
  - visualizer の実装
  - solver の実装
