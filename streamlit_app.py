import streamlit as st
import os
import json
import time
import pandas as pd
import google.generativeai as genai
from pathlib import Path

def process_audio_file(uploaded_file, prompt):
    """Process a single audio file and return the evaluation JSON"""
    try:
        # Create a temporary file
        temp_file_path = f"temp_{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Get file path
        file_path = Path(temp_file_path)
        
        print(f"Processing: {file_path}")
        
        # Generate content with the file and prompt
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Create multipart content with text and audio
        response = model.generate_content(
            [prompt, {"mime_type": "audio/wav", "data": file_content}]
        )
        
        # Save raw response for debugging purposes
        raw_response = response.text
        
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
        
        # Clean up temporary file
        os.remove(temp_file_path)
            
        return result, raw_response
    
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        error_msg = str(e)
        print(f"Error processing {uploaded_file.name}: {error_msg}")
        
        return {
            "audio_file_name": uploaded_file.name,
            "error": error_msg
        }, error_msg

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

# Streamlit App
st.set_page_config(page_title="Audio Evaluation Tool", layout="wide")

st.title("Call Quality Evaluation Tool With Dustin")
st.write("Upload a WAV file to analyze call quality metrics")

# API Key input (secure)
api_key = st.text_input("Enter your Google AI API Key", type="password")

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
        result, raw_response = process_audio_file(uploaded_file, prompt)
    
    # Display the results
    display_evaluation_results(result)
    
    # Option to download the JSON result
    st.download_button(
        label="Download JSON Result",
        data=json.dumps(result, indent=2),
        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_evaluation.json",
        mime="application/json"
    )
    
    # Show raw response in expander
    with st.expander("View Raw API Response"):
        st.text(raw_response)
elif uploaded_file is not None:
    st.warning("Please enter your Google AI API key and evaluation prompt to process the file.")
