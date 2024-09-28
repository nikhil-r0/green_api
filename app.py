from flask import Flask, request, jsonify
from models.plant_optm import recomend_crops

app = Flask(__name__)

@app.route('/recommend_crops', methods=['POST'])
def api_recommend_crops():
    data = request.json
    

    result = recomend_crops(
        terrace_size=data['terrace_size'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        weight_savings=data['savings_weight'],
        weight_carbon_absorption=data['weight_carbon_absorption'],
        total_budget=data['budget'],
        selected_categories=data['types']
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run()