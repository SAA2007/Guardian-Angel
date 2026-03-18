import random

# 1. Evaluate expression function
def evaluate_expression(x, y, z):
    return (6 * x**3) + (9 * y**2) + (90 * z) - 25

# 3. Fitness function (closest to zero is best)
def fitness(x, y, z):
    ans = evaluate_expression(x, y, z)
    if ans == 0:
        return 999999  # Maximum fitness if exact match
    return abs(1 / ans)

def main():
    # 2. Generate initial population of 1000 candidate solutions (0 to 1000)
    population = []
    for _ in range(1000):
        population.append((random.uniform(0, 1000), random.uniform(0, 1000), random.uniform(0, 1000)))

    # 4. Store solutions in format: (fitness_value, (x, y, z))
    ranked_solutions = []
    for ind in population:
        fit_val = fitness(ind[0], ind[1], ind[2])
        ranked_solutions.append((fit_val, ind))

    # 5. Sort population according to fitness (highest to lowest)
    ranked_solutions.sort(key=lambda x: x[0], reverse=True)

    # 6. Print the top 10 best solutions
    print("=== Top 10 Best Solutions from Initial Population ===")
    for i in range(10):
        print(f"Rank {i+1}: Fitness = {ranked_solutions[i][0]:.6f} | (x, y, z) = {ranked_solutions[i][1]}")

if __name__ == "__main__":
    main()