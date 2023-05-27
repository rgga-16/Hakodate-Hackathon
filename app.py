from flask import Flask, send_from_directory, request
import random, requests, base64, cv2, os
import numpy as np
from io import BytesIO
from PIL import Image
from ultralytics import YOLO


from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

subscription_key = os.getenv("VISION_KEY")
endpoint = os.getenv("VISION_ENDPOINT")

cv_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

import infer

app = Flask(__name__, static_folder="./client/public")

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
@app.route("/")
def base():
    return send_from_directory('./client/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('./client/public', path)


if __name__ == "__main__":
    app.run(debug=True)