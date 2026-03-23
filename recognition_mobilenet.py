# recognition_mobilenet.py
import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image

# Load pretrained MobileNetV2 once
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
model.eval()

# image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# load ImageNet labels
import json
import urllib.request

LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
imagenet_labels = urllib.request.urlopen(LABELS_URL).read().decode("utf-8").split("\n")

def predict_product(image_path):
    """
    Returns:
    [
       {"name": "laptop", "confidence": 78.5},
       {"name": "notebook", "confidence": 12.1},
       ...
    ]
    """
    try:
        image = Image.open(image_path).convert("RGB")
        img_tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

        # top 5 predictions
        top5 = torch.topk(probabilities, 5)

        results = []
        for idx, score in zip(top5.indices, top5.values):
            name = imagenet_labels[idx.item()]
            confidence = float(score.item() * 100)
            results.append({
                "name": name,
                "confidence": confidence
            })

        return results

    except Exception as e:
        print("MobileNet error:", e)
        return [{"name": "unknown", "confidence": 0}]
