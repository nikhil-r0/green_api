from flask import Flask, request, jsonify
from models.crop_model import crop_detect
from models.savings_model import estimate_savings, get_market_price, load_plant_data

app = Flask(__name__)

@app.route('/predict_crops', methods=['POST'])
def predict_crops():
    data = request.json
    lat = data['latitude']
    lon = data['longitude']
    sun = data['sunlight']
    area = data['area']
    
    crop_input = crop_detect(lat, lon, sun, area)
    crop_list = [crop.strip() for crop in crop_input.split(', ')]
    
    total_savings = 0
    output = ''
    
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
                output += val[0]
            if savings is not None:
                total_savings += savings
            print("\n")
        else:
            print(f"No data available for the crop '{crop_name}'.")
    
    return jsonify({
        'predicted_crops': output,
        'total_savings': total_savings,
        'recommended_crops': crop_input
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
