import streamlit as st
import os
import json
import time
import pandas as pd
import google.generativeai as genai
from pathlib import Path
import numpy as np

def process_audio_file(uploaded_file, prompt, temperature):
    """Process a single audio file and return the evaluation JSON and transcription"""
    try:
        # Create a temporary file
        temp_file_path = f"temp_{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get file path
        file_path = Path(temp_file_path)
        
        print(f"Processing: {file_path}")
        
        # Generate transcription first
        transcription_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": temperature})
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Get transcription with speaker diarization
        transcription_prompt = """
        Transcribe this audio file with speaker diarization. 
        Identify three different speakers: 
        1. Agent (the caller/fundraiser)
        2. Donor (the call receiver)
        3. Supervisor (if present)
        
        Format the transcription as a JSON with the following structure:
        {
            "transcription": [
                {"speaker": "Agent", "text": "speaker text here", "timestamp": "MM:SS-MM:SS"},
                {"speaker": "Donor", "text": "speaker text here", "timestamp": "MM:SS-MM:SS"},
                ...
            ]
        }
        
        Include approximate timestamps for each speaker turn in MM:SS-MM:SS format.
        """
        
        transcription_response = transcription_model.generate_content(
            [transcription_prompt, {"mime_type": "audio/wav", "data": file_content}]
        )
        
        # Parse transcription
        transcription_text = transcription_response.text
        
        # Clean up JSON string
        transcription_json_str = transcription_text.strip()
        if transcription_json_str.startswith("```json"):
            transcription_json_str = transcription_json_str[7:-3] if transcription_json_str.endswith("```") else transcription_json_str[7:]
        elif transcription_json_str.startswith("```"):
            transcription_json_str = transcription_json_str[3:-3] if transcription_json_str.endswith("```") else transcription_json_str[3:]
            
        # Parse transcription JSON
        transcription_result = json.loads(transcription_json_str)
        
        # Generate evaluation with the file and prompt
        evaluation_model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"temperature": temperature})
        
        # Create multipart content with text and audio for evaluation
        evaluation_response = evaluation_model.generate_content(
            [prompt, {"mime_type": "audio/wav", "data": file_content}]
        )
        
        # Save raw response for debugging purposes
        raw_response = evaluation_response.text
        
        # Parse the JSON response
        json_str = raw_response.strip()
        # Remove markdown code block markers if present
        if json_str.startswith("```json"):
            json_str = json_str[7:-3] if json_str.endswith("```") else json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:-3] if json_str.endswith("```") else json_str[3:]
            
        # Parse the JSON
        result = json.loads(json_str)
        
        # Ensure filename is correctly set in the output
        result['audio_file_name'] = uploaded_file.name
        
        # Add transcription to the result
        result['transcription'] = transcription_result.get('transcription', [])
        
        # Clean up temporary file
        os.remove(temp_file_path)
            
        return result, raw_response, transcription_result
    
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        error_msg = str(e)
        print(f"Error processing {uploaded_file.name}: {error_msg}")
        
        return {
            "audio_file_name": uploaded_file.name,
            "error": error_msg
        }, error_msg, {"transcription": []}

