from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import time

app = FastAPI(title="Heart Rate API", version="1.0.0")

# CORS middleware para permitir requests desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo exacto compatible con tu Android app
class HeartRateApiData(BaseModel):
    id: Optional[int] = None  # Se genera automáticamente
    deviceId: str
    minHeartRate: float
    maxHeartRate: float
    avgHeartRate: float
    startTime: int  # timestamp en milliseconds
    endTime: int    # timestamp en milliseconds
    recordedAt: int # timestamp cuando se registró
    syncTimestamp: Optional[int] = None

class ApiResponse(BaseModel):
    success: bool
    message: str
    insertedCount: Optional[int] = None
    duplicatesCount: Optional[int] = None

# Storage en memoria (se reinicia con cada deployment)
heart_rate_storage: List[dict] = []
current_id_counter = 1

def generate_id():
    """Generar ID único"""
    global current_id_counter
    current_id_counter += 1
    return str(current_id_counter)

def check_duplicate(new_data: HeartRateApiData) -> bool:
    """Verificar si ya existe un registro duplicado"""
    for existing in heart_rate_storage:
        if (existing["deviceId"] == new_data.deviceId and
            existing["startTime"] == new_data.startTime and
            existing["endTime"] == new_data.endTime):
            return True
    return False

@app.get("/")
async def root():
    """Endpoint de salud"""
    return {"message": "Heart Rate API is running!", "status": "healthy"}

@app.get("/heartRateData", response_model=List[HeartRateApiData])
async def get_existing_heart_rate_data():
    """Obtener todos los datos existentes - Compatible con tu Android app"""
    return [HeartRateApiData(**item) for item in heart_rate_storage]

@app.post("/heartRateData", response_model=HeartRateApiData)
async def send_single_heart_rate_data(heart_rate_data: HeartRateApiData):
    """Enviar un registro individual - Compatible con sendSingleHeartRateData"""
    
    # Verificar duplicados
    if check_duplicate(heart_rate_data):
        raise HTTPException(
            status_code=409, 
            detail="Duplicate heart rate data detected"
        )
    
    # Generar ID si no viene
    if heart_rate_data.id is None:
        heart_rate_data.id = generate_id()
    
    # Agregar timestamp de sincronización si no viene
    if heart_rate_data.syncTimestamp is None:
        heart_rate_data.syncTimestamp = int(time.time() * 1000)
    
    # Guardar en storage
    heart_rate_storage.append(heart_rate_data.dict())
    
    return heart_rate_data

@app.post("/heartRateData/batch", response_model=List[HeartRateApiData])
async def send_heart_rate_data_batch(heart_rate_data: List[HeartRateApiData]):
    """Enviar múltiples registros - Compatible con sendHeartRateData"""
    
    inserted_data = []
    duplicates_count = 0
    
    for data in heart_rate_data:
        # Verificar duplicados
        if check_duplicate(data):
            duplicates_count += 1
            continue
        
        # Generar ID si no viene
        if data.id is None:
            data.id = generate_id()
        
        # Agregar timestamp de sincronización si no viene
        if data.syncTimestamp is None:
            data.syncTimestamp = int(time.time() * 1000)
        
        # Guardar en storage
        heart_rate_storage.append(data.dict())
        inserted_data.append(data)
    
    return inserted_data

@app.get("/heartRateData/device/{device_id}", response_model=List[HeartRateApiData])
async def get_heart_rate_by_device(device_id: str):
    """Obtener datos por device ID"""
    filtered_data = [
        HeartRateApiData(**item) for item in heart_rate_storage 
        if item["deviceId"] == device_id
    ]
    return filtered_data

@app.get("/heartRateData/{item_id}", response_model=HeartRateApiData)
async def get_heart_rate_by_id(item_id: str):
    """Obtener dato específico por ID"""
    for item in heart_rate_storage:
        if item["id"] == item_id:
            return HeartRateApiData(**item)
    raise HTTPException(status_code=404, detail="Heart rate data not found")

@app.delete("/heartRateData/clear")
async def clear_all_data():
    """Limpiar todos los datos (útil para testing)"""
    global heart_rate_storage, current_id_counter
    count = len(heart_rate_storage)
    heart_rate_storage.clear()
    current_id_counter = 1
    return {"message": f"Cleared {count} records", "count": count}

@app.get("/stats")
async def get_stats():
    """Estadísticas básicas de la API"""
    return {
        "total_records": len(heart_rate_storage),
        "unique_devices": len(set(item["deviceId"] for item in heart_rate_storage)),
        "latest_sync": max([item["syncTimestamp"] for item in heart_rate_storage]) if heart_rate_storage else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)