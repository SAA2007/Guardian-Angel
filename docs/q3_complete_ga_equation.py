import random

def evaluate_expression(x, y, z):
    return (6 * x**3) + (9 * y**2) + (90 * z) - 25

def fitness(x, y, z):
    ans = evaluate_expression(x, y, z)
    if ans == 0:
        return 999999
    return abs(1 / ans)

def main():
    # 1. Generate an initial population of 1000 solutions
    solutions = [(random.uniform(0, 1000), random.uniform(0, 1000), random.uniform(0, 1000)) for _ in range(1000)]
    
    # 3. Run the algorithm for 10,000 generations
    for generation in range(10000):
        # Fitness evaluation
        ranked_solutions = [(fitness(x, y, z), (x, y, z)) for x, y, z in solutions]
        ranked_solutions.sort(key=lambda item: item[0], reverse=True)
        
        best_sol = ranked_solutions[0]
        
        # 4. Print generation number, best solution, and fitness value
        print(f"Gen {generation}: Fitness = {best_sol[0]:.5f} | Best = {best_sol[1]}")
        
        # Threshold stop condition
        if best_sol[0] > 999:
            print(f"\nThreshold reached at generation {generation}!")
            break
            
        # Selection
        top_100 = ranked_solutions[:100]
        variables = []
        for sol in top_100:
            variables.extend([sol[1][0], sol[1][1], sol[1][2]])
            
        # Generation update & Mutation
        new_generation = []
        for _ in range(1000):
            new_x = random.choice(variables) * random.uniform(0.99, 1.01)
            new_y = random.choice(variables) * random.uniform(0.99, 1.01)
            new_z = random.choice(variables) * random.uniform(0.99, 1.01)
            new_generation.append((new_x, new_y, new_z))
            
        solutions = new_generation

    # 5. Display the optimized values
    final_best = ranked_solutions[0][1]
    print("\n=== Optimized Values ===")
    print(f"x: {final_best[0]}")
    print(f"y: {final_best[1]}")
    print(f"z: {final_best[2]}")

if __name__ == "__main__":
    main()