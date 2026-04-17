


g++ -std=c++17 -O2 -pg -o self_test src/self_tester.cpp
./self_test < ./tools/in/0000.txt 
gprof ./self_test gmon.out > gprof_log