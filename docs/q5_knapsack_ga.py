import random

# Item Setup (Weight, Value)
items = [
    {"name": "A", "weight": 2, "value": 12},
    {"name": "B", "weight": 1, "value": 10},
    {"name": "C", "weight": 3, "value": 20},
    {"name": "D", "weight": 2, "value": 15}
]
MAX_CAPACITY = 5

# 3. Implement fitness function
def get_fitness(chromosome):
    total_weight = 0
    total_value = 0
    
    for i in range(4):
        if chromosome[i] == 1:
            total_weight += items[i]["weight"]
            total_value += items[i]["value"]
            
    # Keep weight within capacity
    if total_weight > MAX_CAPACITY:
        return 0  # Invalid solution, fitness is 0
    return total_value

def main():
    # 2. Generate initial population of 50 chromosomes (1=selected, 0=not selected)
    population = [[random.choice([0, 1]) for _ in range(4)] for _ in range(50)]
    
    # 5. Run the algorithm for 100 generations
    for gen in range(100):
        # Evaluate
        ranked = [(get_fitness(chrom), chrom) for chrom in population]
        ranked.sort(key=lambda item: item[0], reverse=True)
        
        # Selection (top 10 fittest chromosomes)
        best_chromosomes = [item[1] for item in ranked[:10]]
        
        new_population = []
        for _ in range(50):
            # Crossover (Single-point crossover)
            p1 = random.choice(best_chromosomes)
            p2 = random.choice(best_chromosomes)
            split_point = random.randint(1, 3)
            child = p1[:split_point] + p2[split_point:]
            
            # Mutation (Bit flip)
            for i in range(4):
                if random.random() < 0.05:  # 5% chance to flip each bit
                    child[i] = 1 if child[i] == 0 else 0
                    
            new_population.append(child)
            
        population = new_population

    # Final Evaluation
    final_ranked = [(get_fitness(chrom), chrom) for chrom in population]
    final_ranked.sort(key=lambda item: item[0], reverse=True)
    
    best_chrom = final_ranked[0][1]
    max_val = final_ranked[0][0]

    # 6. Print the best chromosome and maximum value obtained
    print("=== Knapsack GA Optimization ===")
    print(f"Items (A, B, C, D) state: {best_chrom}")
    print(f"Maximum Value Obtained: ${max_val}")

if __name__ == "__main__":
    main()