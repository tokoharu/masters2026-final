#include "solve_a.hpp"
#include "solve_b.hpp"
#include "solve_c.hpp"

int main() {
    Input input;
    input.read();

    Solution sol;
    if (input.A_K == 0) {
        sol = solve_a(input);
    } else if (input.A_W == 1000) {
        sol = solve_c(input);
    } else {
        sol = solve_b(input);
    }

    sol.output(input);
    sol.log_summary(input);

    return 0;
}
