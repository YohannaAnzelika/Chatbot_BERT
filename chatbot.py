import streamlit as st
import requests
import base64

backend_url = "http://localhost:5000/chat"

def chat_with_bot(query):
    response = requests.post(backend_url, json={'query': query})
    return response.json().get('answer') if response.status_code == 200 else {
        "description": "Terjadi kesalahan saat berkomunikasi dengan server.",
        "url": ""
    }

def get_base64_of_bin_file(bin_file_path):
    with open(bin_file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_custom_css(dark_mode):
    if dark_mode:
        bg_gradient = "#0a192f"
        text_color = "#ffffff"
        input_bg = "#112240"
        box_bg = "#1f2937"
        link_color = "#64ffda"
        sidebar_bg = "#0a192f"
        sidebar_text = "#ffffff"
        label_color = "#ffffff"
    else:
        bg_gradient = "#e3f2fd"
        text_color = "#0a1932"
        input_bg = "#ffffff"
        box_bg = "#f1f5f9"
        link_color = "#0a1932"
        sidebar_bg = "#ffffff"
        sidebar_text = "#0a1932"
        label_color = "#0a1932"

    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            background-color: {bg_gradient};
        }}

        .navbar {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 16px;
            background: linear-gradient(to right, rgba(10,25,50,0.85), rgba(33,80,120,0.85));
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}

        .navbar img {{
            height: 64px;
            margin-right: 15px;
            background-color: white;
            border-radius: 12px;
            padding: 6px;
            border: 1px solid #ccc;
        }}

        .navbar h1 {{
            color: white;
            font-size: 1.9rem;
            margin: 0;
        }}

        label, .stTextInput label {{
            color: {label_color} !important;
            font-weight: 600;
        }}

        .stTextInput input {{
            background-color: {input_bg};
            color: {text_color};
            border: 2px solid #888;
            border-radius: 10px;
            padding: 12px;
        }}

        .btn-link {{
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            color: #ffffff;
            padding: 10px 18px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            display: inline-block;
            margin-top: 5px;
            box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.3);
        }}

        .btn-link:hover {{
            background: #00c6ff;
            text-decoration: none;
        }}

        .link-box {{
            background-color: {box_bg};
            padding: 16px 20px;
            border-radius: 12px;
            margin-top: 20px;
            color: {text_color};
            font-size: 16px;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.2);
        }}

        .link-box a {{
            color: {link_color};
            text-decoration: none;
            font-weight: bold;
        }}

        .link-box a:hover {{
            text-decoration: underline;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            padding-top: 1.5rem;
            padding-right: 1.5rem;
            padding-left: 1.5rem;
            background-color: {sidebar_bg};
            color: {sidebar_text};
            height: 100%;
            border-top-right-radius: 1rem;
            border-bottom-right-radius: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def main():
    st.set_page_config(page_title="Chatbot PTPN IV", page_icon="🤖", layout="wide")

    if "history" not in st.session_state:
        st.session_state.history = []

    st.sidebar.title("⚙️ Pengaturan")
    dark_mode = st.sidebar.toggle("🌗 Mode Gelap", value=True)
    show_history = st.sidebar.checkbox("📜 Tampilkan Riwayat Pertanyaan", value=True)

    inject_custom_css(dark_mode)

    logo_base64 = get_base64_of_bin_file("logo.png")
    st.markdown(
        f"""
        <div class="navbar">
            <img src="data:image/png;base64,{logo_base64}" alt="PTPN IV Logo">
            <h1>Chatbot PTPN IV</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    user_input = st.text_input(
        "Tanyakan sesuatu tentang PTPN IV:",
        help="Masukkan pertanyaan seperti: produksi harian, profil ptpn, dll.",
        placeholder="Contoh: produksi harian"
    )

    if user_input:
        st.session_state.history.append(user_input)
        answer = chat_with_bot(user_input)
        description = answer.get("description", "").strip()
        url = answer.get("url", "").strip()
        all_links = answer.get("all_links", [])

        if all_links:
            st.markdown(f"<div class='link-box'>{description}</div>", unsafe_allow_html=True)

            search_query = st.text_input("🔎 Cari di daftar sistem/aplikasi:", "")
            filtered_links = [
                item for item in all_links
                if search_query.lower() in item["description"].lower()
                or search_query.lower() in item["keyword"].lower()
            ]

            for item in filtered_links:
                st.markdown(f"""
                    <div style="margin: 10px 0;">
                        🔗 <a href="{item['url']}" target="_blank">{item['description']}</a>
                    </div>
                """, unsafe_allow_html=True)

            if not filtered_links:
                st.info("Tidak ditemukan sistem dengan kata tersebut.")

        elif description and url:
            st.markdown(f"""
                <div class="link-box">
                    {description}<br><br>
                    <a class="btn-link" href="{url}" target="_blank">🔗 Kunjungi Aplikasi</a>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.warning(description or "Maaf, saya tidak menemukan informasi yang relevan.")

    if show_history:
        st.sidebar.markdown("## 🕒 Riwayat Pertanyaan")
        if st.session_state.history:
            for i, q in enumerate(reversed(st.session_state.history[-10:]), 1):
                st.sidebar.markdown(f"{i}. {q}")
        else:
            st.sidebar.caption("Belum ada riwayat.")

if __name__ == "__main__":
    main()
