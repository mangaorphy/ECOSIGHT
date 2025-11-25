#!/usr/bin/env python3
"""
Script to extract specific audio classes from UrbanSound8K dataset
Extracts gun_shot, engine_idling, and dog_bark audio files
"""

import os
import shutil
import pandas as pd
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent
METADATA_PATH = BASE_DIR / "metadata" / "UrbanSound8K.csv"
AUDIO_SOURCE_DIR = BASE_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "extracted_audio"

# Classes to extract
TARGET_CLASSES = ["gun_shot", "engine_idling", "dog_bark"]

def create_output_directories():
    """Create output directories for each target class"""
    for class_name in TARGET_CLASSES:
        class_dir = OUTPUT_DIR / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {class_dir}")

def extract_audio_files():
    """Extract audio files based on metadata"""
    
    # Read metadata CSV
    print(f"\nReading metadata from: {METADATA_PATH}")
    df = pd.read_csv(METADATA_PATH)
    
    print(f"Total audio files in dataset: {len(df)}")
    
    # Filter for target classes
    df_filtered = df[df['class'].isin(TARGET_CLASSES)]
    
    print(f"\nFound files:")
    for class_name in TARGET_CLASSES:
        count = len(df_filtered[df_filtered['class'] == class_name])
        print(f"  - {class_name}: {count} files")
    
    # Copy files
    print("\nCopying files...")
    copied_count = 0
    skipped_count = 0
    
    for idx, row in df_filtered.iterrows():
        file_name = row['slice_file_name']
        fold = row['fold']
        class_name = row['class']
        
        # Source path (audio files are in fold subfolders)
        source_path = AUDIO_SOURCE_DIR / f"fold{fold}" / file_name
        
        # Destination path
        dest_path = OUTPUT_DIR / class_name / file_name
        
        # Copy file if it exists
        if source_path.exists():
            shutil.copy2(source_path, dest_path)
            copied_count += 1
            
            if copied_count % 100 == 0:
                print(f"  Copied {copied_count} files...")
        else:
            print(f"  ⚠ Warning: File not found - {source_path}")
            skipped_count += 1
    
    print(f"\n✓ Extraction complete!")
    print(f"  Successfully copied: {copied_count} files")
    
    if skipped_count > 0:
        print(f"  Skipped (not found): {skipped_count} files")
    
    # Summary by class
    print(f"\nExtracted files by class:")
    for class_name in TARGET_CLASSES:
        class_dir = OUTPUT_DIR / class_name
        file_count = len(list(class_dir.glob("*.wav")))
        print(f"  - {class_name}: {file_count} files in {class_dir}")

def main():
    print("=" * 60)
    print("UrbanSound8K Audio Extraction Tool")
    print("=" * 60)
    print(f"Extracting classes: {', '.join(TARGET_CLASSES)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Create output directories
    create_output_directories()
    
    # Extract audio files
    extract_audio_files()
    
    print("\n" + "=" * 60)
    print("Extraction complete! ✓")
    print("=" * 60)

if __name__ == "__main__":
    main()
