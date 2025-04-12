# Call Quality Evaluation 🎙️📊

This app takes your WAV call recordings and uses Google's Gemini AI. First, it transcribes the entire conversation and figures out who said what (diarization). Then, using a prompt with your specific criteria, Gemini evaluates the call quality, giving you scores and feedback. You can easily switch between viewing the full transcript or just what each individual speaker said using handy tabs.
For the best quality, using Gemini 2.0 Flash and above is recommended.

## Look How Easy!
The app: https://call-quality-evaluation-dzkbd6hchzb9kghhutt2fw.streamlit.app/
**![Tool instruction](https://github.com/dustinvk03/Call-Quality-Evaluation/blob/master/how-to-use-call-quality.png)

## Get it Running ⚙️

**You'll Need: Python 3.11 and some libraries (use pip install to install)**
* `google.generativeai`
* `streamlit` 
* `json`
* `numpy`
* `pandas`
* `pathlib`

1.  **Set up your OpenAI API Key:**
    * You need an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
  
2.  **Prompt example:**
The Prompt You Send to Gemini Should follow the format like that:

You are an expert evaluator reviewing [Specify Type of Call, e.g., fundraising, customer support, sales pitch] call transcripts. Your goal is to assess the [Specify Caller Role, e.g., fundraiser's, agent's, salesperson's] performance against a detailed scorecard based only on the provided transcript and criteria.

Note: The [Specify Caller Role, e.g., fundraiser, agent] DOES NOT NEED to follow any provided script examples strictly; focus on whether the core criteria are met.

Respond ONLY in valid JSON format (do not include any introductory text, explanations, or markdown formatting outside the JSON structure itself) following this structure:

JSON
```json
{
  "audio_file_name": "<filename_of_the_audio_evaluated.wav>",
  "call_length": "<call_duration_in_MM:SS_format>",
  "evaluation_summary": {
    "total_points_lost": <calculated_total_negative_points>,
    "calculation_breakdown": "<Formula_showing_how_points_were_lost, e.g., CriterionName1 (-X) + CriterionName3 (-Y) = -Z>",
    "high_penalty_flag": <true_if_total_points_lost_exceeds_threshold_else_false>
  },
  "criteria_evaluation": [
    // Add one object here for EACH criterion defined below
    {
      "criterion": "[Exact Name/Description of Criterion 1]",
      "weight": <Negative_point_value_if_Not_Met_for_Criterion_1, e.g., -2>,
      "status": "<Met | Not Met | Not Applicable>", // Choose one based on evaluation
      "evidence": "<Direct quote(s) or specific observation from the transcript supporting the status>",
      "confidence": "<High | Medium | Low>", // AI's confidence in this specific evaluation
      "notes": "<Brief explanation for the status, especially if ambiguous or 'Not Applicable'>"
    },
    {
      "criterion": "[Exact Name/Description of Criterion 2]",
      "weight": <Negative_point_value_if_Not_Met_for_Criterion_2, e.g., -1>,
      "status": "<Met | Not Met | Not Applicable>",
      "evidence": "<Direct quote(s) or specific observation from the transcript supporting the status>",
      "confidence": "<High | Medium | Low>",
      "notes": "<Brief explanation for the status, especially if ambiguous or 'Not Applicable'>"
    }
    // ... Continue adding objects for ALL your criteria
  ]
}```

Evaluation Criteria & Rules:

(Define YOUR specific criteria here. Mark as "Not Applicable" if the caller did not have a reasonable opportunity to meet the criterion during the call.)

- [Criterion Name 1] (<Weight, e.g., -2 points>): [Explain what the caller needs to do to meet this criterion. Provide clear positive/negative examples if helpful]. Example: Does caller confirm contact identity? Example: "Am I speaking with [Name]?" or "Is this [Name]?". Mark as "Met" if the donor implicitly agrees.
- [Criterion Name 2] (<Weight, e.g., -1 point>): [Explain what the caller needs to do to meet this criterion]. Example: Proper Campaign Mention (-2): Does caller mention specific campaign/committee/candidate during intro?
- [Criterion Name 3] (<Weight, e.g., -2 points>): [Explain what the caller needs to do to meet this criterion]. Example: Self Identification (-2): Does caller identify themselves clearly? Example: "My name is [Name]".
... (Add all other criteria you want evaluated)
General Guidance for Evaluation:

Prioritize giving the [Specify Caller Role, e.g., fundraiser, agent] the benefit of the doubt. If ambiguity exists in the transcript or actions can be interpreted multiple ways, lean towards "Met" or "Not Applicable" rather than "Not Met." The goal is to identify significant deviations or errors.
Calculate total_points_lost by summing the weight values ONLY for criteria marked as "Not Met". Ignore weights for "Met" and "Not Applicable".
Set high_penalty_flag to true if total_points_lost is less than or equal to <Your Negative Point Threshold, e.g., -5> (meaning the penalty magnitude meets or exceeds your threshold). Otherwise, set it to false.
(Optional: Include if you provide a reference script along with the transcript)

Below is the guidance script that the [Specify Caller Role, e.g., fundraiser, agent] may have used as a reference. Evaluate the call based on the defined criteria, remembering the caller DOES NOT NEED to follow this script word-for-word.

[Paste Your Guidance Script Text Here, if applicable]

How to Use This Template:

Replace all bracketed placeholders ([...] and <...>) with your specific details (type of calls, caller roles, criteria names, explanations, weights, threshold, etc.).
Ensure the JSON structure in the prompt exactly matches the format shown.
List all your evaluation criteria clearly in the designated section.
When sending the request to the Gemini API, this entire block of text (after filling in your details) becomes the prompt content, along with the call transcript itself.

3.  **Run the app:**
    ```bash
    streamlit run streamlit_app.py
    ```
