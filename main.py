from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import io

app = FastAPI(title="Render Gateway API (DEBUG MODE)", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Coloque aqui o link do ngrok ativo do Colab
COLAB_URL = "https://right-vessels-petition-saving.trycloudflare.com/predict"


@app.post("/predict")
async def forward_to_colab(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        files = {'image': (file.filename, io.BytesIO(image_data), file.content_type)}

        print(f"📤 Enviando imagem '{file.filename}' para o Colab...")
        response = requests.post(COLAB_URL, files=files, timeout=60)

        print(f"📥 Resposta do Colab: {response.status_code}")
        print("Conteúdo bruto:", response.text[:300])  # Mostra os 300 primeiros caracteres

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Captura qualquer erro de rede e exibe no Render
        print(f"❌ Erro ao conectar com o Colab: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão com o Colab: {e}")

    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "Render Gateway API (modo debug) rodando",
        "forward_to": COLAB_URL
    }
