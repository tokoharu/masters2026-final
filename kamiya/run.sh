if [[ -n "$1" && -d "tools/in$1" ]]; then
	rm -rf tools/in
	cp -r "tools/in$1" tools/in
fi
python3 ./script/amalgamate.py --root . --entry src/main.cpp --out main.cpp
mkdir -p tools/out tools/err tools/vis
pahcer run

# -------
# [事前準備]

# template をコピペ

## AHC039 （非インタラクティブ問題、スコア最大化）でC++を使用
#pahcer init -p ahc039 -o max -l cpp

## AHC030 （インタラクティブ問題、スコア最小化）でPythonを使用
#pahcer init -p ahc030 -o min -l python -i

# tools をダウンロードして配置