def display_evaluation_results(result):
    """Display the evaluation results in Streamlit with highlighted failed criteria"""
    if "error" in result:
        st.error(f"Error processing file: {result['error']}")
        return
    
    # Display summary information
    st.subheader("Evaluation Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Call Length", value=result.get("call_length", "N/A"))
    
    with col2:
        # Show points lost with color based on severity
        points_lost = result["evaluation_summary"]["total_points_lost"]
        st.metric(
            label="Total Points Lost", 
            value=points_lost,
            delta=None
        )
    
    with col3:
        high_penalty = result["evaluation_summary"]["high_penalty_flag"]
        color = "red" if high_penalty else "green"
        status_text = "YES - High Penalty" if high_penalty else "NO - No High Penalty"
        st.markdown(
            f"<div style='background-color:{color}; padding:10px; border-radius:5px;'>"
            f"<h3 style='color:white; text-align:center;'>High Penalty: {status_text}</h3></div>", 
            unsafe_allow_html=True
        )
    
    # Display criteria evaluation with special highlighting for failed criteria
    st.subheader("Criteria Evaluation")
    
    # Sort criteria to show failed ones first
    criteria = result["criteria_evaluation"]
    criteria.sort(key=lambda x: 0 if x['status'].lower() == 'not met' else 1)
    
    # Display criteria with appropriate styling
    for item in criteria:
        status = item['status'].lower()
        is_failed = status == 'not met'
        
        # Define colors based on status
        if is_failed:
            bg_color = "#FFEBEE"  # Light red background
            border_color = "#F44336"  # Red border
            icon = "❌"
        else:
            bg_color = "#E8F5E9"  # Light green background
            border_color = "#4CAF50"  # Green border
            icon = "✅"
        
        # Create styled expander header
        expander_label = f"{icon} {item['criterion']} - {item['status']}"
        
        with st.expander(expander_label):
            # Styled content container
            st.markdown(
                f"""
                <div style="background-color:{bg_color}; border-left:4px solid {border_color}; padding:15px; border-radius:4px; margin-bottom:10px;">
                    <p><strong>Evidence:</strong> {item['evidence']}</p>
                    <p><strong>Confidence:</strong> {item['confidence']}</p>
                    {f"<p><strong>Notes:</strong> {item['notes']}</p>" if item.get("notes") else ""}
                </div>
                """, 
                unsafe_allow_html=True
            )

