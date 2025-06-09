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

# URL input with example URLs
url = st.text_input(
    "Enter URL:",
    placeholder="https://example.com",
    help="Enter a valid URL starting with http:// or https://"
)

# Add quick test buttons
st.markdown("**Quick Test URLs:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📝 Test JSONPlaceholder"):
        st.session_state.test_url = "https://jsonplaceholder.typicode.com/posts/1"
        
with col2:
    if st.button("🌐 Test Example.com"):
        st.session_state.test_url = "https://example.com"
        
with col3:
    if st.button("🔧 Test HTTPBin"):
        st.session_state.test_url = "https://httpbin.org/get"
        
with col4:
    if st.button("📰 Test News API"):
        st.session_state.test_url = "https://api.github.com/users/octocat"

# Use test URL if button was clicked
if 'test_url' in st.session_state:
    url = st.session_state.test_url
    st.info(f"Using test URL: {url}")
    del st.session_state.test_url

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

# Function to fetch content with multiple fallback methods
def fetch_content(url, timeout=10, headers=None):
    # Method 1: Try direct request first
    try:
        session = requests.Session()
        
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'  # Changed to close to avoid keep-alive issues
        }
        
        if user_agent:
            default_headers['User-Agent'] = user_agent
        if headers:
            default_headers.update(headers)
        
        response = session.get(
            url, 
            headers=default_headers, 
            timeout=timeout,
            allow_redirects=True,
            verify=False,  # Disable SSL verification for problematic sites
            stream=False
        )
        response.raise_for_status()
        return response
        
    except Exception as direct_error:
        # Method 2: Try using a CORS proxy service
        try:
            proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(url)}"
            proxy_response = requests.get(proxy_url, timeout=timeout)
            proxy_response.raise_for_status()
            
            proxy_data = proxy_response.json()
            if proxy_data.get('status', {}).get('http_code') == 200:
                # Create a mock response object
                class MockResponse:
                    def __init__(self, content, status_code=200, headers=None):
                        self.content = content.encode('utf-8') if isinstance(content, str) else content
                        self.text = content if isinstance(content, str) else content.decode('utf-8')
                        self.status_code = status_code
                        self.headers = headers or {'content-type': 'text/html'}
                    
                    def json(self):
                        import json
                        return json.loads(self.text)
                    
                    def raise_for_status(self):
                        if self.status_code >= 400:
                            raise requests.exceptions.HTTPError(f"{self.status_code} Error")
                
                return MockResponse(
                    proxy_data.get('contents', ''),
                    proxy_data.get('status', {}).get('http_code', 200),
                    {'content-type': 'text/html'}
                )
            else:
                raise Exception(f"Proxy returned status: {proxy_data.get('status', {})}")
                
        except Exception as proxy_error:
            # Method 3: Try alternative CORS proxy
            try:
                alt_proxy_url = f"https://cors-anywhere.herokuapp.com/{url}"
                alt_headers = default_headers.copy()
                alt_headers['X-Requested-With'] = 'XMLHttpRequest'
                
                alt_response = requests.get(alt_proxy_url, headers=alt_headers, timeout=timeout)
                alt_response.raise_for_status()
                return alt_response
                
            except Exception as alt_proxy_error:
                # Method 4: Try using requests-html (if available)
                try:
                    import urllib.request
                    import urllib.error
                    
                    req = urllib.request.Request(
                        url,
                        headers={'User-Agent': default_headers['User-Agent']}
                    )
                    
                    with urllib.request.urlopen(req, timeout=timeout) as urllib_response:
                        content = urllib_response.read()
                        
                        class UrllibResponse:
                            def __init__(self, content, code, headers):
                                self.content = content
                                self.text = content.decode('utf-8', errors='ignore')
                                self.status_code = code
                                self.headers = dict(headers)
                            
                            def json(self):
                                import json
                                return json.loads(self.text)
                            
                            def raise_for_status(self):
                                if self.status_code >= 400:
                                    raise requests.exceptions.HTTPError(f"{self.status_code} Error")
                        
                        return UrllibResponse(content, urllib_response.getcode(), urllib_response.headers)
                        
                except Exception as urllib_error:
                    # Return all errors for debugging
                    error_msg = f"""
                    All methods failed:
                    1. Direct request: {str(direct_error)}
                    2. CORS proxy: {str(proxy_error)}
                    3. Alternative proxy: {str(alt_proxy_error)}
                    4. urllib fallback: {str(urllib_error)}
                    
                    This suggests network restrictions on your deployment platform.
                    """
                    return None, error_msg

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
st.sidebar.markdown("""
### 📝 Instructions:
1. Enter a valid URL in the input field
2. Try the quick test buttons first
3. Adjust timeout and other options as needed
4. Click "Fetch Content" to retrieve the content

### ⚠️ Deployment Notes:
- **If getting connection errors on deployed apps:**
  - This is common on cloud platforms (Streamlit Cloud, Heroku)
  - The app tries multiple methods including CORS proxies
  - Some URLs may be blocked by platform firewalls
  - Try the test URLs first to verify functionality

### 🔧 Troubleshooting:
- **"Connection reset by peer"**: Platform network restrictions
- **Timeout errors**: Increase timeout or try different URL
- **403/404 errors**: Website blocks automated requests
- **CORS errors**: Use the built-in proxy methods

### 💡 Tips:
- APIs and simple websites work best
- Some sites block scraping attempts
- Custom headers can help bypass restrictions
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Alternative Solutions:")
st.sidebar.markdown("""
If still having issues:
1. **Run locally**: `streamlit run app.py`
2. **Use VPS/dedicated server** instead of managed platforms
3. **Deploy on platforms** with fewer network restrictions
4. **Use webhook/API approach** instead of direct scraping
""")