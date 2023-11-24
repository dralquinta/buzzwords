from flask import Flask, render_template, request, redirect, url_for, send_file
import qrcode
from PIL import Image
from wordcloud import WordCloud
from io import BytesIO, StringIO
import threading
import time
import base64

app = Flask(__name__)

words = []
lock = threading.Lock()
wordcloud_img = None

def generate_wordcloud_image():
    global words
    global wordcloud_img

    while True:
        time.sleep(60)  # Generate word cloud every 60 seconds

        with lock:
            if words:
                text = ' '.join(words)
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

                img_bytes_io = BytesIO()
                wordcloud.to_image().save(img_bytes_io, format='PNG')
                img_bytes_io.seek(0)

                wordcloud_img = img_bytes_io.read()
                words = []  # Clear the list of words

# Start a separate thread for generating the word cloud in the background
wordcloud_thread = threading.Thread(target=generate_wordcloud_image)
wordcloud_thread.daemon = True
wordcloud_thread.start()

@app.route('/')
def landing_page():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data("http://127.0.0.1:5000/submit_word")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_bytes_io = BytesIO()
    img.save(img_bytes_io)
    img_bytes_io.seek(0)

    # Encode the image bytes using base64
    img_base64 = base64.b64encode(img_bytes_io.read()).decode('utf-8')

    return render_template('landing_page.html', qr_image=img_base64)

@app.route('/submit_word', methods=['POST'])
def submit_word():
    word = request.form.get('word')
    if word:
        with lock:
            words.append(word)
        return redirect(url_for('landing_page'))
    return "No word submitted"

@app.route('/wordcloud')
def display_wordcloud():
    if wordcloud_img:
        return send_file(BytesIO(wordcloud_img), mimetype='image/png')
    return "Word cloud not available yet"

if __name__ == "__main__":
    app.run(debug=True)
