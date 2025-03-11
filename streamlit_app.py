def display_evaluation_results(result):
    """Display the evaluation results in Streamlit with highlighted failed criteria"""
    if "error" in result:
        st.error(f"Error processing file: {result['error']}")
        return
    
    # Display summary information
    st.subheader("Evaluation Summary")
    
    # Calculate real points lost by summing up the point values of "Not Met" criteria
    real_points_lost = 0
    criteria_points = {
        "Confirm House Hold": 2,
        "Proper Campaign": 2,
        "Self Identification": 2,
        "Recorded Line": 2,
        "Political Reason #1": 10,
        "Dollar Drop #1": 10,
        "Political Reason #2": 10,
        "Dollar Drop #2": 10,
        "Political Reason #3": 10,
        "Dollar Drop #3": 10,
        "Assumptive Dollar Drops": 10,
        "Confirmed Amount": 20,
        "Confirmed Time Frame": 20,
        "Text Pledge": 20,
        "Credit Card Ask": 20,
        "Credit Card Rebuttal": 20,
        "Disclaimer": 2,
        "End Call Politely": 20,
        "Sold Letter": 10,
        "Sold Additional Time": 10,
        "Maximize Attempts": 20,
        "Hang Up": 20,
        "Foul Language": 20,
        "Rude": 20
    }
    
    for item in result["criteria_evaluation"]:
        criterion_name = item['criterion']
        status = item['status'].lower()
        
        if status == 'not met' and criterion_name in criteria_points:
            real_points_lost += criteria_points[criterion_name]
    
    # Create four columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Call Length", value=result.get("call_length", "N/A"))
    
    with col2:
        # Show points lost reported by the model
        points_lost = result["evaluation_summary"]["total_points_lost"]
        st.metric(
            label="Total Points Lost", 
            value=points_lost,
            delta=None
        )
    
    with col3:
        # Show real points lost calculated from criteria
        st.metric(
            label="Total Points Lost REAL", 
            value=real_points_lost,
            delta=None
        )
    
    with col4:
        high_penalty = result["evaluation_summary"]["high_penalty_flag"]
        color = "red" if high_penalty else "green"
        status_text = "YES - High Penalty" if high_penalty else "NO - No High Penalty"
        st.markdown(
            f"<div style='background-color:{color}; padding:10px; border-radius:5px;'>"
            f"<h3 style='color:white; text-align:center;'>High Penalty: {status_text}</h3></div>", 
            unsafe_allow_html=True
        )
    
    # Rest of the function remains the same
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
        
        # Get the penalty points for this criterion
        criterion_name = item['criterion']
        penalty_points = criteria_points.get(criterion_name, "?")
        
        # Create styled expander header with penalty points
        expander_label = f"{icon} {item['criterion']} (-{penalty_points}) - {item['status']}"
        
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
