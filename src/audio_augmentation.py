"""
Audio Augmentation Module for EcoSight
======================================
This module provides audio augmentation functions to create multiple
variants of audio files for training data expansion.

Augmentation techniques:
- Time stretching (speed changes)
- Pitch shifting (tone changes)
- Noise addition (background noise)
- Time shifting (temporal offset)
- Volume adjustment (amplitude changes)

Based on the augmentation pipeline from acoustic_togetherso_(1).ipynb
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


def time_stretch(audio: np.ndarray, rate: float = 1.0) -> np.ndarray:
    """
    Time stretch audio by a given rate.
    
    Args:
        audio: Audio data as numpy array
        rate: Stretch rate (>1.0 = faster/shorter, <1.0 = slower/longer)
    
    Returns:
        Time-stretched audio
    """
    return librosa.effects.time_stretch(audio, rate=rate)


def pitch_shift(audio: np.ndarray, sr: int, n_steps: int = 0) -> np.ndarray:
    """
    Shift pitch by n_steps semitones.
    
    Args:
        audio: Audio data as numpy array
        sr: Sample rate
        n_steps: Number of semitones (>0 = higher pitch, <0 = lower pitch)
    
    Returns:
        Pitch-shifted audio
    """
    return librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)


def add_noise(audio: np.ndarray, noise_factor: float = 0.005) -> np.ndarray:
    """
    Add random Gaussian noise to audio.
    
    Args:
        audio: Audio data as numpy array
        noise_factor: Noise intensity (0.001-0.01 recommended)
    
    Returns:
        Audio with added noise
    """
    noise = np.random.randn(len(audio))
    augmented = audio + noise_factor * noise
    return augmented


def time_shift(audio: np.ndarray, shift_max: float = 0.2) -> np.ndarray:
    """
    Shift audio in time domain.
    
    Args:
        audio: Audio data as numpy array
        shift_max: Maximum shift as fraction of total length
    
    Returns:
        Time-shifted audio
    """
    shift = int(np.random.uniform(-shift_max, shift_max) * len(audio))
    return np.roll(audio, shift)


def change_volume(audio: np.ndarray, factor: float = 1.0) -> np.ndarray:
    """
    Change audio volume.
    
    Args:
        audio: Audio data as numpy array
        factor: Volume factor (>1.0 = louder, <1.0 = quieter)
    
    Returns:
        Volume-adjusted audio
    """
    return audio * factor


def random_speed_change(audio: np.ndarray, speed_range: Tuple[float, float] = (0.9, 1.1)) -> np.ndarray:
    """
    Randomly change speed within a range.
    
    Args:
        audio: Audio data as numpy array
        speed_range: Tuple of (min_speed, max_speed)
    
    Returns:
        Speed-adjusted audio
    """
    rate = np.random.uniform(speed_range[0], speed_range[1])
    return time_stretch(audio, rate)


def augment_audio_file(
    audio_path: Path,
    output_dir: Path,
    sr: int = 22050,
    augmentations_per_file: int = 5
) -> List[Path]:
    """
    Apply multiple augmentations to a single audio file.
    
    This function creates multiple augmented versions of an audio file
    using various augmentation techniques. It's designed to match the
    augmentation pipeline from the Jupyter notebook.
    
    Args:
        audio_path: Path to original audio file (.wav or .mp3)
        output_dir: Directory to save augmented files
        sr: Sample rate for loading audio (default: 22050)
        augmentations_per_file: Number of augmented versions to create (default: 5)
    
    Returns:
        List of paths to saved augmented files
    """
    try:
        # Load audio (librosa handles both .wav and .mp3)
        audio, sr = librosa.load(str(audio_path), sr=sr)
        
        saved_files = []
        base_name = audio_path.stem
        
        # Save original (copy to augmented folder as .wav)
        original_path = output_dir / f"{base_name}_original.wav"
        sf.write(str(original_path), audio, sr)
        saved_files.append(original_path)
        
        # Define augmentation strategies
        augmentation_configs: List[Tuple[str, Callable]] = [
            ('time_stretch_fast', lambda a: time_stretch(a, rate=1.1)),
            ('time_stretch_slow', lambda a: time_stretch(a, rate=0.9)),
            ('pitch_up', lambda a: pitch_shift(a, sr, n_steps=2)),
            ('pitch_down', lambda a: pitch_shift(a, sr, n_steps=-2)),
            ('noise_light', lambda a: add_noise(a, noise_factor=0.002)),
            ('noise_medium', lambda a: add_noise(a, noise_factor=0.005)),
            ('time_shift', lambda a: time_shift(a, shift_max=0.15)),
            ('volume_up', lambda a: change_volume(a, factor=1.2)),
            ('volume_down', lambda a: change_volume(a, factor=0.8)),
            ('combined_1', lambda a: add_noise(time_stretch(a, rate=1.05), noise_factor=0.003)),
            ('combined_2', lambda a: change_volume(pitch_shift(a, sr, n_steps=1), factor=0.9))
        ]
        
        # Randomly select augmentations
        selected_indices = np.random.choice(
            len(augmentation_configs),
            size=min(augmentations_per_file, len(augmentation_configs)),
            replace=False
        )
        
        for idx in selected_indices:
            aug_name, aug_func = augmentation_configs[idx]
            try:
                augmented_audio = aug_func(audio)
                
                # Save augmented audio (always save as .wav)
                aug_path = output_dir / f"{base_name}_{aug_name}.wav"
                sf.write(str(aug_path), augmented_audio, sr)
                saved_files.append(aug_path)
                
            except Exception as e:
                logger.warning(f"Error applying {aug_name} to {audio_path.name}: {e}")
        
        logger.info(f"Augmented {audio_path.name}: {len(saved_files)} files created")
        return saved_files
        
    except Exception as e:
        logger.error(f"Error augmenting {audio_path}: {e}")
        return []


def augment_directory(
    input_dir: Path,
    output_dir: Path,
    sr: int = 22050,
    augmentations_per_file: int = 5
) -> dict:
    """
    Augment all audio files in a directory, preserving class structure.
    
    This function processes all audio files in a directory structure like:
    input_dir/
        class1/
            audio1.wav
            audio2.mp3
        class2/
            audio3.wav
    
    And creates:
    output_dir/
        class1/
            audio1_original.wav
            audio1_pitch_up.wav
            audio1_noise_light.wav
            ...
        class2/
            ...
    
    Args:
        input_dir: Directory containing class subdirectories with audio files
        output_dir: Directory to save augmented files
        sr: Sample rate for loading audio
        augmentations_per_file: Number of augmented versions per file
    
    Returns:
        Dictionary with augmentation statistics per class
    """
    results = {}
    
    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Process each class directory
    for class_dir in sorted(input_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        
        class_name = class_dir.name
        logger.info(f"Processing class: {class_name}")
        
        # Create output class directory
        output_class_dir = output_dir / class_name
        output_class_dir.mkdir(exist_ok=True)
        
        # Get all audio files (both .wav and .mp3)
        audio_files = list(class_dir.glob("*.wav")) + list(class_dir.glob("*.mp3"))
        
        if not audio_files:
            logger.warning(f"No audio files found in {class_dir}")
            continue
        
        original_count = len(audio_files)
        total_created = 0
        
        # Augment each file
        for audio_file in audio_files:
            saved_files = augment_audio_file(
                audio_file,
                output_class_dir,
                sr=sr,
                augmentations_per_file=augmentations_per_file
            )
            total_created += len(saved_files)
        
        results[class_name] = {
            'original_files': original_count,
            'augmented_files': total_created,
            'increase_factor': total_created / original_count if original_count > 0 else 0
        }
        
        logger.info(f"Class {class_name}: {original_count} → {total_created} files ({total_created/original_count:.1f}x)")
    
    return results


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Example: Augment a single file
    # audio_path = Path("path/to/audio.wav")
    # output_dir = Path("path/to/output")
    # output_dir.mkdir(exist_ok=True)
    # augment_audio_file(audio_path, output_dir)
    
    # Example: Augment entire directory structure
    # input_dir = Path("extracted_audio")
    # output_dir = Path("augmented_audio")
    # results = augment_directory(input_dir, output_dir)
    # print("Augmentation results:", results)
    
    print("Audio augmentation module loaded successfully!")
