import os
import shutil
from fastapi import APIRouter, UploadFile, File
from src.parser import TrafficParser
from backend.schemas.requests import ScenarioResponse

router = APIRouter()

@router.post("/upload", response_model=ScenarioResponse)
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("scratch", exist_ok=True)
    temp_path = os.path.join("scratch", file.filename)
    
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