def display_transcription(transcription):
    """Display the transcription with speaker separation"""
    st.subheader("Call Transcription")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["All Speakers", "By Speaker"])
    
    with tab1:
        # Display all speakers in sequence
        for entry in transcription:
            speaker = entry.get("speaker", "Unknown")
            text = entry.get("text", "")
            timestamp = entry.get("timestamp", "")
            
            # Color code by speaker
            if speaker.lower() == "agent":
                color = "#E3F2FD"  # Light blue for agent
                border = "#2196F3"
            elif speaker.lower() == "donor":
                color = "#FFF3E0"  # Light orange for donor
                border = "#FF9800"
            elif speaker.lower() == "supervisor":
                color = "#E8F5E9"  # Light green for supervisor
                border = "#4CAF50"
            else:
                color = "#F5F5F5"  # Light grey for unknown
                border = "#9E9E9E"
            
            st.markdown(
                f"""
                <div style="background-color:{color}; border-left:4px solid {border}; padding:10px; border-radius:4px; margin-bottom:8px;">
                    <p><strong>{speaker}</strong> <span style="color:#616161; font-size:0.8em;">({timestamp})</span></p>
                    <p>{text}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    with tab2:
        # Group by speaker
        speakers = {}
        for entry in transcription:
            speaker = entry.get("speaker", "Unknown")
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append(entry)
        
        # Create columns for each speaker
        speaker_tabs = st.tabs(list(speakers.keys()))
        
        for i, (speaker, entries) in enumerate(speakers.items()):
            with speaker_tabs[i]:
                for entry in entries:
                    text = entry.get("text", "")
                    timestamp = entry.get("timestamp", "")
                    
                    st.markdown(
                        f"""
                        <div style="padding:10px; border-bottom:1px solid #e0e0e0; margin-bottom:5px;">
                            <p><span style="color:#616161; font-size:0.8em;">({timestamp})</span></p>
                            <p>{text}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

# Streamlit App
st.set_page_config(page_title="Audio Evaluation Tool", layout="wide")

st.title("Call Quality Evaluation Tool With Dustin V2")
st.write("Upload a WAV file to analyze call quality metrics and get transcription")

# API Key input (secure)
api_key = st.text_input("Enter your Google AI API Key", type="password")

# Two columns for settings
col1, col2 = st.columns(2)

with col1:
    # Temperature parameter
    temperature = st.slider(
        "Gemini AI Temperature", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.2,
        step=0.1,
        help="Controls randomness in results. Lower values make output more focused, higher values make it more creative."
    )

# Prompt input with default
default_prompt = """Analyze this call recording and evaluate it against the following criteria. Provide your results in JSON format:

[ADD YOUR EVALUATION PROMPT HERE]
"""
prompt = st.text_area("Evaluation Prompt", default_prompt, height=200)

# File uploader
uploaded_file = st.file_uploader("Upload WAV File", type=["wav"])

if uploaded_file is not None and api_key and prompt:
    # Set the API key
    genai.configure(api_key=api_key)
    
    with st.spinner("Processing audio file..."):
        result, raw_response, transcription_result = process_audio_file(uploaded_file, prompt, temperature)
    
    # Create tabs for Evaluation and Transcription
    tab1, tab2 = st.tabs(["Evaluation Results", "Transcription"])
    
    with tab1:
        # Display the evaluation results
        display_evaluation_results(result)
        
        # Option to download the JSON result
        st.download_button(
            label="Download Evaluation JSON",
            data=json.dumps(result, indent=2),
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_evaluation.json",
            mime="application/json"
        )
        
        # Show raw response in expander
        with st.expander("View Raw Evaluation API Response"):
            st.text(raw_response)


                # Add a table view of criteria
        # Add a table view of criteria
        with st.expander("View Criteria Table"):
            # Create a DataFrame from the criteria evaluation data
            criteria_data = []
            calculated_points_lost = 0
            
            for item in result["criteria_evaluation"]:
                # Get weight, defaulting to 0 if not present
                weight = item.get('weight', 0)
                try:
                    # Try to convert to float if it's a number
                    weight = float(weight)
                except (ValueError, TypeError):
                    weight = 0
                    
                # Add to points lost if status is "Not Met"
                if item['status'].lower() == 'not met':
                    calculated_points_lost += weight
                    
                criteria_data.append({
                    "Criterion": item['criterion'],
                    "Weight": weight,
                    "Status": item['status'],
                    "Evidence": item['evidence'],
                    "Notes": item.get('notes', '')  # In case notes is not present
                })
            
            # Create DataFrame from the collected data
            criteria_df = pd.DataFrame(criteria_data)
            
            # Display the table
            st.dataframe(criteria_df, use_container_width=True)
            calculated_points_lost = np.abs(calculated_points_lost)
            # Display total points lost (calculated from weights)
            st.markdown(f"**Total Points Lost:** {calculated_points_lost}")
            
            # Determine high penalty status based on total points lost
            # You can adjust the threshold as needed
            high_penalty_threshold = 20  # Example threshold
            high_penalty = calculated_points_lost >= high_penalty_threshold
            
            # Display high penalty status with color
            color = "red" if high_penalty else "green"
            status_text = "YES - High Penalty" if high_penalty else "NO - No High Penalty"
            
            st.markdown(
                f"<div style='background-color:{color}; padding:5px; border-radius:5px; display:inline-block;'>"
                f"<p style='color:white; margin:0; padding:5px;'><strong>High Penalty: {status_text}</strong></p></div>", 
                unsafe_allow_html=True
            )
            
            # Convert DataFrame to CSV for download
            csv = criteria_df.to_csv(index=False)
            
            # Download button for CSV
            st.download_button(
                label="Download Criteria as CSV",
                data=csv,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_criteria.csv",
                mime="text/csv"
            )
    
    with tab2:
        # Display the transcription
        display_transcription(result.get('transcription', []))
        
        # Option to download transcription JSON
        transcription_json = {"transcription": result.get('transcription', [])}
        st.download_button(
            label="Download Transcription JSON",
            data=json.dumps(transcription_json, indent=2),
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_transcription.json",
            mime="application/json"
        )
        
elif uploaded_file is not None:
    st.warning("Please enter your Google AI API key and evaluation prompt to process the file.")
