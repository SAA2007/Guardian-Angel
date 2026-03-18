import random

def evaluate_expression(x, y, z):
    return (6 * x**3) + (9 * y**2) + (90 * z) - 25

def fitness(x, y, z):
    ans = evaluate_expression(x, y, z)
    if ans == 0:
        return 999999
    return abs(1 / ans)

def main():
    # Setup: Generate and rank initial population (from Q1)
    population = [(random.uniform(0, 1000), random.uniform(0, 1000), random.uniform(0, 1000)) for _ in range(1000)]
    ranked_solutions = [(fitness(x, y, z), (x, y, z)) for x, y, z in population]
    ranked_solutions.sort(key=lambda item: item[0], reverse=True)

    # 1. Select the top 100 solutions based on fitness
    top_100 = ranked_solutions[:100]

    # 2. Extract variables x, y, and z from the selected solutions
    variables = []
    for sol in top_100:
        variables.extend([sol[1][0], sol[1][1], sol[1][2]])

    # 3. Create a new generation of 1000 solutions
    new_generation = []
    for _ in range(1000):
        # 4. Apply mutation
        new_x = random.choice(variables) * random.uniform(0.99, 1.01)
        new_y = random.choice(variables) * random.uniform(0.99, 1.01)
        new_z = random.choice(variables) * random.uniform(0.99, 1.01)
        
        # 5. Store new population
        new_generation.append((new_x, new_y, new_z))

    # Evaluate new generation to find the best
    ranked_new_gen = [(fitness(x, y, z), (x, y, z)) for x, y, z in new_generation]
    ranked_new_gen.sort(key=lambda item: item[0], reverse=True)

    # 6. Print the best solution of the generation
    print("=== Best Solution of the New Generation ===")
    print(f"Fitness = {ranked_new_gen[0][0]:.6f} | (x, y, z) = {ranked_new_gen[0][1]}")

if __name__ == "__main__":
    main()