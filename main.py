from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil
from datetime import datetime

from reader import load_file
from merger import merge_ranges
from ip_utils import int_to_ip
import pandas as pd

app = FastAPI()

# ---------------- CORS (IMPORTANT FOR NETLIFY) ---------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your Netlify URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DIRECTORIES ---------------- #
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- STATIC FILES ---------------- #
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------- CORE PROCESSING ---------------- #
def process_file(file_path: str):
    df = load_file(file_path)
    merged = merge_ranges(df)

    data = [
        {"First IP": int_to_ip(start), "Last IP": int_to_ip(end)}
        for start, end in merged
    ]

    df_out = pd.DataFrame(data)

    output_name = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    df_out.to_excel(output_path, index=False)

    return output_path


# ---------------- ROUTES ---------------- #

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/process")
async def process(file: UploadFile = File(...)):

    # ---------------- FILE VALIDATION ---------------- #
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".csv")):
        return JSONResponse(
            status_code=400,
            content={"error": "Only .xlsx or .csv files are allowed"}
        )

    # ---------------- SAFE FILE NAME ---------------- #
    safe_filename = f"{datetime.now().timestamp()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # ---------------- SAVE FILE ---------------- #
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---------------- PROCESS FILE ---------------- #
    try:
        output_file = process_file(file_path)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"}
        )
    finally:
        # cleanup uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    # ---------------- RETURN DOWNLOAD ---------------- #
    return FileResponse(
        path=output_file,
        filename=os.path.basename(output_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---------------- DEPLOYMENT ENTRY ---------------- #
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # Railway/Cloud support
    uvicorn.run(app, host="0.0.0.0", port=port)
