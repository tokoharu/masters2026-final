
python3 ./script/amalgamate.py --root . --entry src/main.cpp --out submit/main.cpp
g++ -std=c++17 -O2 -o ./a.out ./submit/main.cpp 
cd tools
./../a.out < inB/0000.txt > out
cargo run -r --bin score  inB/0000.txt  out
cd ..
python3 ./../visualizer.py ./tools/inB/0000.txt ./tools/out