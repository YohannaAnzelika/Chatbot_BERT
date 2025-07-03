from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
import torch
from trial_model import ptpn_data, trigger_phrases

app = Flask(__name__)
CORS(app)

# Load IndoBERT model
model = SentenceTransformer("indobenchmark/indobert-base-p1")

# Encode semua deskripsi + keyword
combined_texts = [f"{item['description']} {item['keyword']}" for item in ptpn_data]
desc_embeddings = model.encode(combined_texts, convert_to_tensor=True)

@app.route("/chat", methods=["POST"])
def chat():
    query = request.json.get("query", "").strip().lower()
    if not query:
        return jsonify({"answer": {
            "description": "Silakan masukkan pertanyaan terlebih dahulu."
        }})

    # Respons sapaan langsung
    if query in ["hai", "halo", "hello", "assalamualaikum", "selamat pagi", "selamat siang"]:
        return jsonify({
            "answer": {
                "description": "Hai juga! Ada yang bisa saya bantu seputar PTPN IV?"
            }
        })

    # Trigger untuk menampilkan semua link
    if any(trigger in query for trigger in trigger_phrases):
        return jsonify({
            "answer": {
                "description": "Berikut semua sistem dan aplikasi yang tersedia:",
                "all_links": ptpn_data
            }
        })

    # Jawaban berbasis IndoBERT
    return jsonify({"answer": _get_bert_response(query)})

def _get_bert_response(query):
    query_embedding = model.encode(query, convert_to_tensor=True)
    sim_scores = util.pytorch_cos_sim(query_embedding, desc_embeddings)[0]
    best_idx = torch.argmax(sim_scores).item()
    best_score = sim_scores[best_idx].item()

    if best_score >= 0.37:
        return {
            "description": f"Berikut informasi yang saya temukan:\n\n{ptpn_data[best_idx]['description']}",
            "url": ptpn_data[best_idx]["url"]
        }

    return {
        "description": (
            "Maaf, saya belum menemukan jawaban yang cocok untuk pertanyaan itu. "
            "Silakan coba dengan kata kunci lain atau tanyakan dengan cara berbeda."
        )
    }

@app.route("/all_links", methods=["GET"])
def get_all_data():
    return jsonify(ptpn_data)

if __name__ == "__main__":
    app.run(debug=True)
