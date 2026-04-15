find . -type f -name '*Zone.Identifier' -exec rm -f {} \;
rm ./aa.out
rm ./out/result.csv
g++ ./$1.cpp -std=gnu++23 -Wfatal-errors -I../../ac-library -O3 -o ./aa.out
./aa.out < tools/in/$2.txt > out.txt

# # AHC039 （非インタラクティブ問題、スコア最大化）でC++を使用
# pahcer init -p ahc039 -o max -l cpp

# # AHC030 （インタラクティブ問題、スコア最小化）でPythonを使用
# pahcer init -p ahc063 -o min -l cpp