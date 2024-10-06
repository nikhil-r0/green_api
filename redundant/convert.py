import json
import csv

# Sample JSON data (as before)
data = json.load(open('plants.json'))

# Convert JSON data to CSV
def json_to_csv(json_data, csv_filename="plants.csv"):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([
            "Category", "Label", "Temp Min", "Temp Max", 
            "Rainfall", "Sunlight Min", "Perennial", 
            "Market Price", "Growing Price", "Savings", "Carbon Absorption"
        ])
        
        # Process each category (Fruits, Vegetables, etc.)
        for category in json_data:
            for plant_type, plants in category.items():
                for plant in plants:
                    writer.writerow([
                        plant_type, 
                        plant['label'], 
                        plant['temp_min'], 
                        plant['temp_max'], 
                        plant['rainfall'], 
                        plant['sunlight_min'], 
                        "Yes" if plant['perennial'] else "No", 
                        plant['market_price'], 
                        plant['growing_price'], 
                        plant['savings'], 
                        plant['carbon_absorption']
                    ])

# Call the function to create the CSV file
json_to_csv(data, "plants.csv")
print("CSV file created successfully.")
