"""
Streamlit UI Dashboard for Wildlife Sound Classification
Author: EcoSight Team
Date: 2025-11-17

Features:
- Model uptime monitoring
- Data visualizations
- Train/retrain functionality
- File upload for predictions
- Performance metrics display
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import time
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="EcoSight Wildlife Monitoring",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - Use environment variable or default to localhost
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2E7D32;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_model_status():
    """Fetch model status from API"""
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
        return None


def get_metrics():
    """Fetch performance metrics from API"""
    try:
        response = requests.get(f"{API_URL}/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def get_training_history():
    """Fetch training history including learning curves"""
    try:
        response = requests.get(f"{API_URL}/training-history", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def predict_audio(file):
    """Send audio file to API for prediction"""
    try:
        files = {"file": file}
        response = requests.post(f"{API_URL}/predict", files=files, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API returned status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def upload_training_data(file, class_name):
    """Upload new training data to API"""
    try:
        files = {"file": file}
        data = {"class_name": class_name}
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            data=data,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload failed with status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def trigger_retraining(reason="Manual trigger"):
    """Trigger model retraining via API"""
    try:
        data = {"trigger_reason": reason}
        response = requests.post(
            f"{API_URL}/retrain",
            json=data,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Retraining failed with status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/parrot.png", width=100)
    st.title("🦜 EcoSight")
    st.markdown("**Wildlife Sound Monitoring**")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🎯 Predictions", "📊 Analytics", "🔄 Training", "⚙️ Settings"]
    )
    
    st.markdown("---")
    st.markdown("### 📡 System Status")
    
    # Fetch and display status
    status = get_model_status()
    if status:
        if status.get("status") == "operational":
            st.success("✅ System Online")
        else:
            st.error("❌ System Offline")
        
        st.metric("Uptime", status.get("uptime", "N/A"))
        st.metric("Total Predictions", status.get("total_predictions", 0))
    else:
        st.error("❌ Cannot connect to API")
        st.info("Please ensure the API server is running at " + API_URL)


# ============================================================================
# MAIN CONTENT
# ============================================================================

# Dashboard Page
if page == "🏠 Dashboard":
    st.markdown('<div class="main-header">🦜 EcoSight Wildlife Monitoring Dashboard</div>', 
                unsafe_allow_html=True)
    
    status = get_model_status()
    
    if status:
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🎯 Model Status",
                value="Operational" if status.get("model_loaded") else "Offline",
                delta="Active" if status.get("model_loaded") else "Inactive"
            )
        
        with col2:
            st.metric(
                label="⏱️ Uptime",
                value=status.get("uptime", "N/A")
            )
        
        with col3:
            st.metric(
                label="📈 Total Predictions",
                value=f"{status.get('total_predictions', 0):,}"
            )
        
        with col4:
            st.metric(
                label="🎓 Accuracy",
                value=f"{status.get('test_accuracy', 0)*100:.2f}%"
            )
        
        st.markdown("---")
        
        # Model Information
        st.subheader("📋 Model Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Model Name:** {status.get('model_name', 'N/A')}")
            st.markdown(f"**Training Date:** {status.get('training_date', 'N/A')}")
            st.markdown(f"**Number of Classes:** {status.get('num_classes', 0)}")
        
        with col2:
            st.markdown("**Recognized Classes:**")
            classes = status.get('classes', [])
            for cls in classes:
                st.markdown(f"- {cls}")
        
        st.markdown("---")
        
        # Performance Metrics
        metrics = get_metrics()
        if metrics:
            st.subheader("📊 Performance Metrics")
            
            per_class_metrics = metrics.get("per_class_metrics", {})
            
            if per_class_metrics:
                # Create dataframe for metrics
                metrics_data = []
                for class_name, class_metrics in per_class_metrics.items():
                    metrics_data.append({
                        "Class": class_name,
                        "Precision": class_metrics.get("precision", 0),
                        "Recall": class_metrics.get("recall", 0),
                        "F1-Score": class_metrics.get("f1_score", 0),
                        "Support": class_metrics.get("support", 0)
                    })
                
                df_metrics = pd.DataFrame(metrics_data)
                
                # Display metrics table
                st.dataframe(
                    df_metrics.style.format({
                        "Precision": "{:.4f}",
                        "Recall": "{:.4f}",
                        "F1-Score": "{:.4f}"
                    }),
                    use_container_width=True
                )
                
                # Visualize metrics
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Precision',
                    x=df_metrics['Class'],
                    y=df_metrics['Precision'],
                    marker_color='lightblue'
                ))
                
                fig.add_trace(go.Bar(
                    name='Recall',
                    x=df_metrics['Class'],
                    y=df_metrics['Recall'],
                    marker_color='lightgreen'
                ))
                
                fig.add_trace(go.Bar(
                    name='F1-Score',
                    x=df_metrics['Class'],
                    y=df_metrics['F1-Score'],
                    marker_color='lightcoral'
                ))
                
                fig.update_layout(
                    barmode='group',
                    title='Performance Metrics by Class',
                    xaxis_title='Class',
                    yaxis_title='Score',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ Cannot fetch model status. Please ensure the API is running.")
    
    # Learning Curves Section (if retraining has occurred)
    st.markdown("---")
    st.subheader("📈 Training History & Learning Curves")
    
    training_history = get_training_history()
    
    if training_history and training_history.get("has_history"):
        history = training_history.get("training_history", {})
        retraining_log = training_history.get("retraining_log", {})
        
        # Display retraining sessions summary
        if retraining_log and "retraining_history" in retraining_log:
            sessions = retraining_log["retraining_history"]
            
            if sessions:
                st.markdown(f"**Total Retraining Sessions:** {len(sessions)}")
                
                # Show latest session info
                latest = sessions[-1]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Latest Training Date", latest.get("datetime", "N/A"))
                with col2:
                    st.metric("Epochs Trained", latest.get("epochs_trained", "N/A"))
                with col3:
                    st.metric("Total Samples", f"{latest.get('total_samples', 0):,}")
        
        # Plot Learning Curves
        if history and "epochs" in history:
            tab1, tab2 = st.tabs(["📉 Loss Curves", "📈 Accuracy Curves"])
            
            with tab1:
                # Loss curves
                fig_loss = go.Figure()
                
                if "loss" in history and history["loss"]:
                    fig_loss.add_trace(go.Scatter(
                        x=history["epochs"],
                        y=history["loss"],
                        mode='lines+markers',
                        name='Training Loss',
                        line=dict(color='#FF6B6B', width=3),
                        marker=dict(size=6)
                    ))
                
                if "val_loss" in history and history["val_loss"]:
                    fig_loss.add_trace(go.Scatter(
                        x=history["epochs"],
                        y=history["val_loss"],
                        mode='lines+markers',
                        name='Validation Loss',
                        line=dict(color='#4ECDC4', width=3),
                        marker=dict(size=6)
                    ))
                
                fig_loss.update_layout(
                    title='Model Loss Over Epochs',
                    xaxis_title='Epoch',
                    yaxis_title='Loss',
                    height=450,
                    hovermode='x unified',
                    template='plotly_white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_loss, use_container_width=True)
                
                # Loss statistics
                if "loss" in history and "val_loss" in history:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Initial Train Loss", f"{history['loss'][0]:.4f}")
                    with col2:
                        st.metric("Final Train Loss", f"{history['loss'][-1]:.4f}")
                    with col3:
                        st.metric("Initial Val Loss", f"{history['val_loss'][0]:.4f}")
                    with col4:
                        st.metric("Final Val Loss", f"{history['val_loss'][-1]:.4f}")
            
            with tab2:
                # Accuracy curves
                fig_acc = go.Figure()
                
                if "accuracy" in history and history["accuracy"]:
                    fig_acc.add_trace(go.Scatter(
                        x=history["epochs"],
                        y=history["accuracy"],
                        mode='lines+markers',
                        name='Training Accuracy',
                        line=dict(color='#95E1D3', width=3),
                        marker=dict(size=6)
                    ))
                
                if "val_accuracy" in history and history["val_accuracy"]:
                    fig_acc.add_trace(go.Scatter(
                        x=history["epochs"],
                        y=history["val_accuracy"],
                        mode='lines+markers',
                        name='Validation Accuracy',
                        line=dict(color='#F38181', width=3),
                        marker=dict(size=6)
                    ))
                
                fig_acc.update_layout(
                    title='Model Accuracy Over Epochs',
                    xaxis_title='Epoch',
                    yaxis_title='Accuracy',
                    height=450,
                    hovermode='x unified',
                    template='plotly_white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_acc, use_container_width=True)
                
                # Accuracy statistics
                if "accuracy" in history and "val_accuracy" in history:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Initial Train Acc", f"{history['accuracy'][0]*100:.2f}%")
                    with col2:
                        st.metric("Final Train Acc", f"{history['accuracy'][-1]*100:.2f}%")
                    with col3:
                        st.metric("Initial Val Acc", f"{history['val_accuracy'][0]*100:.2f}%")
                    with col4:
                        st.metric("Final Val Acc", f"{history['val_accuracy'][-1]*100:.2f}%")
        
        # Show retraining history table
        if retraining_log and "retraining_history" in retraining_log:
            sessions = retraining_log["retraining_history"]
            
            if sessions:
                st.markdown("---")
                st.subheader("🔄 Retraining Sessions History")
                
                session_data = []
                for idx, session in enumerate(sessions, 1):
                    session_data.append({
                        "Session": idx,
                        "Date": session.get("datetime", "N/A"),
                        "Accuracy": f"{session.get('test_accuracy', 0)*100:.2f}%",
                        "Loss": f"{session.get('test_loss', 0):.4f}",
                        "Samples": session.get('total_samples', 0),
                        "Epochs": session.get('epochs_trained', 0),
                        "Classes": session.get('num_classes', 0)
                    })
                
                df_sessions = pd.DataFrame(session_data)
                st.dataframe(df_sessions, use_container_width=True)
                
                # Plot accuracy trend across retraining sessions
                if len(sessions) > 1:
                    fig_trend = go.Figure()
                    
                    fig_trend.add_trace(go.Scatter(
                        x=[s.get("datetime", f"Session {i}") for i, s in enumerate(sessions, 1)],
                        y=[s.get("test_accuracy", 0) * 100 for s in sessions],
                        mode='lines+markers',
                        name='Test Accuracy',
                        line=dict(color='#2E7D32', width=3),
                        marker=dict(size=10)
                    ))
                    
                    fig_trend.update_layout(
                        title='Model Performance Across Retraining Sessions',
                        xaxis_title='Retraining Session',
                        yaxis_title='Test Accuracy (%)',
                        height=350,
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("📝 No retraining history available yet. Training history will appear after the first retraining session.")


# Predictions Page
elif page == "🎯 Predictions":
    st.markdown('<div class="main-header">🎯 Audio Classification</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    Upload an audio file to classify wildlife sounds. The model will identify:
    - 🔫 Gun shots (anti-poaching alerts)
    - 🐕 Dogs
    - 🚗 Engine Idling
    - Humane voices
    """)
    
    uploaded_file = st.file_uploader(
        "Choose an audio files",
        type=["wav", "mp3", "ogg", "flac"],
        help="Supported formats: WAV, MP3, OGG, FLAC"
    )
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔍 Classify Audio", type="primary"):
                with st.spinner("Analyzing audio..."):
                    result = predict_audio(uploaded_file)
                    
                    if "error" in result:
                        st.error(f"❌ Prediction failed: {result['error']}")
                    else:
                        st.success("✅ Classification Complete!")
                        
                        # Display results
                        st.markdown("---")
                        st.subheader("🎯 Prediction Results")
                        
                        # Main prediction
                        predicted_class = result.get("predicted_class", "Unknown")
                        confidence = result.get("confidence", 0)
                        
                        st.markdown(f"### Predicted Class: **{predicted_class}**")
                        st.progress(confidence)
                        st.markdown(f"**Confidence:** {confidence*100:.2f}%")
                        
                        # All probabilities
                        st.markdown("---")
                        st.subheader("📊 All Class Probabilities")
                        
                        probs = result.get("all_probabilities", {})
                        prob_df = pd.DataFrame([
                            {"Class": k, "Probability": v}
                            for k, v in sorted(probs.items(), key=lambda x: x[1], reverse=True)
                        ])
                        
                        fig = px.bar(
                            prob_df,
                            x="Probability",
                            y="Class",
                            orientation='h',
                            color="Probability",
                            color_continuous_scale="Greens"
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Processing info
                        st.markdown("---")
                        st.info(f"⏱️ Processing time: {result.get('processing_time', 0):.3f} seconds")
                        st.caption(f"Timestamp: {result.get('timestamp', 'N/A')}")


# Analytics Page
elif page == "📊 Analytics":
    st.markdown('<div class="main-header">📊 Model Analytics</div>', 
                unsafe_allow_html=True)
    
    metrics = get_metrics()
    status = get_model_status()
    
    if metrics and status:
        # Confusion Matrix
        st.subheader("🔍 Confusion Matrix")
        
        cm = metrics.get("confusion_matrix", [])
        classes = status.get("classes", [])
        
        if cm and classes:
            cm_df = pd.DataFrame(cm, columns=classes, index=classes)
            
            fig = px.imshow(
                cm_df,
                labels=dict(x="Predicted", y="True", color="Count"),
                x=classes,
                y=classes,
                color_continuous_scale="Greens",
                text_auto=True
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Per-class performance
        st.subheader("📈 Per-Class Performance Analysis")
        
        per_class = metrics.get("per_class_metrics", {})
        
        if per_class:
            for class_name, class_metrics in per_class.items():
                with st.expander(f"📊 {class_name.upper()}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Precision", f"{class_metrics.get('precision', 0):.4f}")
                    with col2:
                        st.metric("Recall", f"{class_metrics.get('recall', 0):.4f}")
                    with col3:
                        st.metric("F1-Score", f"{class_metrics.get('f1_score', 0):.4f}")
                    with col4:
                        st.metric("Support", class_metrics.get('support', 0))
                    
                    # Create gauge chart for F1-score
                    f1_score = class_metrics.get('f1_score', 0)
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=f1_score * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "F1-Score"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "darkgreen"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightcoral"},
                                {'range': [50, 75], 'color': "lightyellow"},
                                {'range': [75, 100], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ Cannot load analytics. Please ensure the API is running.")


# Training Page
elif page == "🔄 Training":
    st.markdown('<div class="main-header">🔄 Model Training & Retraining</div>', 
                unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📤 Upload Training Data", "🔄 Retrain Model"])
    
    with tab1:
        st.subheader("📤 Upload New Training Data")
        st.markdown("Upload new audio samples to expand the training dataset.")
        
        status = get_model_status()
        classes = status.get("classes", []) if status else []
        
        # 1. ENABLE MULTIPLE FILES
        uploaded_training_files = st.file_uploader(
            "Choose audio files for training",
            type=["wav", "mp3", "ogg", "flac"],
            key="training_upload",
            accept_multiple_files=True  # <--- THIS IS THE KEY CHANGE
        )
        
        selected_class = st.selectbox(
            "Select class label",
            options=classes + ["unknown"],
            help="Choose the correct class for these audio files"
        )
        
        # 2. HANDLE THE LIST OF FILES
        if uploaded_training_files:
            file_count = len(uploaded_training_files)
            st.info(f"✅ {file_count} file(s) selected for class: **{selected_class}**")
            
            # Optional: Use an expander to preview files so the UI doesn't get cluttered
            with st.expander("View selected files"):
                for i, file in enumerate(uploaded_training_files):
                    st.text(f"{i+1}. {file.name}")
                    # Only show audio player if fewer than 5 files to save memory/space
                    if file_count <= 5:
                        st.audio(file, format='audio/wav')

            if st.button("📤 Upload All to Training Dataset", type="primary"):
                
                # Create containers for progress and results
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                errors = []

                # 3. LOOP THROUGH FILES AND UPLOAD
                for idx, file_obj in enumerate(uploaded_training_files):
                    # Update status
                    status_text.text(f"Uploading {file_obj.name} ({idx + 1}/{file_count})...")
                    
                    # Call your existing backend function
                    # Note: We assume upload_training_data handles the pointer reset (seek(0))
                    result = upload_training_data(file_obj, selected_class)
                    
                    if "error" in result:
                        errors.append(f"{file_obj.name}: {result['error']}")
                    else:
                        success_count += 1
                    
                    # Update progress bar
                    progress_bar.progress((idx + 1) / file_count)

                # Final Summary
                status_text.empty()
                progress_bar.empty()

                if success_count == file_count:
                    st.success(f"✅ All {file_count} files uploaded successfully!")
                else:
                    st.warning(f"⚠️ Processed with issues. Success: {success_count}, Failed: {len(errors)}")
                    if errors:
                        with st.expander("Show Errors"):
                            for err in errors:
                                st.error(err)
    
    with tab2:
        st.subheader("🔄 Retrain Model")
        st.markdown("""
        Trigger model retraining with the latest data. This process will:
        1. Extract features from all training data
        2. Train a new model
        3. Evaluate performance
        4. Update the production model if performance improves
        """)
        
        st.warning("⚠️ Retraining may take several minutes. The API will continue serving predictions during this time.")
        
        reason = st.text_input(
            "Retraining reason (optional)",
            value="Manual trigger from UI",
            help="Describe why you're triggering retraining"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🚀 Start Retraining", type="primary"):
                with st.spinner("Triggering retraining..."):
                    result = trigger_retraining(reason)
                    
                    if "error" in result:
                        st.error(f"❌ Retraining failed: {result['error']}")
                    else:
                        if result.get("success"):
                            st.success(f"✅ {result.get('message')}")
                            st.info(f"Status: {result.get('status')}")
                        else:
                            st.warning(result.get("message"))


# Settings Page
elif page == "⚙️ Settings":
    st.markdown('<div class="main-header">⚙️ System Settings</div>', 
                unsafe_allow_html=True)
    
    st.subheader("🔧 API Configuration")
    
    api_url = st.text_input("API URL", value=API_URL)
    
    if st.button("Test Connection"):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API connection successful!")
                st.json(response.json())
            else:
                st.error(f"❌ API returned status code {response.status_code}")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
    
    st.markdown("---")
    
    st.subheader("📊 System Information")
    
    status = get_model_status()
    if status:
        st.json(status)
    
    st.markdown("---")
    
    st.subheader("ℹ️ About")
    st.markdown("""
    **EcoSight Wildlife Monitoring System**
    
    Version: 1.0.0  
    Author: EcoSight Team  
    Date: 2025-11-17
    
    This system uses deep learning to classify wildlife sounds for anti-poaching efforts.
    
    **Features:**
    - Real-time audio classification
    - Automated model retraining
    - Performance monitoring
    - Training data management
    
    **Technology Stack:**
    - YAMNet (TensorFlow Hub)
    - FastAPI
    - Streamlit
    - Docker
    """)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "EcoSight Wildlife Monitoring System © 2025 | Powered by TensorFlow & Streamlit"
    "</div>",
    unsafe_allow_html=True
)
