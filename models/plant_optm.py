import pandas as pd
import numpy as np
import logging
from models.get_weather_data import get_weather_data

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PLANT_SIZE = 0.5  # Each plant takes 0.5 square meters
PERENNIAL_CARBON_WEIGHT = 1.5
PERENNIAL_SAVINGS_WEIGHT = 1.2

def load_plant_data(file_path):
    """Loads plant data from CSV file."""
    try:
        logger.info("Loading plant data from CSV")
        plant_data = pd.read_csv(file_path)
        logger.debug(f"Loaded {len(plant_data)} plants from {file_path}")
        return plant_data
    except Exception as e:
        logger.error(f"Error loading plant data: {str(e)}")
        raise

def filter_plants_by_weather(plant_data, weather_data):
    """Filters plants based on compatibility with weather data."""
    try:
        logger.info("Filtering plants based on weather data")
        temp_min = weather_data['temp_min']
        temp_max = weather_data['temp_max']
        rainfall = weather_data['rainfall']
        sunlight = weather_data['sunlight']

        filtered_plants = plant_data[
            (plant_data['Temp Min'] <= temp_max) & 
            (plant_data['Temp Max'] >= temp_min) & 
            (plant_data['Sunlight Min'] <= sunlight)
        ]
        logger.debug(f"Filtered plants count: {len(filtered_plants)}")
        return filtered_plants
    except Exception as e:
        logger.error(f"Error filtering plants: {str(e)}")
        raise

def score_plants(plant_data, weight_savings, weight_carbon_absorption):
    """Scores plants based on user preferences."""
    try:
        logger.info("Scoring plants based on user preferences")
        plant_data['Score'] = (
            weight_savings * plant_data['Savings'] +
            weight_carbon_absorption * plant_data['Carbon Absorption'] * 
            np.where(plant_data['Perennial'] == 'Yes', PERENNIAL_CARBON_WEIGHT, 1)
        )
        logger.debug(f"Scored plants: {plant_data[['Label', 'Score']].head()}")
        return plant_data
    except Exception as e:
        logger.error(f"Error scoring plants: {str(e)}")
        raise

def allocate_plants(plant_data, terrace_size, budget, selected_categories, weight_savings, weight_carbon_absorption):
    """Allocates plants based on terrace size, budget, and preferences."""
    try:
        logger.info("Allocating plants based on constraints")

        max_plants = int(terrace_size / PLANT_SIZE)
        logger.debug(f"Max plants to allocate: {max_plants}")

        selected_plants = plant_data[plant_data['Category'].isin(selected_categories)]
        selected_plants = score_plants(selected_plants, weight_savings, weight_carbon_absorption)
        sorted_plants = selected_plants.sort_values(by='Score', ascending=False)

        total_cost = 0
        allocated_plants = []
        plant_counts = {category: 0 for category in selected_categories}

        for index, row in sorted_plants.iterrows():
            if total_cost + row['Growing Price'] > budget or len(allocated_plants) >= max_plants:
                break
            if plant_counts[row['Category']] < max_plants / len(selected_categories):
                allocated_plants.append(row)
                plant_counts[row['Category']] += 1
                total_cost += row['Growing Price']

        total_savings = sum([plant['Savings'] for plant in allocated_plants])
        total_carbon_absorption = sum([plant['Carbon Absorption'] for plant in allocated_plants])

        logger.info(f"Total plants allocated: {len(allocated_plants)}")
        logger.debug(f"Total savings: {total_savings}, Total carbon absorption: {total_carbon_absorption}")

        return allocated_plants, total_savings, total_carbon_absorption
    except Exception as e:
        logger.error(f"Error allocating plants: {str(e)}")
        raise

def recommend_crops(terrace_size, latitude, longitude, weight_savings, weight_carbon_absorption, total_budget, selected_categories):
    """Main function to recommend crops."""
    try:
        logger.info("Starting recommend_crops function")

        # Load plant data
        plant_data = load_plant_data('plants.csv')

        # Get weather data
        weather_data = get_weather_data(latitude, longitude)
        logger.info(weather_data)

        # Filter plants based on weather compatibility
        filtered_plants = filter_plants_by_weather(plant_data, weather_data)

        # Allocate plants based on the constraints
        allocated_plants, total_savings, total_carbon_absorption = allocate_plants(
            filtered_plants, 
            terrace_size, 
            total_budget, 
            selected_categories, 
            weight_savings, 
            weight_carbon_absorption
        )

        # Prepare response
        plant_list = [{
            "Label": plant["Label"],
            "Category": plant["Category"],
            "Savings": plant["Savings"],
            "Carbon Absorption": plant["Carbon Absorption"]
            } for plant in allocated_plants]

        result = {
            "allocated_plants": plant_list,
            "total_savings": total_savings,
            "total_carbon_absorption": total_carbon_absorption
        }

        logger.info("Crops recommendation completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in recommend_crops: {str(e)}")
        raise
