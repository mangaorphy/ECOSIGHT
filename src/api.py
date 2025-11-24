"""
FastAPI Backend for Wildlife Sound Classification Model
Author: EcoSight Team
Date: 2025-11-17

Features:
- Model predictions endpoint
- Model retraining trigger
- Model status and uptime monitoring
- File upload for new data
- Performance metrics
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import numpy as np
import librosa
import soundfile as sf
import tensorflow as tf
import tensorflow_hub as hub
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Wildlife Sound Classification API",
    description="Anti-Poaching Wildlife Protection System - Audio Classification API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
MODEL = None
YAMNET_MODEL = None
CLASS_NAMES = []
MODEL_METADATA = {}
START_TIME = datetime.now()
PREDICTION_COUNT = 0
RETRAINING_IN_PROGRESS = False

# Paths (adjust these based on your deployment)
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOAD_DIR = BASE_DIR / "uploads"
AUGMENTED_AUDIO_DIR = BASE_DIR / "augmented_audio"
EXTRACTED_AUDIO_DIR = BASE_DIR / "extracted_audio"

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
for class_dir in ["gun_shot", "dog_bark", "engine_idling", "clips"]:
    (AUGMENTED_AUDIO_DIR / class_dir).mkdir(parents=True, exist_ok=True)
    (EXTRACTED_AUDIO_DIR / class_dir).mkdir(parents=True, exist_ok=True)


# ============================================================================
# STARTUP: DOWNLOAD MODEL FROM S3
# ============================================================================

def load_model_artifacts():
    """Load model, class names, and metadata on startup"""
    global MODEL, YAMNET_MODEL, CLASS_NAMES, MODEL_METADATA
    
    try:
        logger.info("Loading model artifacts...")
        
        # Load YAMNet pretrained model with timeout handling
        logger.info("Loading YAMNet pretrained model...")
        try:
            yamnet_model_url = 'https://tfhub.dev/google/yamnet/1'
            YAMNET_MODEL = hub.load(yamnet_model_url)
            logger.info("✓ YAMNet model loaded")
        except Exception as e:
            logger.error(f"Failed to load YAMNet: {e}")
            logger.warning("YAMNet will be loaded on first prediction request")
            YAMNET_MODEL = None
        
        # Load classifier model with custom objects for compatibility
        model_path = MODELS_DIR / "yamnet_classifier_v2.keras"
        # Fallback to original if v2 doesn't exist
        if not model_path.exists():
            model_path = MODELS_DIR / "yamnet_classifier.keras"
        
        if model_path.exists():
            try:
                # Try loading with compile=False to avoid optimizer issues
                MODEL = tf.keras.models.load_model(model_path, compile=False)
                # Recompile the model
                MODEL.compile(
                    optimizer='adam',
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy']
                )
                logger.info(f"✓ Classifier model loaded from {model_path}")
            except Exception as e:
                logger.error(f"Error loading keras model: {e}")
                logger.info("Attempting to load as SavedModel format...")
                try:
                    # Try loading the .h5 or rebuild from architecture
                    MODEL = tf.keras.models.load_model(str(model_path).replace('.keras', '.h5'))
                    logger.info("✓ Loaded from .h5 format")
                except:
                    logger.warning(f"Could not load model. Model will need to be retrained.")
                    MODEL = None
        else:
            logger.warning(f"Model not found at {model_path}")
            MODEL = None
        
        # Load class names
        class_names_path = MODELS_DIR / "class_names.json"
        if class_names_path.exists():
            with open(class_names_path, 'r') as f:
                CLASS_NAMES = json.load(f)
            logger.info(f"✓ Class names loaded: {CLASS_NAMES}")
        
        # Load metadata
        metadata_path = MODELS_DIR / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                MODEL_METADATA = json.load(f)
            logger.info("✓ Model metadata loaded")
            
            # If model failed to load, try rebuilding from metadata and weights
            if MODEL is None and model_path.exists():
                logger.info("Attempting to rebuild model from metadata and load weights...")
                MODEL = build_model_from_metadata(MODEL_METADATA)
                if MODEL is not None:
                    try:
                        # Try to load just the weights
                        weights_path = str(model_path).replace('.keras', '_weights.h5')
                        if Path(weights_path).exists():
                            MODEL.load_weights(weights_path)
                            logger.info("✓ Model weights loaded successfully")
                        else:
                            logger.warning("Weights file not found. Model initialized with random weights.")
                    except Exception as e:
                        logger.warning(f"Could not load weights: {e}. Model needs retraining.")

        
        logger.info("Model artifacts loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading model artifacts: {e}")
        logger.error(f"Stack trace:", exc_info=True)
        # Don't crash the API - allow it to start even if model loading fails
        logger.warning("API starting without model loaded. Model will need to be retrained.")


@app.on_event("startup")
async def startup_event():
    """Initialize models on API startup"""
    try:
        logger.info("Starting up API...")

        # Define required files
        required_files = [
            "yamnet_classifier_v2.keras",
            "class_names.json",
            "model_metadata.json",
            "performance_metrics.json",
            "training_history.pkl",
        ]

        # Check if any required file is missing
        missing_files = []
        for filename in required_files:
            file_path = MODELS_DIR / filename
            if not file_path.exists():
                missing_files.append(filename)

        if missing_files:
            logger.info(f"Missing files: {missing_files}. Downloading from S3...")
            try:
                from src.s3_storage import S3Storage
                s3 = S3Storage()
                # Assuming your S3Storage class has a method to download the entire models folder
                # Or modify it to download specific files
                success = s3.download_model(str(MODELS_DIR))

                if success:
                    logger.info("✓ Model and metrics downloaded from S3")
                else:
                    logger.error("✗ Failed to download model and metrics from S3")
            except Exception as e:
                logger.error(f"Error downloading model and metrics from S3: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.info("All required files found locally, skipping download")

        # Load model artifacts
        load_model_artifacts()

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        logger.warning("API starting with limited functionality")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PredictionResponse(BaseModel):
    success: bool
    predicted_class: str
    confidence: float
    all_probabilities: Dict[str, float]
    processing_time: float
    timestamp: str


class ModelStatusResponse(BaseModel):
    status: str
    uptime: str
    total_predictions: int
    model_loaded: bool
    model_name: str
    training_date: str
    test_accuracy: float
    num_classes: int
    classes: List[str]


class RetrainingRequest(BaseModel):
    trigger_reason: Optional[str] = "Manual trigger"
    min_new_samples: Optional[int] = 100


class RetrainingResponse(BaseModel):
    success: bool
    message: str
    status: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_yamnet_embeddings(audio_path: Path, max_duration: int = 4):
    """
    Extract YAMNet embeddings from audio file
    
    Args:
        audio_path: Path to audio file
        max_duration: Maximum duration in seconds
    
    Returns:
        Mean embedding vector (1024 dimensions)
    """
    global YAMNET_MODEL
    
    # Lazy load YAMNet if not already loaded
    if YAMNET_MODEL is None:
        logger.info("Loading YAMNet model (lazy load)...")
        try:
            yamnet_model_url = 'https://tfhub.dev/google/yamnet/1'
            YAMNET_MODEL = hub.load(yamnet_model_url)
            logger.info("✓ YAMNet model loaded")
        except Exception as e:
            logger.error(f"Failed to load YAMNet: {e}")
            raise HTTPException(status_code=503, detail=f"Could not load YAMNet model: {e}")
    
    # Load audio at 16kHz (YAMNet's required sample rate)
    audio, sr = librosa.load(audio_path, sr=16000, duration=max_duration)
    audio = audio.astype(np.float32)
    
    # Get YAMNet predictions
    scores, embeddings, spectrogram = YAMNET_MODEL(audio)
    
    # Average embeddings over time
    embedding_mean = np.mean(embeddings.numpy(), axis=0)
    
    return embedding_mean


def get_uptime():
    """Calculate API uptime"""
    uptime = datetime.now() - START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days}d {hours}h {minutes}m {seconds}s"


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Wildlife Sound Classification API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "predict": "/predict",
            "status": "/status",
            "retrain": "/retrain",
            "upload": "/upload",
            "metrics": "/metrics"
        }
    }


@app.get("/status", response_model=ModelStatusResponse)
async def get_status():
    """Get model status and uptime information"""
    global PREDICTION_COUNT
    
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return ModelStatusResponse(
        status="operational",
        uptime=get_uptime(),
        total_predictions=PREDICTION_COUNT,
        model_loaded=MODEL is not None,
        model_name=MODEL_METADATA.get("model_name", "Unknown"),
        training_date=MODEL_METADATA.get("training_date", "Unknown"),
        test_accuracy=MODEL_METADATA.get("test_accuracy", 0.0),
        num_classes=len(CLASS_NAMES),
        classes=CLASS_NAMES
    )


@app.get("/metrics")
async def get_metrics():
    """Get detailed performance metrics"""
    metrics_path = MODELS_DIR / "performance_metrics.json"
    
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics file not found")
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    return JSONResponse(content=metrics)


@app.get("/training-history")
async def get_training_history():
    """Get model retraining history with learning curves"""
    history_path = MODELS_DIR / "training_history.pkl"
    retraining_log_path = MODELS_DIR / "retraining_log.json"
    
    response = {
        "has_history": False,
        "training_history": None,
        "retraining_log": None
    }
    
    # Load training history (loss/accuracy curves)
    if history_path.exists():
        try:
            import pickle
            with open(history_path, 'rb') as f:
                history = pickle.load(f)
                response["has_history"] = True
                response["training_history"] = {
                    "loss": history.get("loss", []),
                    "val_loss": history.get("val_loss", []),
                    "accuracy": history.get("accuracy", []),
                    "val_accuracy": history.get("val_accuracy", []),
                    "epochs": list(range(1, len(history.get("loss", [])) + 1))
                }
        except Exception as e:
            logger.error(f"Error loading training history: {e}")
    
    # Load retraining log
    if retraining_log_path.exists():
        try:
            with open(retraining_log_path, 'r') as f:
                response["retraining_log"] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading retraining log: {e}")
    
    return JSONResponse(content=response)


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    """
    Predict wildlife sound class from uploaded audio file
    
    Args:
        file: Audio file (.wav or .mp3)
    
    Returns:
        Prediction results with confidence scores
    """
    global PREDICTION_COUNT
    
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Classifier model not loaded. Please retrain the model first.")
    
    # Validate file type
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Supported: .wav, .mp3, .ogg, .flac"
        )
    
    start_time = datetime.now()
    
    try:
        # Save uploaded file temporarily
        temp_path = UPLOAD_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract YAMNet embeddings
        embedding = extract_yamnet_embeddings(temp_path)
        
        # Normalize embedding (same as training)
        embedding_normalized = (embedding - embedding.mean()) / embedding.std()
        embedding_normalized = embedding_normalized.reshape(1, -1)
        
        # Get prediction
        prediction = MODEL.predict(embedding_normalized, verbose=0)
        predicted_class_idx = np.argmax(prediction[0])
        predicted_class = CLASS_NAMES[predicted_class_idx]
        confidence = float(prediction[0][predicted_class_idx])
        
        # Get all probabilities
        all_probs = {
            CLASS_NAMES[i]: float(prediction[0][i])
            for i in range(len(CLASS_NAMES))
        }
        
        # Clean up temp file
        temp_path.unlink()
        
        # Update prediction count
        PREDICTION_COUNT += 1
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PredictionResponse(
            success=True,
            predicted_class=predicted_class,
            confidence=confidence,
            all_probabilities=all_probs,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        # Clean up temp file if exists
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/upload")
async def upload_training_data(
    file: UploadFile = File(...),
    class_name: str = Form("unknown")  # <--- CHANGED: Use Form() to read from body
):
    """
    Upload new audio file for training data
    """
    # Validate class name
    if class_name not in CLASS_NAMES and class_name != "unknown":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid class name. Valid classes: {CLASS_NAMES}"
        )
    
    try:
        # Create class directory if needed
        class_dir = EXTRACTED_AUDIO_DIR / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file to extracted_audio (originals)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize filename to prevent directory traversal or spaces
        safe_filename = Path(file.filename).name
        filename = f"{timestamp}_{safe_filename}"
        file_path = class_dir / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to extracted_audio: {file_path}")
        
        # Upload to S3 if configured
        s3_uploaded = False
        try:
            from src.s3_storage import S3Storage
            s3 = S3Storage()
            # Upload single file to S3
            s3_key = f"extracted_audio/{class_name}/{filename}"
            s3_uploaded = s3.upload_file(str(file_path), s3_key)
            if s3_uploaded:
                logger.info(f"File uploaded to S3: {s3_key}")
        except Exception as s3_error:
            # We catch specific S3 errors so the main upload doesn't fail
            logger.warning(f"S3 upload failed (continuing anyway): {s3_error}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_path": str(file_path),
            "class": class_name,
            "s3_uploaded": s3_uploaded,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        # Fixed: Removed the duplicate raise line
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/retrain", response_model=RetrainingResponse)
async def trigger_retraining(
    request: RetrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger model retraining
    
    Args:
        request: Retraining parameters
        background_tasks: FastAPI background tasks
    
    Returns:
        Retraining status
    """
    global RETRAINING_IN_PROGRESS
    
    if RETRAINING_IN_PROGRESS:
        return RetrainingResponse(
            success=False,
            message="Retraining already in progress",
            status="in_progress"
        )
    
    # Start retraining in background
    def run_retraining():
        global RETRAINING_IN_PROGRESS, MODEL
        RETRAINING_IN_PROGRESS = True
        
        try:
            import subprocess
            
            logger.info(f"Starting retraining: {request.trigger_reason}")
            
            # Run the retraining script from the correct path
            script_path = Path("/app/scripts/retrain_model.py")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info("✓ Retraining completed successfully")
                logger.info(result.stdout)
                
                # Reload the model
                model_path = MODELS_DIR / "yamnet_classifier_v2.keras"
                if model_path.exists():
                    MODEL = tf.keras.models.load_model(model_path, compile=False)
                    MODEL.compile(
                        optimizer='adam',
                        loss='sparse_categorical_crossentropy',
                        metrics=['accuracy']
                    )
                    logger.info("✓ New model loaded successfully")
            else:
                logger.error(f"Retraining failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Retraining error: {e}")
        finally:
            RETRAINING_IN_PROGRESS = False
    
    # Add to background tasks
    background_tasks.add_task(run_retraining)
    
    logger.info(f"Retraining triggered: {request.trigger_reason}")
    
    return RetrainingResponse(
        success=True,
        message="Retraining started in background. Check logs for progress.",
        status="running"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": MODEL is not None
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
