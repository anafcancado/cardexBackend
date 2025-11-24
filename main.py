from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List  # ✅ IMPORTAÇÃO NECESSÁRIA
import requests
import io

app = FastAPI(title="Render Gateway API (DEBUG MODE)", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Coloque aqui o link do Cloudflare ativo do Colab
COLAB_URL_BASE = "https://local-lows-strikes-consequence.trycloudflare.com"
COLAB_PREDICT_URL = f"{COLAB_URL_BASE}/predict"
COLAB_PREDICT_BATCH_URL = f"{COLAB_URL_BASE}/predict_batch"


# ============================
# ENDPOINT: Predição simples
# ============================
@app.post("/predict")
async def forward_to_colab(file: UploadFile = File(...)):
    """Forward uma única imagem para o Colab"""
    try:
        image_data = await file.read()
        files = {'file': (file.filename, io.BytesIO(image_data), file.content_type)}

        print(f"📤 [PREDICT] Enviando imagem '{file.filename}' para o Colab...")
        response = requests.post(COLAB_PREDICT_URL, files=files, timeout=60)

        print(f"📥 [PREDICT] Resposta do Colab: {response.status_code}")
        print(f"Conteúdo: {response.text[:300]}")

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"❌ [PREDICT] Erro ao conectar com o Colab: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro de conexão com o Colab (predict): {str(e)}"
        )

    except Exception as e:
        print(f"💥 [PREDICT] Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# ENDPOINT: Predição em batch
# ============================
@app.post("/predict_batch")
async def forward_batch_to_colab(files: List[UploadFile] = File(...)):  # ✅ List do typing
    """Forward múltiplas imagens para o Colab em batch"""
    try:
        # Validar se há arquivos
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="Nenhum arquivo foi enviado"
            )

        print(f"📤 [BATCH] Enviando {len(files)} imagem(ns) para o Colab...")

        # Preparar arquivos para envio
        files_to_send = []
        for file in files:
            image_data = await file.read()
            files_to_send.append(
                ('files', (file.filename, io.BytesIO(image_data), file.content_type))
            )

        print(f"📨 Enviando para: {COLAB_PREDICT_BATCH_URL}")
        response = requests.post(
            COLAB_PREDICT_BATCH_URL,
            files=files_to_send,
            timeout=300  # Timeout maior para batch
        )

        print(f"📥 [BATCH] Resposta do Colab: {response.status_code}")
        print(f"Conteúdo: {response.text[:500]}")

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        print(f"⏱️ [BATCH] Timeout ao processar batch")
        raise HTTPException(
            status_code=504,
            detail="Timeout: o processamento em batch demorou muito tempo"
        )

    except requests.exceptions.RequestException as e:
        print(f"❌ [BATCH] Erro ao conectar com o Colab: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro de conexão com o Colab (predict_batch): {str(e)}"
        )

    except Exception as e:
        print(f"💥 [BATCH] Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# DEBUG ENDPOINTS
# ============================
@app.get("/")
async def root():
    """Informações do gateway"""
    return {
        "message": "Render Gateway API (modo debug) rodando",
        "colab_base_url": COLAB_URL_BASE,
        "endpoints": {
            "/predict": "Forwarda uma única imagem para o Colab",
            "/predict_batch": "Forwarda múltiplas imagens para o Colab em paralelo",
            "/health": "Status de saúde da API",
            "/debug/colab-status": "Verifica se o Colab está acessível"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "Render Gateway API",
        "version": "1.1"
    }


@app.get("/debug/colab-status")
async def colab_status():
    """Verifica se o Colab está acessível"""
    try:
        # Tentar fazer ping no endpoint /predict do Colab
        response = requests.get(f"{COLAB_URL_BASE}/debug/routes", timeout=10)
        
        if response.status_code == 200:
            return {
                "status": "online",
                "colab_url": COLAB_URL_BASE,
                "endpoints": response.json()
            }
        else:
            return {
                "status": "offline",
                "status_code": response.status_code,
                "colab_url": COLAB_URL_BASE
            }

    except requests.exceptions.RequestException as e:
        return {
            "status": "offline",
            "error": str(e),
            "colab_url": COLAB_URL_BASE
        }