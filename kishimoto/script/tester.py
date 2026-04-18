"""
指定した問題 (A/B/C) の入力ファイルを自動で走らせ、スコアを表示・記録する。

使い方:
  python3 script/tester.py <実行ファイル> [--problem A|B|C] [--cases START END]

例:
  python3 script/tester.py ./a.out --problem A
  python3 script/tester.py ./a.out --problem B --cases 0 50
"""

import sys
import argparse
import datetime
import os
import collections
import shutil
import subprocess
import tempfile


def parse_args():
    parser = argparse.ArgumentParser(description="Run tester for Periodic Patrol Automata")
    parser.add_argument("executable", help="Path to the executable (e.g., ./a.out)")
    parser.add_argument("--problem", "-p", default="A", choices=["A", "B", "C"],
                        help="Problem ID (default: A)")
    parser.add_argument("--cases", nargs=2, type=int, default=[0, 100], metavar=("START", "END"),
                        help="Case range [START, END) (default: 0 100)")
    parser.add_argument("--timeout", type=int, default=10,
                        help="Timeout per case in seconds (default: 10)")
    return parser.parse_args()


def load_best_scores(output_dir, problem):
    """過去の result.csv から best スコアを読み込む（最大化）"""
    best_score = collections.defaultdict(lambda: 0)
    if not os.path.exists(output_dir):
        return best_score
    for pathname, dirnames, filenames in os.walk(output_dir):
        for filename in filenames:
            if filename != "result.csv":
                continue
            filepath = os.path.join(pathname, filename)
            with open(filepath, "r") as f:
                data = f.readlines()
            for line in data:
                parts = line.strip().split(",")
                if len(parts) < 3 or parts[0] == "source":
                    continue
                # problem が一致するもののみ
                if parts[0].startswith(f"in{problem}/") or f"/in{problem}/" in parts[0]:
                    pass  # OK
                elif not parts[0].startswith("in"):
                    continue
                key = parts[0]
                try:
                    score = int(parts[1])
                except ValueError:
                    continue
                if score <= 0:
                    continue
                best_score[key] = max(best_score[key], score)
    return best_score


def run_case(executable, input_file, tools_dir, timeout):
    """1ケースを実行しスコアを返す"""
    # プログラム実行
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir=tools_dir) as tmp:
        out_file = tmp.name

    try:
        with open(input_file, "r") as stdin_f:
            proc = subprocess.run(
                [executable],
                stdin=stdin_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        if proc.returncode != 0:
            stderr_msg = proc.stderr.decode("utf-8", errors="replace").strip()
            print(f"  RE (return code {proc.returncode}): {stderr_msg[:200]}", file=sys.stderr)
            return -1

        with open(out_file, "w") as f:
            f.write(proc.stdout.decode("utf-8"))

        # スコア計算: cargo run -r --bin score in.txt out.txt
        score_proc = subprocess.run(
            ["cargo", "run", "-r", "--bin", "score", input_file, out_file],
            cwd=tools_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

        score = -1
        # score は stdout または stderr に出力される可能性がある
        for output in [score_proc.stdout, score_proc.stderr]:
            text = output.decode("utf-8", errors="replace")
            for line in text.split("\n"):
                if "Score = " in line:
                    try:
                        score = int(line.split("Score = ")[1].strip())
                    except (ValueError, IndexError):
                        pass
                # 単純に数値のみの行もチェック
                stripped = line.strip()
                if stripped.isdigit() and score == -1:
                    score = int(stripped)
        return score

    except subprocess.TimeoutExpired:
        print(f"  TLE", file=sys.stderr)
        return -1
    finally:
        if os.path.exists(out_file):
            os.unlink(out_file)


def main():
    args = parse_args()

    # パス解決
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    tools_dir = os.path.join(project_dir, "tools")
    output_dir = os.path.join(project_dir, "output")
    executable = os.path.abspath(args.executable)

    problem = args.problem
    in_dir = os.path.join(tools_dir, f"in{problem}")
    cases_start, cases_end = args.cases

    if not os.path.isdir(in_dir):
        print(f"Error: Input directory not found: {in_dir}", file=sys.stderr)
        sys.exit(1)

    # 出力ディレクトリ作成
    now = datetime.datetime.now()
    out_dirname = os.path.join(
        output_dir,
        now.strftime("%m%d_%H%M%S") + f"_prob{problem}_cases{cases_start}_{cases_end}"
    )
    os.makedirs(out_dirname, exist_ok=True)

    # ベストスコア読み込み（最大化問題）
    best_score = load_best_scores(output_dir, problem)

    # 実行
    results = []
    total_score = 0
    total_best = 0
    improved = 0
    regressed = 0

    print(f"=== Problem {problem} | Cases [{cases_start}, {cases_end}) | Exec: {args.executable} ===")
    print()

    for i in range(cases_start, cases_end):
        input_file = os.path.join(in_dir, f"{i:04}.txt")
        if not os.path.exists(input_file):
            continue

        key = f"in{problem}/{i:04}.txt"
        score = run_case(executable, input_file, tools_dir, args.timeout)

        best = best_score.get(key, 0)
        if score > 0:
            new_best = max(best, score)
        else:
            new_best = best

        # 表示
        marker = ""
        if score > 0 and best > 0:
            if score > best:
                marker = " *** NEW BEST ***"
                improved += 1
            elif score < best:
                marker = f" (best: {best})"
                regressed += 1

        print(f"  {key}: {score}{marker}")

        results.append((key, score, new_best))
        if score > 0:
            total_score += score
        total_best += new_best

    # result.csv 書き出し
    csv_path = os.path.join(out_dirname, "result.csv")
    with open(csv_path, "w") as f:
        f.write("source,score,best\n")
        for key, score, best in results:
            f.write(f"{key},{score},{best}\n")

    # サマリ表示
    n_cases = len(results)
    n_valid = sum(1 for _, s, _ in results if s > 0)
    print()
    print(f"=== Summary ===")
    print(f"  Cases: {n_valid}/{n_cases} valid")
    print(f"  Total score: {total_score}")
    if n_valid > 0:
        print(f"  Average score: {total_score / n_valid:.1f}")
    print(f"  Total best:  {total_best}")
    if improved > 0:
        print(f"  Improved: {improved} cases")
    if regressed > 0:
        print(f"  Regressed: {regressed} cases")
    print(f"  Results saved to: {out_dirname}")


if __name__ == "__main__":
    main()
