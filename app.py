from flask import Flask, send_from_directory, request, jsonify, render_template
import random, requests, base64, cv2, os
import numpy as np
from io import BytesIO
from PIL import Image
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

# Load the pre-trained YOLO model here
model = YOLO("yolov8s.pt")

def get_predicted_objects_yolo(image_nparray):
    results = model.predict(image_nparray)
    infer.plot_bboxes(image_nparray,results[0].boxes.boxes,conf=0.8)
    cv2.imshow("",image_nparray)

    return 

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    form_data = request.get_json()
    image_data = form_data['image']

    image_bytes = BytesIO(base64.b64decode(image_data.split(',')[1]))

    # image = Image.open(im_bytes)
    # image_nparray = np.array(image)[:,:,:3]
    # get_predicted_objects_yolo(image_nparray)

    # Using Microsoft Azure Computer Vision API
    response = cv_client.analyze_image_in_stream(image_bytes, [VisualFeatureTypes.tags, VisualFeatureTypes.categories])
    
    if response.tags:
        print('Tags:')
        for tag in response.tags:
            print(tag.name)

    if response.categories:
        print('Categories:')
        for category in response.categories:
            print(category.name)
    
    
    print()


    return

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