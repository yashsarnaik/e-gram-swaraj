import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="API Response Tester",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 API Response Tester")
st.markdown("Test API endpoints and analyze their responses")

def test_url(url: str, headers: dict = None, timeout: int = 30):
    """Test a URL and return response details"""
    try:
        start_time = time.time()
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=timeout)
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        # Get response details
        response_data = {
            "status": response.status_code,
            "status_ok": response.ok,
            "headers": dict(response.headers),
            "url": response.url,
            "content_type": response.headers.get("content-type", "Not specified"),
            "response_time": response_time,
            "encoding": response.encoding
        }
        
        # Get response body
        try:
            # Try to parse as JSON first
            if "application/json" in response_data["content_type"].lower():
                response_data["body"] = response.json()
                response_data["body_type"] = "JSON"
            else:
                # Check if the response might be JSON even if content-type is wrong
                try:
                    response_data["body"] = response.json()
                    response_data["body_type"] = "JSON (detected)"
                except:
                    response_data["body"] = response.text
                    response_data["body_type"] = "Text/HTML"
        except Exception as e:
            response_data["body"] = f"Error reading body: {str(e)}"
            response_data["body_type"] = "Error"
        
        return response_data, None
        
    except requests.exceptions.Timeout:
        return None, f"Request timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return None, "Connection error - check URL and internet connection"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# URL input
url = st.sidebar.text_input(
    "Enter URL to test:",
    value="https://egramswaraj.gov.in/gpProfileStateReport.do?year=2025-2026",
    help="Enter the full URL including protocol (http/https)"
)

# Timeout setting
timeout = st.sidebar.slider("Request timeout (seconds)", min_value=5, max_value=120, value=30)

# Custom headers section
st.sidebar.subheader("Custom Headers (Optional)")
add_headers = st.sidebar.checkbox("Add custom headers")

headers = {}
if add_headers:
    # Common headers presets
    st.sidebar.markdown("**Quick presets:**")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("JSON Accept"):
            st.session_state.header_key_0 = "Accept"
            st.session_state.header_value_0 = "application/json"
    
    with col2:
        if st.button("User Agent"):
            st.session_state.header_key_1 = "User-Agent"
            st.session_state.header_value_1 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    num_headers = st.sidebar.number_input("Number of headers", min_value=1, max_value=10, value=2)
    
    for i in range(int(num_headers)):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            header_key = st.text_input(f"Header {i+1} Key", key=f"header_key_{i}")
        with col2:
            header_value = st.text_input(f"Header {i+1} Value", key=f"header_value_{i}")
        
        if header_key and header_value:
            headers[header_key] = header_value

# Test button
test_button = st.sidebar.button("🚀 Test URL", type="primary")

# Clear results button
if st.sidebar.button("🗑️ Clear Results"):
    if 'response_data' in st.session_state:
        del st.session_state.response_data
    if 'error' in st.session_state:
        del st.session_state.error

# Main content area
if test_button and url:
    with st.spinner("Testing URL..."):
        response_data, error = test_url(url, headers if headers else None, timeout)
        
        # Store in session state to persist results
        st.session_state.response_data = response_data
        st.session_state.error = error

