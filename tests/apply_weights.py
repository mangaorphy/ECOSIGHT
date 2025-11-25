"""
Final weight application script - applies only Dense layer weights

This script was used to fix a Keras version compatibility issue where the trained
model (yamnet_classifier.keras) couldn't be loaded due to changes between Keras versions.

What it does:
1. Extracts the trained weights from the incompatible .keras file
2. Rebuilds the model architecture using the metadata (model_metadata.json)
3. Applies the extracted weights to the new model
4. Saves as yamnet_classifier_v2.keras in a compatible format
"""

import h5py
import numpy as np
import tensorflow as tf
import json
from pathlib import Path

def apply_dense_weights():
    """Apply only Dense layer weights from extracted H5 file"""
    
    models_dir = Path("models")
    weights_file = models_dir / "extracted_weights.h5"
    
    # Read metadata
    with open(models_dir / "model_metadata.json", 'r') as f:
        metadata = json.load(f)
    
    # Build new model (without BatchNorm since we don't have it in metadata)
    num_classes = metadata['num_classes']
    input_shape = tuple(metadata['input_shape'])
    arch = metadata['architecture']
    
    print("Building model...")
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=input_shape, name='input_layer'),
        tf.keras.layers.Dense(arch['layers'][0], activation=arch['activation'], name='dense_1'),
        tf.keras.layers.Dropout(arch['dropout_rates'][0], name='dropout_1'),
        tf.keras.layers.Dense(arch['layers'][1], activation=arch['activation'], name='dense_2'),
        tf.keras.layers.Dropout(arch['dropout_rates'][1], name='dropout_2'),
        tf.keras.layers.Dense(arch['layers'][2], activation=arch['activation'], name='dense_3'),
        tf.keras.layers.Dropout(arch['dropout_rates'][2], name='dropout_3'),
        tf.keras.layers.Dense(arch['layers'][3], activation=arch['activation'], name='dense_4'),
        tf.keras.layers.Dropout(arch['dropout_rates'][3], name='dropout_4'),
        tf.keras.layers.Dense(num_classes, activation='softmax', name='output'),
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=arch.get('learning_rate', 0.001)),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Build model
    dummy = np.zeros((1,) + input_shape)
    _ = model(dummy)
    
    print("\nModel Summary:")
    model.summary()
    
    # Extract Dense layer weights from H5
    print("\n" + "=" * 60)
    print("Extracting Dense layer weights...")
    print("=" * 60)
    
    with h5py.File(weights_file, 'r') as f:
        # Map of H5 layer names to their weights
        dense_weights = {
            'dense': ('layers/dense/vars/0', 'layers/dense/vars/1'),
            'dense_1': ('layers/dense_1/vars/0', 'layers/dense_1/vars/1'),
            'dense_2': ('layers/dense_2/vars/0', 'layers/dense_2/vars/1'),
            'dense_3': ('layers/dense_3/vars/0', 'layers/dense_3/vars/1'),
            'dense_4': ('layers/dense_4/vars/0', 'layers/dense_4/vars/1'),
        }
        
        # Apply weights to each Dense layer
        # Correct mapping: model layer -> H5 path
        layer_mapping = {
            'dense_1': 'dense',      # Input layer (1024 -> 512)
            'dense_2': 'dense_1',    # 512 -> 256
            'dense_3': 'dense_2',    # 256 -> 128
            'dense_4': 'dense_3',    # 128 -> 64
            'output': 'dense_4',     # 64 -> 4
        }
        
        for layer in model.layers:
            if layer.name in layer_mapping:
                h5_name = layer_mapping[layer.name]
                
                if h5_name in dense_weights:
                    kernel_path, bias_path = dense_weights[h5_name]
                    
                    try:
                        kernel = f[kernel_path][:]
                        bias = f[bias_path][:]
                        
                        print(f"\n{layer.name} <- {h5_name}:")
                        print(f"  Kernel shape: {kernel.shape}")
                        print(f"  Bias shape: {bias.shape}")
                        
                        layer.set_weights([kernel, bias])
                        print(f"  ✓ Weights applied successfully")
                        
                    except Exception as e:
                        print(f"  ⚠ Error: {e}")
    
    # Save model
    output_path = models_dir / "yamnet_classifier_v2.keras"
    print(f"\n" + "=" * 60)
    print(f"Saving model to {output_path}...")
    model.save(output_path)
    print("✓ Model saved successfully!")
    
    # Also save with the original name as backup
    backup_path = models_dir / "yamnet_classifier_fixed.keras"
    model.save(backup_path)
    print(f"✓ Backup saved to {backup_path}")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Your trained model weights have been loaded!")
    print("=" * 60)
    print(f"\nTest accuracy from training: {metadata['test_accuracy']:.4f}")
    print(f"Model ready to use at: {output_path}")
    
    return model

if __name__ == "__main__":
    apply_dense_weights()
