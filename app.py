from flask import Flask, send_from_directory, request, jsonify, render_template
import random, requests, base64, cv2, os
# https://www.youtube.com/watch?v=ZzC3SJJifMg&t=59s
import random, requests, base64, cv2, os, sys, shutil

import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw
from ultralytics import YOLO
import pickle
import uuid

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

#ubscription_key = os.getenv("VISION_KEY")
#endpoint = os.getenv("VISION_ENDPOINT")

#cv_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

AZURE_TRANSLATE_KEY = os.environ["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATE_ENDPOINT = os.environ["AZURE_TRANSLATE_ENDPOINT"]
AZURE_TRANSLATE_LOCATION = os.environ["AZURE_TRANSLATE_LOCATION"]
import infer

app = Flask(__name__, static_folder="./client/static", template_folder="./client/templates")

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
@app.route("/old")
def base():
    return send_from_directory('./client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('./client/public', path)

# Path for schedule list api
@app.route('/api/schedule')
def schedule_index():
    output = []

    with open ('./datastore.pickle','rb') as f:
        origin_data = pickle.load(f,encoding='utf8')

    for category in origin_data:
        for line in origin_data[category]:
            output.append({category:line})

    return jsonify(output)

# Path for Azure Translator
@app.route('/api/translate',methods=['post'])
def translate():
    request_body = request.get_json()
    source_lang = request_body['from']
    target_lang = request_body['to']
    text_list = request_body['text']

    azure_translate_body = []
    for text in text_list:
        azure_translate_body.append({'text':text})
    print(azure_translate_body)

    azure_translate_params = {
        'api-version':'3.0',
        'from':source_lang,
        'to':target_lang
    }

    azure_translate_header ={
        'Ocp-Apim-Subscription-Key':AZURE_TRANSLATE_KEY,
        'Ocp-Apim-Subscription-Region':AZURE_TRANSLATE_LOCATION,
        'Content-type':'application/json',
        'X-ClientTraceId':str(uuid.uuid4())
    }

    translate_request = requests.post(AZURE_TRANSLATE_ENDPOINT,params=azure_translate_params,headers=azure_translate_header,json=azure_translate_body)
    translate_responses = translate_request.json()

    print(translate_responses)

    translate_result = []
    for translate_response in translate_responses:
        result = translate_response['translations'][0]['text']
        print(result)
        translate_result.append(result)

    return jsonify(translate_result)

# Path for new index
@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)