# Display results if they exist in session state
if hasattr(st.session_state, 'response_data') or hasattr(st.session_state, 'error'):
    response_data = getattr(st.session_state, 'response_data', None)
    error = getattr(st.session_state, 'error', None)
    
    if error:
        st.error(f"❌ Error occurred: {error}")
    elif response_data:
        # Display results
        if response_data["status_ok"]:
            st.success("✅ Request completed successfully!")
        else:
            st.warning(f"⚠️ Request completed with status {response_data['status']}")
        
        # Response overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status Code", response_data["status"])
        
        with col2:
            st.metric("Response Time", f"{response_data['response_time']} ms")
        
        with col3:
            st.metric("Content Type", response_data["content_type"].split(';')[0])
        
        with col4:
            st.metric("Body Type", response_data["body_type"])
        
        # Tabs for detailed information
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Response Body", "📊 Headers", "🔗 Request Info", "📝 Raw Data", "💾 Export"])
        
        with tab1:
            st.subheader("Response Body")
            
            if response_data["body_type"] in ["JSON", "JSON (detected)"]:
                # Pretty print JSON
                st.json(response_data["body"])
                
                # Download JSON button
                json_str = json.dumps(response_data["body"], indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                # If it's a JSON response, try to create a DataFrame for tabular data
                try:
                    if isinstance(response_data["body"], list):
                        df = pd.DataFrame(response_data["body"])
                        st.subheader("Data as Table")
                        st.dataframe(df, use_container_width=True)
                        
                        # Download CSV button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"api_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    elif isinstance(response_data["body"], dict):
                        # Try to find list data within the dict
                        for key, value in response_data["body"].items():
                            if isinstance(value, list) and len(value) > 0:
                                st.subheader(f"Table: {key}")
                                try:
                                    df = pd.DataFrame(value)
                                    st.dataframe(df, use_container_width=True)
                                    
                                    # Download CSV for this table
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        label=f"📥 Download {key} CSV",
                                        data=csv,
                                        file_name=f"api_{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                        key=f"download_{key}"
                                    )
                                except:
                                    st.write(f"Could not convert {key} to table")
                except Exception as e:
                    st.write(f"Could not create table view: {e}")
                    
            else:
                # Show text/HTML content
                body_str = str(response_data["body"])
                if len(body_str) > 5000:
                    st.text_area("Response Body (truncated)", body_str[:5000] + "\n... (truncated)", height=300)
                    st.info(f"Response truncated. Full length: {len(body_str)} characters")
                else:
                    st.text_area("Response Body", body_str, height=300)
                
                # Download text button
                st.download_button(
                    label="📥 Download Response",
                    data=body_str,
                    file_name=f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        with tab2:
            st.subheader("Response Headers")
            headers_df = pd.DataFrame(list(response_data["headers"].items()), columns=["Header", "Value"])
            st.dataframe(headers_df, use_container_width=True)
            
            # Download headers as CSV
            headers_csv = headers_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Headers CSV",
                data=headers_csv,
                file_name=f"api_headers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with tab3:
            st.subheader("Request Information")
            st.write(f"**URL:** {response_data['url']}")
            st.write(f"**Status:** {response_data['status']} ({'OK' if response_data['status_ok'] else 'Error'})")
            st.write(f"**Response Time:** {response_data['response_time']} ms")
            st.write(f"**Content Type:** {response_data['content_type']}")
            st.write(f"**Encoding:** {response_data['encoding']}")
            st.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if headers:
                st.write("**Custom Headers:**")
                for key, value in headers.items():
                    st.write(f"- {key}: {value}")
        
        with tab4:
            st.subheader("Raw Response Data")
            st.json(response_data)
        
        with tab5:
            st.subheader("Export Options")
            
            # Full response export
            full_response = {
                "request": {
                    "url": url,
                    "headers": headers,
                    "timestamp": datetime.now().isoformat()
                },
                "response": response_data
            }
            
            full_json = json.dumps(full_response, indent=2)
            st.download_button(
                label="📥 Download Complete Report (JSON)",
                data=full_json,
                file_name=f"api_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            # Summary report
            summary = f"""API Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

REQUEST:
URL: {url}
Headers: {headers if headers else 'None'}

RESPONSE:
Status: {response_data['status']} ({'OK' if response_data['status_ok'] else 'Error'})
Response Time: {response_data['response_time']} ms
Content Type: {response_data['content_type']}
Body Type: {response_data['body_type']}

HEADERS:
{chr(10).join([f"{k}: {v}" for k, v in response_data['headers'].items()])}
"""
            
            st.download_button(
                label="📥 Download Summary Report (TXT)",
                data=summary,
                file_name=f"api_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# Footer with instructions
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 How to use:
1. Enter the URL you want to test
2. Optionally add custom headers
3. Set timeout if needed
4. Click "Test URL" to send the request
5. View the response in the tabs above

### 💡 Tips:
- Use full URLs with protocol (https://)
- Check the Headers tab for content-type
- JSON responses will be formatted nicely
- Large responses are truncated for performance
- Use export options to save results
""")

# Example URLs section
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Example URLs:")
example_urls = [
    "https://jsonplaceholder.typicode.com/posts/1",
    "https://api.github.com/users/octocat",
    "https://httpbin.org/json",
    "https://httpbin.org/headers"
]

for example_url in example_urls:
    if st.sidebar.button(f"Load: {example_url.split('//')[-1][:25]}...", key=f"example_{example_url}"):
        st.session_state.url_input = example_url
        st.rerun()