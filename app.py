import streamlit as st
import requests
import time
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Model Comparison",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .comparison-card {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .faster-badge {
        background: #10b981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title and header
st.title("⚡ AI Model Comparison Tool")
st.markdown("Compare performance and responses between different AI models")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key - Use secrets or user input
    try:
        # Try to get API key from secrets first
        api_key = st.secrets["OPENROUTER_API_KEY"]
        st.success("✅ API Key loaded from secrets")
    except (KeyError, AttributeError):
        # Fallback to user input if secrets not available
        api_key = st.text_input(
            "OpenRouter API Key", 
            type="password",
            help="Enter your OpenRouter API key. Get one from https://openrouter.ai/"
        )
        if not api_key:
            st.warning("⚠️ Please enter your OpenRouter API key to use the app")
    
    # Model Selection
    st.subheader("Model Selection")
    model_1 = st.selectbox(
        "First Model",
        ["qwen/qwen3-32b", "qwen/qwen3-14b", "anthropic/claude-3-haiku"],
        index=0
    )
    
    model_2 = st.selectbox(
        "Second Model", 
        ["qwen/qwen3-32b", "qwen/qwen3-14b", "anthropic/claude-3-haiku"],
        index=1
    )
    
    # Parameters
    st.subheader("Parameters")
    max_tokens = st.slider("Max Tokens", 50, 2000, 200, 50)
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Enter Your Prompt")
    prompt = st.text_area(
        "Prompt",
        placeholder="Enter your test prompt here...",
        height=150,
        label_visibility="collapsed"
    )

with col2:
    st.subheader("🚀 Actions")
    
    # Compare button
    compare_button = st.button("⚡ Compare Both Models", type="primary")
    
    # Individual test buttons
    col_a, col_b = st.columns(2)
    with col_a:
        test_model_1 = st.button(f"Test {model_1.split('/')[-1].upper()}")
    with col_b:
        test_model_2 = st.button(f"Test {model_2.split('/')[-1].upper()}")

# Function to make API call
def make_api_call(model, prompt, api_key, max_tokens, temperature):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://comparemodel.streamlit.app/",  # Add referer
        "X-Title": "AI Model Comparison Tool"  # Add title
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            try:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Debug: Check if content is empty or None
                if not content or content.strip() == "":
                    content = "[Empty response from model]"
                
                return {
                    "success": True,
                    "content": content,
                    "response_time": response_time,
                    "word_count": len(content.split()),
                    "char_count": len(content),
                    "words_per_second": len(content.split()) / response_time if response_time > 0 else 0,
                    "raw_response": result  # Add raw response for debugging
                }
            except (KeyError, IndexError, TypeError) as e:
                return {
                    "success": False,
                    "error": f"Failed to parse response: {str(e)}",
                    "response_time": response_time,
                    "raw_response": response.text
                }
        else:
            return {
                "success": False,
                "error": f"Error {response.status_code}: {response.text}",
                "response_time": response_time,
                "status_code": response.status_code
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "response_time": 0
        }

