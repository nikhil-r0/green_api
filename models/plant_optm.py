import math
import json
from collections import defaultdict
import logging
from models.crop_prediction_model import crop_prediction_model

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

average_pot_size = 1

def calculate_scores(dataset, selected_categories, weight_savings, weight_carbon_absorption, max_savings, max_carb_absorption):
    scores = defaultdict(list)
    logger.debug(f"Dataset keys: {dataset.keys()}")
    logger.debug(f"Selected categories: {selected_categories}")
    logger.debug(f"Max savings: {max_savings}, Max carb absorption: {max_carb_absorption}")

    if not dataset:
        logger.error("Empty dataset")
        return scores

    if not selected_categories:
        logger.error("No categories selected")
        return scores

    if max_savings == 0 or max_carb_absorption == 0:
        logger.error("max_savings or max_carb_absorption is zero")
        return scores

    for category, plants in dataset.items():
        if category in selected_categories:
            for plant in plants:
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

    logger.debug(f"Scores keys: {scores.keys()}")
    logger.debug(f"Number of plants per category: {[len(plants) for plants in scores.values()]}")

    return scores

def optimize_plants(scores, total_plants, total_budget):
    if not scores:
        logger.warning("No valid plant scores available.")
        return [], 0, 0, 0, 0

    optimized = []
    total_savings = 0
    total_carbon_absorbed = 0
    remaining_budget = total_budget
    remaining_plants = total_plants
    plant_counts = defaultdict(int)
    logger.debug(total_plants)

    num_categories = len(scores.items())
    if num_categories == 0:
        logger.warning("No plant categories available.")
        return [], 0, 0, 0, 0

    plants_per_category = math.floor(total_plants / num_categories)
    extra_plants = total_plants % num_categories

    for category, plants in scores.items():
        category_plants = plants_per_category + (1 if extra_plants > 0 else 0)
        extra_plants -= 1 if extra_plants > 0 else 0
        flag = True
        while category_plants > 0 and remaining_budget > 0 and flag:
            for plant in plants:
                #logger.debug(math.floor(remaining_budget / plant["growing_price"]))
                if remaining_budget >= plant["growing_price"]:
                    # Determine how many plants to add (either 1 or 2 depending on category_plants size)
                    num_plants = min(2 if category_plants > total_plants / 5 else 1,  # Add more plants early on, then reduce
                                    category_plants,
                                    math.floor(remaining_budget / plant["growing_price"]),  # Respect budget
                                    remaining_plants,  # Respect remaining total plants
                                    total_plants / 10 - plant_counts[plant["label"]])  # Ensure not adding too many per plant
                    logger.debug(num_plants)
                    if num_plants > 0:
                        plant_cost = num_plants * plant["growing_price"]
                        remaining_budget -= plant_cost
                        remaining_plants -= num_plants
                        category_plants -= num_plants
                        plant_counts[plant["label"]] += num_plants

                        # Check if plant already exists in optimized list
                        plant_in_list = next((p for p in optimized if p["label"] == plant["label"]), None)

                        if plant_in_list:
                            # Update values if the plant exists in the optimized list
                            plant_in_list["no_of_plants"] += num_plants
                            plant_in_list["savings"] += num_plants * plant["savings"]
                            plant_in_list["total_carbon_absorption"] += num_plants * plant["carbon_absorption"]
                        else:
                            # Append a new plant if not already in the list
                            optimized.append({
                                "label": plant["label"],
                                "carbon_absorption": plant["carbon_absorption"],
                                "total_carbon_absorption": num_plants * plant["carbon_absorption"],
                                "no_of_plants": num_plants,
                                "savings": num_plants * plant["savings"],
                                "growing_price": plant["growing_price"]
                            })

                        # Update total_savings and total_carbon_absorbed outside of appending/modifying the plant
                        total_savings += num_plants * plant["savings"]
                        total_carbon_absorbed += num_plants * plant["carbon_absorption"]
                else:
                    flag = False
                    break
                # Exit loop if there's no more budget or plants to add
                if category_plants <= 0 or remaining_budget <= 0:
                    flag = False
                    break



    return optimized, total_savings, total_carbon_absorbed, total_plants - remaining_plants, total_budget - remaining_budget

def recomend_crops(terrace_size, latitude, longitude, weight_savings, weight_carbon_absorption, total_budget, selected_categories):
    try:
        logger.info(f"Starting recomend_crops with parameters: terrace_size={terrace_size}, latitude={latitude}, longitude={longitude}, "
                    f"weight_savings={weight_savings}, weight_carbon_absorption={weight_carbon_absorption}, "
                    f"total_budget={total_budget}, selected_categories={selected_categories}")

        total_plants = terrace_size // average_pot_size
        logger.debug(f"Total plants: {total_plants}")

        dataset = crop_prediction_model(latitude, longitude)
        # logger.debug(f"Dataset keys: {dataset.items()}")

        max_savings = 0
        max_carb_absorption = 0

        for category, plants in dataset.items():
            if category in selected_categories:
                for plant in plants:
                    if plant["carbon_absorption"] > max_carb_absorption:
                        max_carb_absorption = plant["carbon_absorption"]
                    if plant["savings"] > max_savings:
                        max_savings = plant["savings"]

        logger.debug(f"Max savings: {max_savings}, Max carb absorption: {max_carb_absorption}")

        if max_savings == 0 or max_carb_absorption == 0:
            logger.warning("No valid plant data found for the given criteria.")
            return {
                "error": "No valid plant data found for the given criteria.",
                "total_savings": 0,
                "total_carbon_absorbed": 0,
                "total_plants_grown": 0,
                "total_budget_used": 0,
                "recommended_plants": []
            }

        scores = calculate_scores(dataset, selected_categories, weight_savings, weight_carbon_absorption, max_savings, max_carb_absorption)

        if not scores:
            logger.warning("No valid plant scores calculated.")
            return {
                "error": "No valid plant scores calculated.",
                "total_savings": 0,
                "total_carbon_absorbed": 0,
                "total_plants_grown": 0,
                "total_budget_used": 0,
                "recommended_plants": []
            }

        recommended_plants, total_savings, total_carbon_absorbed, plants_grown, budget_used = optimize_plants(scores, total_plants, total_budget)
        logger.debug(f"Optimization results: recommended_plants={len(recommended_plants)}, total_savings={total_savings}, "
                     f"total_carbon_absorbed={total_carbon_absorbed}, plants_grown={plants_grown}, budget_used={budget_used}")

        output = {
            "total_savings": total_savings,
            "total_carbon_absorbed": round(total_carbon_absorbed, 6),
            "total_plants_grown": plants_grown,
            "total_budget_used": budget_used,
            "recommended_plants": recommended_plants
        }

        logger.info("recomend_crops completed successfully")
        return output

    except Exception as e:
        logger.exception(f"An error occurred in recomend_crops: {str(e)}")
        return {
            "error": f"An unexpected error occurred: {str(e)}",
            "total_savings": 0,
            "total_carbon_absorbed": 0,
            "total_plants_grown": 0,
            "total_budget_used": 0,
            "recommended_plants": []
        }

if __name__ == "__main__":
    result = recomend_crops(100, 12, 71, 0.2, 0.8, 2000, ['Vegetables', 'Fruits'])
    print(json.dumps(result, indent=2))