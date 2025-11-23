"""
EcoSight Model Retraining Script
Automated pipeline for retraining the YAMNet classifier

Author: EcoSight Team
Date: 2025-11-19
"""

import os
import sys
import json
import pickle
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.utils import to_categorical
import warnings
warnings.filterwarnings('ignore')

# Import S3 storage utility and audio augmentation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
try:
    from s3_storage import get_s3_storage
    S3_AVAILABLE = True
except ImportError:
    print("⚠️  S3 storage not available (boto3 not installed)")
    S3_AVAILABLE = False

try:
    from audio_augmentation import augment_directory
    AUGMENTATION_AVAILABLE = True
except ImportError:
    print("⚠️  Audio augmentation not available")
    AUGMENTATION_AVAILABLE = False

# Configure paths
BASE_DIR = Path("/app") if Path("/app").exists() else Path(__file__).parent.parent
EXTRACTED_AUDIO_DIR = BASE_DIR / "extracted_audio"
AUGMENTED_AUDIO_DIR = BASE_DIR / "augmented_audio"
MODELS_DIR = BASE_DIR / "models"
FEATURES_DIR = BASE_DIR / "features"

# Create directories
MODELS_DIR.mkdir(exist_ok=True)
FEATURES_DIR.mkdir(exist_ok=True)

# Configuration
SAMPLE_RATE = 16000  # YAMNet uses 16kHz
EPOCHS = 100
BATCH_SIZE = 64
MIN_NEW_SAMPLES = 100  # Trigger retraining after 100 new samples


