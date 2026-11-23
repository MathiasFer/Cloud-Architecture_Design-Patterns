import os
import time
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/ficha")
def get_ficha():
    chaos_mode = os.getenv("CHAOS_MODE", "none").lower()
    if chaos_mode == "slow":
        time.sleep(5)
    elif chaos_mode == "fail":
        raise HTTPException(status_code=500, detail="Chaos induced failure")
    return {
        "species": "Canis lupus familiaris",
        "size": "Medium",
        "color": "Golden"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
