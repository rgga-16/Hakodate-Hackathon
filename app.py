# https://www.youtube.com/watch?v=ZzC3SJJifMg&t=59s

from flask import Flask, send_from_directory, request, jsonify
import random, requests, base64, cv2, os, sys, shutil
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw
from ultralytics import YOLO


import infer

app = Flask(__name__, static_folder="./client/public")

trash_cats = ['Aluminium foil', 'Battery', 'Blister pack', 'Bottle', 'Bottle cap', 'Broken glass', 'Can', 'Carton', 'Cup', 'Food waste', 'Glass jar', 'Lid','Other plastic', 'Paper', 'Paper bag', 'Plastic bag & wrapper', 'Plastic container', 'Plastic glooves', 'Plastic utensils', 'Pop tab', 'Rope & strings', 'Scrap metal', 'Shoe', 'Squeezable tube', 'Straw', 'Styrofoam piece', 'Unlabeled litter','Cigarette']

burnable = ['Carton', 'Cup', 'Food waste', 'Paper', 'Paper bag', 'Rope & strings', 'Shoe', 'Paper', 'Paper bag', 'Unlabeled litter', 'Cigarette']
non_burnable = ['Aluminium foil', 'Battery', 'Broken glass', 'Glass jar', 'Lid', 'Scrap metal']
plastic = ['Blister pack', 'Bottle cap','Other plastic', 'Plastic bag & wrapper', 'Plastic container', 'Plastic glooves', 'Plastic utensils', 'Squeezable tube', 'Straw', 'Styrofoam piece','Pop tab']
PET_bottles_cans = ['Bottle','Can']


@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    form_data = request.get_json()
    image_data = form_data['image']

    image_bytes = BytesIO(base64.b64decode(image_data.split(',')[1]))
    image = Image.open(image_bytes)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    temp_impath = "temp.jpg"
    image.save(temp_impath)

    shutil.rmtree('runs')

    os.system(f"yolo task=detect mode=predict model=best.pt conf=0.25 source=temp.jpg save=True save_txt=True")

    image_detections = Image.open('./runs/detect/predict/temp.jpg')
    buffered = BytesIO()
    image_detections.save(buffered, format='JPEG')
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    detected_cat_ids = []
    detections = []
    labels_path = './runs/detect/predict/labels/temp.txt'

    if (os.path.exists(labels_path)):
        print("Labels file exists")
        with open(labels_path,'r') as file:
            for line in file:
                first_digit = int(line.split()[0])
                detected_cat_ids.append(first_digit)


    detected_cat_names = [trash_cats[cat] for cat in detected_cat_ids]
    for cat_name in detected_cat_names:
        for burnable_cat in burnable:
            if cat_name == burnable_cat:
                print("Burnable")
                detections.append({
                    "name": cat_name,
                    "type": "burnable"
                })
                break
        for non_burnable_cat in non_burnable:
            if cat_name == non_burnable_cat:
                print("Non-burnable")
                detections.append({
                    "name": cat_name,
                    "type": "non-burnable"
                })
                break
        for plastic_cat in plastic:
            if cat_name == plastic_cat:
                print("Plastic")
                detections.append({
                    "name": cat_name,
                    "type": "plastic"
                })
                break
        for PET_bottles_can in PET_bottles_cans:
            if cat_name == PET_bottles_can:
                print("PET bottles and cans")
                detections.append({
                    "name": cat_name,
                    "type": "PET bottles, bottles, and cans"
                })
                break

    response_dict = {
        "detection_image": image_base64,
        "detection_labels": detections,
    }
    print()
    return jsonify(response_dict)

# Path for our main Svelte page
@app.route("/")
def base():
    return send_from_directory('./client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('./client/public', path)


if __name__ == "__main__":
    app.run(debug=True)