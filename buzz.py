from flask import Flask, render_template, request, redirect, url_for
import qrcode
from wordcloud import WordCloud
from io import BytesIO
import threading
import base64
import os
import time

app = Flask(__name__)

words = []
lock = threading.Lock()
wordcloud_img_path = 'wordcloud.png'

def generate_wordcloud_image():
    global words
    global wordcloud_img_path

    while True:
        with lock:
            if words:
                text = ' '.join(words)
                wordcloud = WordCloud(width=800, height=400, background_color='white')
                wordcloud.generate(text)

                wordcloud.to_file(wordcloud_img_path)

                words = []

        # Sleep after generating the word cloud
        time.sleep(60)

# Start a separate thread for generating the word cloud in the background
wordcloud_thread = threading.Thread(target=generate_wordcloud_image)
wordcloud_thread.daemon = True
wordcloud_thread.start()

# Sleep to ensure the word cloud thread has time to generate the initial image
time.sleep(10)

@app.route('/')
def landing_page():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data("http://144.22.51.76/submit_word")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_bytes_io = BytesIO()
    img.save(img_bytes_io)
    img_bytes_io.seek(0)

    img_base64 = base64.b64encode(img_bytes_io.read()).decode('utf-8')

    # Check if the word cloud image file exists
    if os.path.exists(wordcloud_img_path):
        with open(wordcloud_img_path, 'rb') as img_file:
            wordcloud_img = base64.b64encode(img_file.read()).decode('utf-8')
    else:
        wordcloud_img = None

    # Generate the link to the word cloud page
    wordcloud_link = url_for('display_wordcloud')

    return render_template('landing_page.html', qr_image=img_base64, wordcloud_link=wordcloud_link, wordcloud_img=wordcloud_img)

@app.route('/submit_word', methods=['GET', 'POST'])
def submit_word():
    if request.method == 'POST':
        word = request.form.get('word')
        if word:
            with lock:
                words.append(word)
            return redirect(url_for('landing_page'))
        return "No word submitted"
    else:
        return render_template('submit_word_page.html')

@app.route('/wordcloud')
def display_wordcloud():
    if os.path.exists(wordcloud_img_path):
        with open(wordcloud_img_path, 'rb') as img_file:
            wordcloud_img = base64.b64encode(img_file.read()).decode('utf-8')
        return render_template('wordcloud_page.html', wordcloud_img=wordcloud_img)
    return "Word cloud not available yet"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
