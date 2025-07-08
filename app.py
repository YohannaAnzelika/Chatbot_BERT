import torch
import torch.nn as nn
import json
from flask import Flask, request, jsonify
from utils import tokenize, bag_of_words
from model import NeuralNet
from flask_cors import CORS
import difflib

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = Flask(__name__)
CORS(app)

# Load intents
with open("intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)["intents"]

# Load model
data = torch.load("model.pth")
input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]

model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(data["model_state"])
model.eval()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "").lower()

    # Jika pertanyaan mengandung kata kunci untuk semua/daftar situs
    trigger_keywords = [
        "semua", "seluruh", "situs apa saja", "daftar situs", "akses apa saja",
        "apa saja yang tersedia", "situs web apa saja yang ada disini","website yang ada", "link apa saja"
    ]
    if any(k in query for k in trigger_keywords):
        all_links = []
        for intent in intents:
            tag = intent["tag"]
            for response in intent["responses"]:
                url = next((word for word in response.split() if word.startswith("http")), "")
                if url:
                    description = response.replace(url, "").strip()
                    all_links.append({
                        "description": description,
                        "url": url,
                        "keyword": tag
                    })
        return jsonify({
            "answer": {
                "description": "",
                "url": "",
                "all_links": all_links,
                "tag": "all"
            }
        })

    # Tokenisasi & prediksi model
    sentence = tokenize(query)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]
    prob = torch.softmax(output, dim=1)[0][predicted.item()]

    if prob >= 0.5:
        for intent in intents:
            if intent["tag"] == tag:
                if tag == "greeting":
                    return jsonify({
                        "answer": {
                            "description": intent["responses"][0],
                            "url": "",
                            "all_links": [],
                            "tag": tag
                        }
                    })
                else:
                    all_links = []
                    for response in intent["responses"]:
                        url = next((word for word in response.split() if word.startswith("http")), "")
                        description = response.replace(url, "").strip() if url else response
                        all_links.append({
                            "description": description,
                            "url": url,
                            "keyword": tag
                        })
                    return jsonify({
                        "answer": {
                            "description": all_links[0]["description"] if all_links else "",
                            "url": all_links[0]["url"] if all_links else "",
                            "all_links": all_links,
                            "tag": tag
                        }
                    })

    # Fallback ke pencocokan pattern manual dengan fuzzy match
    fallback_links = []
    for intent in intents:
        tag = intent["tag"]
        for pattern in intent["patterns"]:
            pattern_l = pattern.lower()
            if query in pattern_l or difflib.get_close_matches(query, [pattern_l], cutoff=0.7):
                for response in intent["responses"]:
                    url = next((word for word in response.split() if word.startswith("http")), "")
                    description = response.replace(url, "").strip() if url else response
                    fallback_links.append({
                        "description": description,
                        "url": url,
                        "keyword": tag
                    })
                break

    if fallback_links:
        return jsonify({
            "answer": {
                "description": fallback_links[0]["description"],
                "url": fallback_links[0]["url"],
                "all_links": fallback_links,
                "tag": tag
            }
        })

    return jsonify({
        "answer": {
            "description": "Maaf, saya belum menemukan link yang cocok. Silakan coba lagi.",
            "url": "",
            "all_links": [],
            "tag": "unknown"
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
