if [[ -n "$1" && -d "tools/in$1" ]]; then
	rm -rf tools/in
	cp -r "tools/in$1" tools/in
fi
python3 ./script/amalgamate.py --root . --entry src/main.cpp --out main.cpp
mkdir -p tools/out tools/err tools/vis
pahcer run

