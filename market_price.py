import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import crop_detection
from io import StringIO
from flask import Flask, request, jsonify

app = Flask(__name__)
# Function to get market price for a specific crop
def get_market_price(crop, date):
    base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    api_key = "579b464db66ec23bdd000001c0a290a221ac4a1e7f41626aaf9ee723"  # Replace with your actual API key

    formatted_date = date.strftime("%d/%m/%Y")

    params = {
        "api-key": api_key,
        "format": "csv",
        "filters[commodity]": crop,
        "filters[arrival_date]": formatted_date,
        "limit": 1000
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        if not df.empty:
            df.columns = ['State', 'District', 'Market', 'Commodity', 'Variety', 'Grade', 'Arrival_Date', 'Min_Price', 'Max_Price', 'Modal_Price']
            avg_price_per_100kg = df['Modal_Price'].mean()

            # Convert the price to per kg
            avg_price_per_kg = avg_price_per_100kg / 100
            return avg_price_per_kg

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market price: {e}")
        return None
    except pd.errors.EmptyDataError:
        print(f"No data available for {crop} on {formatted_date}")
        return None

# Function to collect two days' worth of market price data
def collect_two_day_data(crop):
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)  # This will give us 2 days of data including today
    current_date = start_date
    while current_date <= end_date:
        price = get_market_price(crop, current_date)
        if price is not None:
            data.append({'date': current_date, 'price': price})
        current_date += timedelta(days=1)
    return pd.DataFrame(data)

# Function to estimate savings
def estimate_savings(crop, quantity, growing_cost):
    df = collect_two_day_data(crop)
    if df.empty:
        print(f"No data available for {crop} in the past two days.")
        return None

    current_price = df['price'].iloc[-1]
    estimated_future_price = current_price  # Simplified: using current price as future price estimate

    market_cost = estimated_future_price * quantity
    growing_total_cost = growing_cost * quantity

    savings = market_cost - growing_total_cost
    savings_per_kg = savings / quantity
    res = ""

    res += f"Crop: {crop}"
    res += f"Current market price: ₹{current_price:.2f} per kg"
    res += f"Estimated future market price: ₹{estimated_future_price:.2f} per kg"
    res += f"Cost to grow: ₹{growing_cost:.2f} per kg"
    res += f"Total market cost for {quantity} kg: ₹{market_cost:.2f}"
    res += f"Total growing cost for {quantity} kg: ₹{growing_total_cost:.2f}"
    res += f"Estimated total savings: ₹{savings:.2f}"
    res += f"Estimated savings per kg: ₹{savings_per_kg:.2f}"

    return (res, savings)

# Function to load plant data from the JSON file
def load_plant_data(crop_name, file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        if 'plants' in data and isinstance(data['plants'], list):
            for plant in data['plants']:
                if plant['name'].lower() == crop_name.lower():
                    return plant
        else:
            print(f"JSON structure is not as expected. Here's what we found:")
            print(json.dumps(data, indent=2))
            return None
    except json.JSONDecodeError:
        print(f"Error: The file at {file_path} is not a valid JSON file.")
        return None
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

    print(f"No data found for the crop '{crop_name}'.")
    return None

# Main function
@app.route('/predict_crops', methods=['POST'])
def main():
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    sun = data.get('sunlight')
    are = data.get('area')
    # print(type(crop_detection.crop_detect()))
    crop_input = crop_detection.crop_detect(lat, lon, sun, are)
    #crop_input = ''.join(crop_input.split(' '))
    crop_list = [crop.strip() for crop in crop_input.split(', ')]

    total_savings = 0
    out = ''
    for crop_info in crop_list:
        crop_name, quantity = crop_info.split(':')
        crop_name = crop_name.strip()
        quantity = int(quantity.strip())

        plants_data = load_plant_data(crop_name, 'growing_cost.json')

        if plants_data:
            val = estimate_savings(plants_data['name'], quantity, plants_data['growing_cost'])
            if val != None:
                savings = val[1]
                print(val[0])
                out += val[0]
            if savings is not None:
                total_savings += savings
            print("\n")
        else:
            print(f"No data available for the crop '{crop_name}'.")

    print(f"Total estimated savings for all crops: ₹{total_savings:.2f}")
    try:
        return jsonify({
            'predicted_crops': out,
            'savings': savings,
            'total_savings': total_savings,
            'recommended_crops': crop_input
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An internal error occurred'}), 500
    

if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000)