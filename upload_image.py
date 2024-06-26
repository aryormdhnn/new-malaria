import streamlit as st
import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing import image
import cv2
import pickle

def preprocess_image(img, target_size):
    img = img.resize(target_size)
    array = image.img_to_array(img)
    array = np.expand_dims(array, axis=0)
    return array

def is_valid_image(img):
    return img.mode == 'RGB' and len(img.getbands()) == 3

def calculate_histogram(image):
    image = cv2.resize(image, (128, 128))  # Ensure consistent size for histogram calculation
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

def load_histograms(histogram_file):
    with open(histogram_file, 'rb') as file:
        histograms = pickle.load(file)
    return [np.array(hist, dtype=np.float32) for hist in histograms]

def compare_histograms(image_hist, reference_histograms):
    highest_similarity = -1
    for ref_hist in reference_histograms:
        similarity = cv2.compareHist(np.array(image_hist, dtype=np.float32), np.array(ref_hist, dtype=np.float32), cv2.HISTCMP_CORREL)
        if similarity > highest_similarity:
            highest_similarity = similarity
    return highest_similarity

def show_upload_image(model, infected_histograms, uninfected_histograms):
    st.markdown("<h1 style='text-align: center; color: white;'>Aplikasi Deteksi Malaria</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: grey;'>Unggah gambar untuk mendeteksi malaria. Ukuran file maksimum adalah 100 KB.</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Unggah gambar untuk mendeteksi malaria. Ukuran file maksimum adalah 100 KB.", type=["png", "jpg", "jpeg", "bmp"], help="Limit 100KB per file • PNG, JPG, JPEG, BMP")

    if uploaded_file is not None:
        file_size = uploaded_file.size
        if file_size > 100 * 1024:  # 100 KB limit
            st.warning("Gambar yang diunggah terlalu besar. Silakan unggah gambar yang lebih kecil dari 100 KB.")
        else:
            try:
                img = Image.open(uploaded_file)
                
                if not is_valid_image(img):
                    st.warning("Gambar yang diunggah tidak sesuai dengan karakteristik yang diharapkan dari dataset. Silakan unggah gambar berwarna (RGB).")
                else:
                    img_array = preprocess_image(img, target_size=(128, 128))  # Resize image for model input
                    img_gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

                    image_hist = calculate_histogram(img_gray)
                    infected_similarity = compare_histograms(image_hist, infected_histograms)
                    uninfected_similarity = compare_histograms(image_hist, uninfected_histograms)

                    similarity_threshold = 0.05  # Adjusted this value based on observed similarities

                    if infected_similarity > similarity_threshold or uninfected_similarity > similarity_threshold:
                        with st.spinner('Mengklasifikasikan...'):
                            prediction = model.predict(img_array)
                            malaria_probability = prediction[0][0] * 100
                            classification_result = 'Malaria' if malaria_probability > 50 else 'Bukan Malaria'

                        st.image(img, caption='Unggah Gambar', use_column_width=True, channels="RGB")
                        st.markdown(f"<h3 style='text-align: center; color: white;'>Prediksi: {classification_result}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: grey;'>Kemungkinan: {malaria_probability:.2f}%</p>", unsafe_allow_html=True)

                        st.progress(malaria_probability / 100)

                        if 'results' not in st.session_state:
                            st.session_state['results'] = []
                        st.session_state['results'].append({
                            "Image": uploaded_file.name,
                            "Prediction": classification_result,
                            "Probability": f"{malaria_probability:.2f}%"
                        })
                    else:
                        st.warning("Gambar yang diunggah tidak sesuai dengan gambar sel darah. Silakan unggah gambar yang benar.")
            except Exception as e:
                st.warning(f"Terjadi kesalahan saat memproses gambar: {e}")

if __name__ == "__main__":
    from tensorflow.keras.models import load_model
    model = load_model('Nadam_TTS_Epoch50.h5')  # Load your model here
    infected_histograms = load_histograms('infected_histograms.pkl')  # Load infected histograms
    uninfected_histograms = load_histograms('uninfected_histograms.pkl')  # Load uninfected histograms
    show_upload_image(model, infected_histograms, uninfected_histograms)
