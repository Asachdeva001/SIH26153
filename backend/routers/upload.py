import os
import shutil
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from backend.src.parser import TrafficParser
from backend.schemas.requests import ScenarioResponse

router = APIRouter()

MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 500 * 1024 * 1024))

@router.post("/upload", response_model=ScenarioResponse)
def upload_file(request: Request, file: UploadFile = File(...)):
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload Too Large")

    os.makedirs("scratch", exist_ok=True)
    safe_filename = os.path.basename(file.filename)
    temp_path = os.path.join("scratch", safe_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    parser = TrafficParser(window_size_sec=10.0)
    
    if file.filename.endswith('.csv'):
        df_parsed = parser.parse_csv(temp_path)
    else:
        df_parsed = parser.parse_pcap(temp_path)
        
    df_win = parser.create_time_windows(df_parsed)
    
    df_win_clean = df_win.replace({float('nan'): None})
    windows = df_win_clean.to_dict(orient='records')
    
    df_raw_sub = df_parsed.head(50).replace({float('nan'): None})
    raw_packets = df_raw_sub.to_dict(orient='records')
    
    for pkt in raw_packets:
        if 'timestamp_dt' in pkt and pkt['timestamp_dt'] is not None:
            pkt['timestamp'] = str(pkt['timestamp_dt'])
        elif 'timestamp' in pkt and pkt['timestamp'] is not None:
            pkt['timestamp'] = str(pkt['timestamp'])
            
    return {"windows": windows, "raw_packets": raw_packets}
