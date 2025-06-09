import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
import time

# Set page config
st.set_page_config(
    page_title="URL Content Fetcher",
    page_icon="🌐",
    layout="wide"
)

# Title and description
st.title("🌐 URL Content Fetcher")
st.markdown("Paste any URL below and fetch its content instantly!")

# URL input
url = st.text_input(
    "Enter URL:",
    placeholder="https://example.com",
    help="Enter a valid URL starting with http:// or https://"
)

# Options section
st.sidebar.header("⚙️ Options")
timeout = st.sidebar.slider("Request Timeout (seconds)", 5, 30, 10)
show_headers = st.sidebar.checkbox("Show Response Headers", value=False)
show_raw_html = st.sidebar.checkbox("Show Raw HTML", value=False)
user_agent = st.sidebar.text_input(
    "Custom User Agent (optional)",
    placeholder="Leave empty for default"
)

# Custom headers section
st.sidebar.subheader("Custom Headers")
custom_headers = {}
if st.sidebar.checkbox("Add custom headers"):
    num_headers = st.sidebar.number_input("Number of headers", 1, 10, 1)
    for i in range(num_headers):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            key = st.text_input(f"Header {i+1} Key", key=f"header_key_{i}")
        with col2:
            value = st.text_input(f"Header {i+1} Value", key=f"header_value_{i}")
        if key and value:
            custom_headers[key] = value

# Function to validate URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# Function to fetch content
def fetch_content(url, timeout=10, headers=None):
    try:
        # Default headers
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Update with custom user agent if provided
        if user_agent:
            default_headers['User-Agent'] = user_agent
            
        # Add custom headers
        if headers:
            default_headers.update(headers)
        
        # Make request
        response = requests.get(url, headers=default_headers, timeout=timeout)
        response.raise_for_status()
        
        return response
    except requests.exceptions.RequestException as e:
        return None, str(e)

# Main logic
if url:
    if is_valid_url(url):
        if st.button("🚀 Fetch Content", type="primary"):
            with st.spinner("Fetching content..."):
                start_time = time.time()
                result = fetch_content(url, timeout, custom_headers)
                
                if isinstance(result, tuple):  # Error case
                    response, error = result
                    st.error(f"❌ Error fetching URL: {error}")
                else:
                    response = result
                    fetch_time = time.time() - start_time
                    
                    # Success metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Status Code", response.status_code)
                    with col2:
                        st.metric("Response Time", f"{fetch_time:.2f}s")
                    with col3:
                        st.metric("Content Length", f"{len(response.content):,} bytes")
                    with col4:
                        content_type = response.headers.get('content-type', 'Unknown')
                        st.metric("Content Type", content_type.split(';')[0])
                    
                    # Show response headers if requested
                    if show_headers:
                        st.subheader("📋 Response Headers")
                        headers_dict = dict(response.headers)
                        st.json(headers_dict)
                    
                    # Content display
                    st.subheader("📄 Content")
                    
                    # Check content type and display accordingly
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        try:
                            json_data = response.json()
                            st.json(json_data)
                        except:
                            st.text(response.text)
                    
                    elif 'text/html' in content_type:
                        # Parse HTML and show cleaned text
                        try:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Extract title
                            title = soup.find('title')
                            if title:
                                st.markdown(f"**Page Title:** {title.get_text().strip()}")
                            
                            # Extract and display main content
                            # Remove script and style elements
                            for script in soup(["script", "style"]):
                                script.decompose()
                            
                            # Get text content
                            text_content = soup.get_text()
                            # Clean up text
                            lines = (line.strip() for line in text_content.splitlines())
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                            
                            # Display cleaned text
                            if clean_text:
                                st.text_area("Extracted Text Content", clean_text, height=400)
                            else:
                                st.warning("No text content found")
                            
                            # Show raw HTML if requested
                            if show_raw_html:
                                st.subheader("🔧 Raw HTML")
                                st.code(response.text, language='html')
                                
                        except Exception as e:
                            st.error(f"Error parsing HTML: {str(e)}")
                            st.text_area("Raw Content", response.text, height=400)
                    
                    elif 'text/' in content_type:
                        st.text_area("Text Content", response.text, height=400)
                    
                    elif 'image/' in content_type:
                        st.image(response.content)
                    
                    else:
                        st.info(f"Content type '{content_type}' - showing raw content")
                        if len(response.content) < 10000:  # Only show if not too large
                            st.text_area("Raw Content", response.text if hasattr(response, 'text') else str(response.content), height=400)
                        else:
                            st.warning("Content too large to display")
                    
                    # Download button
                    st.download_button(
                        label="💾 Download Content",
                        data=response.content,
                        file_name=f"content_{int(time.time())}.txt",
                        mime=content_type or "text/plain"
                    )
                    
    else:
        st.error("❌ Please enter a valid URL (must start with http:// or https://)")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <small>URL Content Fetcher | Built with Streamlit</small>
    </div>
    """, 
    unsafe_allow_html=True
)

# Instructions in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📝 Instructions:
1. Enter a valid URL in the input field
2. Adjust timeout and other options as needed
3. Click "Fetch Content" to retrieve the content
4. View the formatted content or download it

### ⚠️ Notes:
- Some websites may block automated requests
- Large files may take longer to load
- Custom headers can help bypass some restrictions
""")