# Function to display results
def display_comparison_results(result1, result2, model1_name, model2_name):
    st.markdown("---")
    st.header("📊 Comparison Results")
    
    # Model icons mapping
    model_icons = {
        "qwen": "[QWEN]", 
        "claude": "[CLAUDE]",
    }
    
    def get_model_icon(model_name):
        for key, icon in model_icons.items():
            if key in model_name.lower():
                return icon
        return "[AI]"
    
    # Success indicators and response display
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{get_model_icon(model1_name)} {model1_name.split('/')[-1].upper()}")
        if result1["success"]:
            st.success(f"Generated in {result1['response_time']:.2f} seconds")
            st.markdown("**Result:**")
            # Debug info
            if result1["content"] == "[Empty response from model]":
                st.warning("Model returned empty response")
                with st.expander("Debug Info"):
                    st.json(result1.get("raw_response", {}))
            st.text_area("", value=result1["content"], height=200, key="result1", disabled=True)
        else:
            st.error(f"Error: {result1['error']}")
            with st.expander("Debug Info"):
                st.text(result1.get("raw_response", "No debug info available"))
                if "status_code" in result1:
                    st.text(f"Status Code: {result1['status_code']}")
    
    with col2:
        st.subheader(f"{get_model_icon(model2_name)} {model2_name.split('/')[-1].upper()}")
        if result2["success"]:
            st.success(f"Generated in {result2['response_time']:.2f} seconds")
            st.markdown("**Result:**")
            # Debug info
            if result2["content"] == "[Empty response from model]":
                st.warning("Model returned empty response")
                with st.expander("Debug Info"):
                    st.json(result2.get("raw_response", {}))
            st.text_area("", value=result2["content"], height=200, key="result2", disabled=True)
        else:
            st.error(f"Error: {result2['error']}")
            with st.expander("Debug Info"):
                st.text(result2.get("raw_response", "No debug info available"))
                if "status_code" in result2:
                    st.text(f"Status Code: {result2['status_code']}")
    
    # Performance comparison (only if both succeeded)
    if result1["success"] and result2["success"]:
        st.markdown("---")
        st.header("⚡ Performance Comparison")
        
        # Determine faster model
        faster_model = model1_name if result1["response_time"] < result2["response_time"] else model2_name
        time_diff = abs(result1["response_time"] - result2["response_time"])
        speed_improvement = (time_diff / max(result1["response_time"], result2["response_time"])) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Model 1 Time**")
            st.markdown(f"### {result1['response_time']:.2f}s")
        
        with col2:
            st.markdown("**Model 2 Time**")
            st.markdown(f"### {result2['response_time']:.2f}s")
        
        with col3:
            st.markdown("**Faster Model**")
            st.markdown(f"### {faster_model.split('/')[-1].upper()}")
            st.markdown(f"<span class='faster-badge'>↑ {speed_improvement:.1f}% faster</span>", unsafe_allow_html=True)
        
        # Text Statistics
        st.markdown("---")
        st.header("📈 Text Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{model1_name.split('/')[-1].upper()} Statistics:**")
            st.markdown(f"• Words: {result1['word_count']}")
            st.markdown(f"• Characters: {result1['char_count']}")
            st.markdown(f"• Words/second: {result1['words_per_second']:.1f}")
        
        with col2:
            st.markdown(f"**{model2_name.split('/')[-1].upper()} Statistics:**")
            st.markdown(f"• Words: {result2['word_count']}")
            st.markdown(f"• Characters: {result2['char_count']}")
            st.markdown(f"• Words/second: {result2['words_per_second']:.1f}")

# Handle button clicks
if compare_button and prompt and api_key:
    with st.spinner("Loading... Comparing models..."):
        result1 = make_api_call(model_1, prompt, api_key, max_tokens, temperature)
        result2 = make_api_call(model_2, prompt, api_key, max_tokens, temperature)
        
        display_comparison_results(result1, result2, model_1, model_2)

elif test_model_1 and prompt and api_key:
    with st.spinner(f"Loading... Testing {model_1}..."):
        result = make_api_call(model_1, prompt, api_key, max_tokens, temperature)
        
        st.markdown("---")
        st.header(f"Test Results - {model_1.split('/')[-1].upper()}")
        
        if result["success"]:
            st.success(f"Generated in {result['response_time']:.2f} seconds")
            st.markdown("**Result:**")
            st.text_area("", value=result["content"], height=200, disabled=True)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Words", result['word_count'])
            with col2:
                st.metric("Characters", result['char_count'])
            with col3:
                st.metric("Words/sec", f"{result['words_per_second']:.1f}")
        else:
            st.error(f"Error: {result['error']}")
            with st.expander("Debug Info"):
                st.text(result.get("raw_response", "No debug info available"))
                if "status_code" in result:
                    st.text(f"Status Code: {result['status_code']}")

elif test_model_2 and prompt and api_key:
    with st.spinner(f"Loading... Testing {model_2}..."):
        result = make_api_call(model_2, prompt, api_key, max_tokens, temperature)
        
        st.markdown("---")
        st.header(f"Test Results - {model_2.split('/')[-1].upper()}")
        
        if result["success"]:
            st.success(f"Generated in {result['response_time']:.2f} seconds")
            st.markdown("**Result:**")
            st.text_area("", value=result["content"], height=200, disabled=True)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Words", result['word_count'])
            with col2:
                st.metric("Characters", result['char_count'])
            with col3:
                st.metric("Words/sec", f"{result['words_per_second']:.1f}")
        else:
            st.error(f"Error: {result['error']}")
            with st.expander("Debug Info"):
                st.text(result.get("raw_response", "No debug info available"))
                if "status_code" in result:
                    st.text(f"Status Code: {result['status_code']}")

# Validation messages
if (compare_button or test_model_1 or test_model_2) and not api_key:
    st.error("Please enter your OpenRouter API key in the sidebar")

if (compare_button or test_model_1 or test_model_2) and not prompt:
    st.error("Please enter a prompt to test")

# Footer
st.markdown("---")
st.markdown("**Note:** Make sure to enter a valid OpenRouter API key to use this application.")
st.markdown("Get your API key from [OpenRouter](https://openrouter.ai/)")