class ModelRetrainingPipeline:
    """Automated model retraining pipeline"""
    
    def __init__(self, models_dir, augmented_audio_dir):
        self.models_dir = Path(models_dir)
        self.augmented_audio_dir = Path(augmented_audio_dir)
        self.retraining_log_path = self.models_dir / "retraining_log.json"
        
        # Download training data from S3 if available
        self._download_training_data_from_s3()
        
        # Load retraining history
        if self.retraining_log_path.exists():
            with open(self.retraining_log_path, 'r') as f:
                self.retraining_log = json.load(f)
        else:
            self.retraining_log = {"retraining_history": []}
    
    def _download_training_data_from_s3(self):
        """
        Download extracted audio from S3 and apply augmentation
        
        Workflow:
        1. Download extracted_audio/ from S3 (original/raw files)
        2. Apply augmentation to create augmented_audio/
        3. Use augmented_audio/ for training
        """
        if not S3_AVAILABLE:
            print("ℹ️  S3 not configured, using local training data")
            return
        
        # Check if S3 is configured
        s3_bucket = os.getenv("S3_BUCKET")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        
        if not s3_bucket or not aws_access_key:
            print("ℹ️  S3 credentials not set, using local training data")
            return
        
        print("=" * 70)
        print("DOWNLOADING AND AUGMENTING TRAINING DATA")
        print("=" * 70)
        print(f"📦 Bucket: {s3_bucket}")
        print(f"📥 Downloading to: {EXTRACTED_AUDIO_DIR}")
        print(f"🎵 Augmenting to: {self.augmented_audio_dir}")
        print("")
        
        try:
            # Step 1: Download extracted_audio from S3
            print("Step 1: Downloading extracted audio from S3...")
            s3_storage = get_s3_storage()
            success = s3_storage.download_extracted_audio(str(EXTRACTED_AUDIO_DIR))
            
            if not success:
                print("⚠️  S3 download failed, using local data if available")
                return
            
            # Count downloaded files
            extracted_files = sum(1 for _ in EXTRACTED_AUDIO_DIR.rglob("*.wav")) + \
                             sum(1 for _ in EXTRACTED_AUDIO_DIR.rglob("*.mp3"))
            print(f"✓ Downloaded {extracted_files} extracted audio files")
            print("")
            
            # Step 2: Apply augmentation
            if not AUGMENTATION_AVAILABLE:
                print("⚠️  Augmentation not available, using extracted files directly")
                return
            
            print("Step 2: Applying audio augmentation...")
            print("  This creates multiple variants of each audio file")
            print("  Augmentations: pitch shift, time stretch, noise, volume, etc.")
            print("")
            
            # Create augmented_audio directory
            self.augmented_audio_dir.mkdir(exist_ok=True, parents=True)
            
            # Apply augmentation to all classes
            results = augment_directory(
                input_dir=EXTRACTED_AUDIO_DIR,
                output_dir=self.augmented_audio_dir,
                sr=SAMPLE_RATE,
                augmentations_per_file=5  # Create 5 augmented versions per file
            )
            
            # Show augmentation results
            print("")
            print("Augmentation Results:")
            print("-" * 70)
            for class_name, stats in results.items():
                print(f"  {class_name}: "
                      f"{stats['original_files']} → {stats['augmented_files']} files "
                      f"({stats['increase_factor']:.1f}x)")
            print("-" * 70)
            
            total_augmented = sum(s['augmented_files'] for s in results.values())
            print(f"✓ Total augmented files: {total_augmented}")
            
        except Exception as e:
            print(f"⚠️  Error in S3 download/augmentation: {e}")
            print("   Using local training data if available")
        
        print("")
    
    def check_retraining_trigger(self, min_new_samples=100):
        """Check if retraining should be triggered based on new data"""
        # Count current samples
        current_samples = {}
        for class_dir in self.augmented_audio_dir.iterdir():
            if class_dir.is_dir():
                audio_files = list(class_dir.glob("*.wav"))
                current_samples[class_dir.name] = len(audio_files)
        
        # Get last training sample count
        if len(self.retraining_log["retraining_history"]) > 0:
            last_training = self.retraining_log["retraining_history"][-1]
            last_samples = last_training.get("sample_counts", {})
            
            # Calculate new samples
            total_new = sum(current_samples.get(cls, 0) - last_samples.get(cls, 0) 
                          for cls in current_samples.keys())
            
            print(f"📊 New samples since last training: {total_new}")
            
            if total_new >= min_new_samples:
                print(f"✓ Retraining trigger activated! ({total_new} new samples >= {min_new_samples} threshold)")
                return True, total_new
            else:
                print(f"⏸️  Not enough new samples for retraining ({total_new} < {min_new_samples})")
                return False, total_new
        else:
            print(f"📝 No previous training found. Initial training recommended.")
            return True, sum(current_samples.values())
    
    def extract_features_batch(self, yamnet_model):
        """Extract YAMNet features from all audio files"""
        X_features = []
        y_labels = []
        class_names = []
        
        print("="*70)
        print("EXTRACTING FEATURES FOR RETRAINING")
        print("="*70)
        
        class_dirs = sorted([d for d in self.augmented_audio_dir.iterdir() if d.is_dir()])
        
        for class_idx, class_dir in enumerate(class_dirs):
            class_name = class_dir.name
            class_names.append(class_name)
            
            audio_files = list(class_dir.glob("*.wav"))
            print(f"[{class_idx + 1}/{len(class_dirs)}] {class_name}: {len(audio_files)} files")
            
            for audio_file in tqdm(audio_files, desc=f"  Processing"):
                try:
                    # Load audio at 16kHz
                    audio, sr = librosa.load(audio_file, sr=SAMPLE_RATE, duration=4)
                    audio = audio.astype(np.float32)
                    
                    # Extract YAMNet embeddings
                    scores, embeddings, spectrogram = yamnet_model(audio)
                    embedding_mean = np.mean(embeddings.numpy(), axis=0)
                    
                    X_features.append(embedding_mean)
                    y_labels.append(class_idx)
                except Exception as e:
                    print(f"    ⚠️  Error: {audio_file.name}: {e}")
        
        X_features = np.array(X_features)
        y_labels = np.array(y_labels)
        
        print(f"\n✓ Feature extraction complete!")
        print(f"  Total samples: {len(X_features):,}")
        print(f"  Feature shape: {X_features.shape}")
        print("="*70)
        
        return X_features, y_labels, class_names
    
    def build_model(self, input_dim=1024, num_classes=4):
        """Build YAMNet classifier architecture"""
        model = Sequential([
            Dense(512, activation='relu', input_shape=(input_dim,)),
            BatchNormalization(),
            Dropout(0.5),
            
            Dense(256, activation='relu'),
            BatchNormalization(),
            Dropout(0.4),
            
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def retrain_model(self, yamnet_model, epochs=100, batch_size=64):
        """Complete retraining pipeline"""
        print("\n" + "="*70)
        print("🔄 STARTING MODEL RETRAINING PIPELINE")
        print("="*70)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Step 1: Extract features
        X_features, y_labels, class_names = self.extract_features_batch(yamnet_model)
        
        # Step 2: Normalize features
        X_normalized = (X_features - X_features.mean()) / X_features.std()
        
        # Step 3: Convert labels to categorical
        y_categorical = to_categorical(y_labels, num_classes=len(class_names))
        
        # Step 4: Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X_normalized, y_categorical, test_size=0.15, random_state=42, stratify=y_labels
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=42
        )
        
        print(f"\n📊 Data Split:")
        print(f"  Training:   {len(X_train):,} samples")
        print(f"  Validation: {len(X_val):,} samples")
        print(f"  Test:       {len(X_test):,} samples")
        
        # Step 5: Build model
        model = self.build_model(input_dim=X_train.shape[1], num_classes=len(class_names))
        
        # Step 6: Setup callbacks
        model_checkpoint_path = self.models_dir / "yamnet_classifier_v2.keras"
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-7, verbose=1),
            ModelCheckpoint(filepath=str(model_checkpoint_path), monitor='val_accuracy', 
                          save_best_only=True, verbose=1)
        ]
        
        # Step 7: Train model
        print(f"\n🚀 Training model...")
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Step 8: Evaluate model
        test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
        
        print(f"\n✓ Training complete!")
        print(f"  Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
        print(f"  Test Loss: {test_loss:.4f}")
        
        # Step 9: Calculate detailed metrics
        y_pred = model.predict(X_test)
        y_pred_classes = np.argmax(y_pred, axis=1)
        y_test_classes = np.argmax(y_test, axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test_classes, y_pred_classes, average=None
        )
        
        # Step 10: Save artifacts
        sample_counts = {}
        for class_dir in self.augmented_audio_dir.iterdir():
            if class_dir.is_dir():
                sample_counts[class_dir.name] = len(list(class_dir.glob("*.wav")))
        
        # Save class names
        with open(self.models_dir / "class_names.json", 'w') as f:
            json.dump(class_names, f, indent=2)
        
        # Save model metadata
        metadata = {
            "model_name": "YAMNet Wildlife Classifier",
            "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_accuracy": float(test_accuracy),
            "test_loss": float(test_loss),
            "num_classes": len(class_names),
            "classes": class_names,
            "sample_counts": sample_counts
        }
        
        with open(self.models_dir / "model_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save performance metrics
        performance = {
            "test_accuracy": float(test_accuracy),
            "test_loss": float(test_loss),
            "per_class_metrics": {}
        }
        
        for idx, class_name in enumerate(class_names):
            performance["per_class_metrics"][class_name] = {
                "precision": float(precision[idx]),
                "recall": float(recall[idx]),
                "f1_score": float(f1[idx])
            }
        
        with open(self.models_dir / "performance_metrics.json", 'w') as f:
            json.dump(performance, f, indent=2)
        
        # Save training history
        with open(self.models_dir / "training_history.pkl", 'wb') as f:
            pickle.dump(history.history, f)
        
        # Step 11: Update retraining log
        retraining_record = {
            "timestamp": timestamp,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_path": str(model_checkpoint_path),
            "test_accuracy": float(test_accuracy),
            "test_loss": float(test_loss),
            "num_classes": len(class_names),
            "classes": class_names,
            "sample_counts": sample_counts,
            "total_samples": len(X_features),
            "epochs_trained": len(history.history['loss']),
            "metrics": {
                "precision": precision.tolist(),
                "recall": recall.tolist(),
                "f1_score": f1.tolist()
            }
        }
        
        self.retraining_log["retraining_history"].append(retraining_record)
        
        with open(self.retraining_log_path, 'w') as f:
            json.dump(self.retraining_log, f, indent=2)
        
        print(f"\n✓ All artifacts saved to {self.models_dir}")
        print(f"  - Model: yamnet_classifier_v2.keras")
        print(f"  - Metadata: model_metadata.json")
        print(f"  - Metrics: performance_metrics.json")
        print(f"  - History: training_history.pkl")
        print(f"  - Retraining log: retraining_log.json")
        print("="*70)
        
        return model, {
            "test_accuracy": test_accuracy,
            "test_loss": test_loss,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "class_names": class_names
        }


def main():
    """Main retraining function"""
    print("="*70)
    print("🦜 EcoSight Wildlife Monitoring - Model Retraining")
    print("="*70)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Audio Directory: {AUGMENTED_AUDIO_DIR}")
    print(f"Models Directory: {MODELS_DIR}")
    print("="*70)
    
    # Initialize pipeline
    pipeline = ModelRetrainingPipeline(
        models_dir=MODELS_DIR,
        augmented_audio_dir=AUGMENTED_AUDIO_DIR
    )
    
    # Check if retraining should be triggered
    should_retrain, new_samples = pipeline.check_retraining_trigger(min_new_samples=MIN_NEW_SAMPLES)
    
    if not should_retrain:
        print("\n⏸️  Retraining skipped. Not enough new data.")
        print(f"   Current new samples: {new_samples}")
        print(f"   Required: {MIN_NEW_SAMPLES}")
        return
    
    # Load YAMNet model
    print("\n📥 Loading YAMNet pretrained model...")
    yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
    print("✓ YAMNet model loaded!")
    
    # Run retraining
    model, metrics = pipeline.retrain_model(
        yamnet_model=yamnet_model,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )
    
    print("\n" + "="*70)
    print("✅ RETRAINING COMPLETE!")
    print("="*70)
    print(f"Final Test Accuracy: {metrics['test_accuracy']:.4f} ({metrics['test_accuracy']*100:.2f}%)")
    print(f"Classes: {', '.join(metrics['class_names'])}")
    print("="*70)
    
    # Print per-class metrics
    print("\n📊 Per-Class Performance:")
    print("-"*70)
    for idx, class_name in enumerate(metrics['class_names']):
        print(f"{class_name:15s} - Precision: {metrics['precision'][idx]:.4f}, "
              f"Recall: {metrics['recall'][idx]:.4f}, F1: {metrics['f1_score'][idx]:.4f}")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Retraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during retraining: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
