import math
import json
from collections import defaultdict
from models.crop_prediction_model import crop_prediction_model  # Import the updated function

average_pot_size = 1

def calculate_scores(dataset, selected_categories, weight_savings, weight_carbon_absorption, max_savings, max_carb_absorption):
    scores = defaultdict(list)
    for category, plants in dataset.items():
        if category in selected_categories:
            for plant in plants:
                # Adjust score calculation using max_savings and max_carb_absorption
                score = ((plant["savings"] / max_savings) * weight_savings) + (plant["carbon_absorption"] / max_carb_absorption * weight_carbon_absorption)
                scores[category].append({
                    "label": plant["label"],
                    "score": score,
                    "savings": plant["savings"],
                    "carbon_absorption": plant["carbon_absorption"],
                    "growing_price": plant["growing_price"],
                    "market_price": plant["market_price"],
                    "temp_min": plant["temp_min"],
                    "temp_max": plant["temp_max"],
                    "rainfall": plant["rainfall"],
                    "sunlight_min": plant["sunlight_min"],
                    "perennial": plant["perennial"]
                })
                        
    for category in scores:
        scores[category].sort(key=lambda x: x["score"], reverse=True)
    return scores

def optimize_plants(scores, total_plants, total_budget):
    optimized = []
    total_savings = 0
    total_carbon_absorbed = 0
    remaining_budget = total_budget
    remaining_plants = total_plants
    plant_counts = defaultdict(int)
    print(scores)
    plants_per_category = math.floor(total_plants / len(scores.items()))
    extra_plants = total_plants % len(scores)

    for category, plants in scores.items():
        category_plants = plants_per_category + (1 if extra_plants > 0 else 0)
        extra_plants -= 1 if extra_plants > 0 else 0

        for plant in plants:
            if category_plants > 0 and remaining_budget >= plant["growing_price"] and plant_counts[plant["label"]] < 2:
                num_plants = min(category_plants, 
                                 math.floor(remaining_budget / plant["growing_price"]), 
                                 remaining_plants,
                                 total_plants / 10 - plant_counts[plant["label"]])
                
                if num_plants > 0:
                    plant_cost = num_plants * plant["growing_price"]
                    remaining_budget -= plant_cost
                    remaining_plants -= num_plants
                    category_plants -= num_plants
                    plant_counts[plant["label"]] += num_plants

                    optimized.append({
                        "label": plant["label"],
                        "carbon_absorption": plant["carbon_absorption"],
                        "savings": plant["savings"],
                        "growing_price": plant["growing_price"]
                    })

                    total_savings += num_plants * plant["savings"]
                    total_carbon_absorbed += num_plants * plant["carbon_absorption"]

            if category_plants == 0 or remaining_plants == 0 or remaining_budget < plant["growing_price"]:
                break

    return optimized, total_savings, total_carbon_absorbed, total_plants - remaining_plants, total_budget - remaining_budget

def format_and_print_results(output):
    print("\n===== Optimized Crop Selection Results =====\n")
    print(f"    Total Savings = {output['total_savings']}")
    print(f"    Total Carbon Absorbed = {output["total_carbon_absorbed"]}")
    print(f"    Total Plants Grown = {output['total_plants_grown']}")
    print(f"    Total Budget Used = {output['total_budget_used']}")
    print("\nRecommended Plants:")
    for plant in output['recommended_plants']:
        print(f"\n  {plant['label']}:")
        print(f"    Carbon Absorption: {plant['carbon_absorption']}")
        print(f"    Savings: {plant['savings']}")

def save_to_json(output, filename="optimized_plants.json"):
    with open(filename, "w") as json_file:
        json.dump(output, json_file, indent=4)
    print(f"\nData saved to {filename}")

def recomend_crops(terrace_size, latitude, longitude, weight_savings, weight_carbon_absorption, total_budget, selected_categories):
    # Hard-coded input values
    total_plants = terrace_size // average_pot_size

    # Get dataset from the model prediction
    dataset = crop_prediction_model(latitude, longitude)

    # Calculate max_savings and max_carb_absorption properly
    max_savings = 0
    max_carb_absorption = 0

    for category, plants in dataset.items():
        if category in selected_categories:
            for plant in plants:
                if plant["carbon_absorption"] > max_carb_absorption:
                    max_carb_absorption = plant["carbon_absorption"]
                if plant["savings"] > max_savings:
                    max_savings = plant["savings"]

    # Calculate scores
    scores = calculate_scores(dataset, selected_categories, weight_savings, weight_carbon_absorption, max_savings, max_carb_absorption)

    # Optimize plants
    recommended_plants, total_savings, total_carbon_absorbed, plants_grown, budget_used = optimize_plants(scores, total_plants, total_budget)
    print(total_savings,total_carbon_absorbed)

    # Prepare output
    output = {
        "total_savings": total_savings,
        "total_carbon_absorbed": round(total_carbon_absorbed,6),
        "total_plants_grown": plants_grown,
        "total_budget_used": budget_used,
        "recommended_plants": recommended_plants
    }

    # Format and print the results
    format_and_print_results(output)

    # Save results to JSON file
    save_to_json(output)

    return output

if __name__ == "__main__":
    result = recomend_crops(100,12,71,0.2,0.8,2000,['Vegetables','Fruits'])