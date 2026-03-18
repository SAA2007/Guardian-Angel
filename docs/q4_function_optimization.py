import random

# Function to optimize
def f(x):
    return x**2 - 10*x + 25

# 2. Fitness function to find the minimum value
# We use 1 / (f(x) + epsilon) so smaller f(x) gives larger fitness
def get_fitness(x):
    val = f(x)
    return 1 / (val + 1e-6)

def main():
    # 1. Generate an initial population of 200 random values of x
    # Choosing a reasonable range like -50 to 50
    population = [random.uniform(-50, 50) for _ in range(200)]
    
    # 4. Run the algorithm for 500 generations
    for gen in range(500):
        # Evaluate
        ranked = [(get_fitness(x), x) for x in population]
        ranked.sort(key=lambda item: item[0], reverse=True)
        
        # Selection (top 20 fittest individuals)
        best_parents = [item[1] for item in ranked[:20]]
        
        new_population = []
        for _ in range(200):
            # Crossover (average of two random parents)
            p1 = random.choice(best_parents)
            p2 = random.choice(best_parents)
            child = (p1 + p2) / 2
            
            # Mutation (small random shift)
            if random.random() < 0.1:  # 10% chance to mutate
                child += random.uniform(-1, 1)
                
            new_population.append(child)
            
        population = new_population

    # Final Evaluation
    final_ranked = [(get_fitness(x), x) for x in population]
    final_ranked.sort(key=lambda item: item[0], reverse=True)
    best_x = final_ranked[0][1]

    # 5. Print the best value of x and corresponding minimum value
    print("=== Function Optimization f(x) = x^2 - 10x + 25 ===")
    print(f"Best value of x: {best_x:.6f}")
    print(f"Minimum value of the function: {f(best_x):.6f}")

if __name__ == "__main__":
    main()