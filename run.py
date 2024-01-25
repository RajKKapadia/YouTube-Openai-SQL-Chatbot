import gradio as gr
from fastapi import FastAPI

from gradio_ui import demo

app = FastAPI()

@app.get('/')
def home():
    return 'Gradio UI is running at /gradio', 200

app = gr.mount_gradio_app(app, demo, '/gradio')
