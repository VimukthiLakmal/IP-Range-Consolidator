from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import os
import shutil
from datetime import datetime

from reader import load_file
from merger import merge_ranges
from ip_utils import int_to_ip
import pandas as pd

app = FastAPI()

# ---------------- DIRECTORIES ---------------- #
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- STATIC ---------------- #
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

@app.get("/")
def home():
    return FileResponse("templates/index.html")


@app.post("/process")
async def process(file: UploadFile = File(...)):

    # ---------------- VALIDATION ---------------- #
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".csv")):
        return JSONResponse(
            status_code=400,
            content={"error": "Only .xlsx or .csv files are allowed"}
        )

    # ---------------- SAVE UPLOADED FILE ---------------- #
    file_path = os.path.join(UPLOAD_DIR, file.filename)

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
        # OPTIONAL CLEANUP (removes uploaded file after processing)
        if os.path.exists(file_path):
            os.remove(file_path)

    # ---------------- RETURN DOWNLOAD ---------------- #
    return FileResponse(
        path=output_file,
        filename=os.path.basename(output_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )