from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import io
import httpx

app = FastAPI(title="Render Gateway API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL pública gerada pelo ngrok do Colab
COLAB_URL = "https://merideth-unresembling-wyatt.ngrok-free.dev/predict"

@app.post("/predict")
async def forward_to_colab(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        files = {'file': (file.filename, io.BytesIO(image_data), file.content_type)}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(COLAB_URL, files=files)
            response.raise_for_status()

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Render Gateway API rodando", "forward_to": COLAB_URL}
