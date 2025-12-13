import streamlit as st
import requests
import json
import os
from datetime import datetime
import trafilatura
import time

st.set_page_config(
    page_title="AI Phone Caller",
    page_icon="📞",
    layout="wide"
)

BLAND_API_BASE = "https://api.bland.ai/v1"

def get_bland_api_key():
    """Get Bland AI API key from environment or session state"""
    api_key = os.environ.get("BLAND_AI_API_KEY", "")
    if not api_key and "bland_api_key" in st.session_state:
        api_key = st.session_state.bland_api_key
    return api_key

def scrape_website(url: str) -> str:
    """Scrape website content using trafilatura"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        st.error(f"Error scraping website: {str(e)}")
        return ""

def init_session_state():
    """Initialize session state variables"""
    if "call_history" not in st.session_state:
        st.session_state.call_history = []
    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = {
            "website_content": {},
            "transcripts": []
        }
    if "bland_api_key" not in st.session_state:
        st.session_state.bland_api_key = ""

def build_knowledge_context():
    """Build combined knowledge from website content and transcripts"""
    knowledge_parts = []
    
    for url, content in st.session_state.knowledge_base["website_content"].items():
        if content:
            knowledge_parts.append(f"--- Website Information from {url} ---\n{content}")
    
    for transcript in st.session_state.knowledge_base["transcripts"]:
        knowledge_parts.append(
            f"--- Previous Conversation ({transcript['timestamp']}) ---\n{transcript['content']}"
        )
    
    return "\n\n".join(knowledge_parts)

def initiate_call(phone_number: str, website_url: str, api_key: str, voice_settings: dict):
    """Initiate a call using Bland AI API"""
    website_content = scrape_website(website_url)
    
    if not website_content:
        st.warning("Could not extract content from the website. The AI agent will have limited knowledge.")
        website_content = f"Information from {website_url} - content could not be extracted. The caller may need to provide context about this website."
        st.session_state.knowledge_base["website_content"][website_url] = website_content
    else:
        st.session_state.knowledge_base["website_content"][website_url] = website_content
    
    full_knowledge = build_knowledge_context()
    
    task_prompt = f"""You are a real human making a phone call, NOT an AI. Your job is to:
1. Greet the person naturally and warmly
2. Answer any questions they have based on the knowledge you have
3. Be helpful, friendly, and conversational like a real person
4. If you don't know something, say something like "hmm, let me think... I'm not sure about that one"

IMPORTANT - Sound completely human by:
- Use natural filler words like "um", "uh", "hmm", "you know", "like", "so", "well"
- Pause naturally before answering, as if thinking
- Sometimes start sentences and restart them, like "I think... well actually, what I mean is..."
- React naturally with "oh", "ah", "right", "gotcha", "I see"
- Vary your pace - sometimes speak faster when excited, slower when thinking
- Use casual phrases like "yeah", "sure thing", "no problem", "absolutely"
- Occasionally make small corrections mid-sentence like a real person would

Your Knowledge Base:
{full_knowledge}

Remember to:
- Sound 100% human, never robotic or scripted
- Listen carefully and respond naturally
- Be warm, friendly, and personable
- Use the knowledge base to answer questions accurately"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "phone_number": phone_number,
        "task": task_prompt,
        "voice": voice_settings.get("voice", "nat"),
        "wait_for_greeting": True,
        "record": True,
        "max_duration": 300,
        "temperature": voice_settings.get("temperature", 0.7),
        "interruption_threshold": voice_settings.get("interruption_threshold", 100),
        "background_track": voice_settings.get("background_track", "office")
    }
    
    try:
        response = requests.post(
            f"{BLAND_API_BASE}/calls",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            call_record = {
                "call_id": result.get("call_id", "unknown"),
                "phone_number": phone_number,
                "website_url": website_url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "initiated",
                "transcript": None
            }
            st.session_state.call_history.append(call_record)
            return result
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def get_call_transcript(call_id: str, api_key: str):
    """Retrieve transcript for a completed call"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BLAND_API_BASE}/calls/{call_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_transcript(transcripts):
    """Format transcript data into readable text"""
    if not transcripts:
        return "No transcript available"
    
    formatted = []
    for entry in transcripts:
        speaker = entry.get("user", "Agent") if entry.get("user") else "Agent"
        text = entry.get("text", "")
        formatted.append(f"{speaker}: {text}")
    
    return "\n".join(formatted)

def main():
    init_session_state()
    
    st.title("📞 AI Phone Caller")
    st.markdown("Make AI-powered phone calls with knowledge from any website. Conversations are transcribed and added to the knowledge base for future calls.")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        
        env_api_key = os.environ.get("BLAND_AI_API_KEY", "")
        if env_api_key:
            st.success("✅ API Key configured via environment")
            api_key = env_api_key
        else:
            api_key = st.text_input(
                "Bland AI API Key",
                type="password",
                value=st.session_state.bland_api_key,
                help="Enter your Bland AI API key from https://app.bland.ai/dashboard/settings"
            )
            if api_key:
                st.session_state.bland_api_key = api_key
        
        st.divider()
        
        st.header("📚 Knowledge Base")
        kb = st.session_state.knowledge_base
        st.metric("Website Sources", len(kb["website_content"]))
        st.metric("Saved Transcripts", len(kb["transcripts"]))
        
        if st.button("Clear Knowledge Base", type="secondary"):
            st.session_state.knowledge_base = {
                "website_content": {},
                "transcripts": []
            }
            st.success("Knowledge base cleared!")
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📞 Make a Call", "📋 Call History", "📚 Knowledge Base"])
    
    with tab1:
        st.header("Initiate a New Call")
        
        col1, col2 = st.columns(2)
        
        with col1:
            phone_number = st.text_input(
                "Phone Number",
                placeholder="+1234567890",
                help="Enter the phone number with country code (e.g., +1 for US)"
            )
        
        with col2:
            website_url = st.text_input(
                "Website URL for Knowledge Base",
                placeholder="https://example.com",
                help="The AI will learn from this website to answer questions"
            )
        
        with st.expander("🎙️ Voice Settings (Human-like Realism)", expanded=True):
            st.markdown("Configure settings to make the AI sound exactly like a human")
            
            voice_col1, voice_col2 = st.columns(2)
            
            with voice_col1:
                voice_option = st.selectbox(
                    "Voice",
                    options=["nat", "mason", "ryan", "adriana", "tina", "evelyn"],
                    index=0,
                    help="Choose the voice personality"
                )
                
                temperature = st.slider(
                    "Spontaneity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="Higher = more spontaneous and natural, Lower = more scripted"
                )
            
            with voice_col2:
                background_track = st.selectbox(
                    "Background Atmosphere",
                    options=["office", "convention_hall", "cafe", "restaurant", "none"],
                    index=0,
                    help="Add realistic background noise"
                )
                
                interruption_threshold = st.slider(
                    "Response Speed",
                    min_value=50,
                    max_value=200,
                    value=100,
                    step=10,
                    help="Lower = responds faster, Higher = waits longer (more thoughtful)"
                )
        
        voice_settings = {
            "voice": voice_option,
            "temperature": temperature,
            "background_track": background_track,
            "interruption_threshold": interruption_threshold
        }
        
        if st.button("🚀 Start Call", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please enter your Bland AI API key in the sidebar.")
            elif not phone_number:
                st.error("Please enter a phone number.")
            elif not website_url:
                st.error("Please enter a website URL.")
            else:
                with st.spinner("Scraping website and initiating call..."):
                    result = initiate_call(phone_number, website_url, api_key, voice_settings)
                
                if "error" in result:
                    st.error(f"Failed to initiate call: {result['error']}")
                else:
                    st.success(f"✅ Call initiated successfully!")
                    st.json(result)
        
        st.divider()
        st.markdown("### How it works")
        st.markdown("""
        1. **Enter a phone number** - The AI will call this number
        2. **Provide a website URL** - Content from this site becomes the AI's knowledge base
        3. **Configure voice settings** - Adjust for maximum human-like realism
        4. **Click Start Call** - The AI agent will call and answer questions naturally
        5. **Transcripts are saved** - Each conversation is added to the knowledge base for future calls
        """)
    
    with tab2:
        st.header("Call History")
        
        if not st.session_state.call_history:
            st.info("No calls made yet. Start a call from the 'Make a Call' tab.")
        else:
            for i, call in enumerate(reversed(st.session_state.call_history)):
                with st.expander(f"📞 {call['phone_number']} - {call['timestamp']}", expanded=(i == 0)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Call ID:** {call['call_id']}")
                        st.write(f"**Website:** {call['website_url']}")
                    with col2:
                        st.write(f"**Status:** {call['status']}")
                        st.write(f"**Time:** {call['timestamp']}")
                    
                    if st.button(f"🔄 Fetch Transcript", key=f"fetch_{call['call_id']}"):
                        if api_key:
                            with st.spinner("Fetching transcript..."):
                                transcript_data = get_call_transcript(call['call_id'], api_key)
                            
                            if "error" in transcript_data:
                                st.error(f"Error: {transcript_data['error']}")
                            else:
                                call_status = transcript_data.get("status", "unknown")
                                call["status"] = call_status
                                
                                transcripts = transcript_data.get("transcripts", [])
                                if transcripts:
                                    formatted = format_transcript(transcripts)
                                    call["transcript"] = formatted
                                    
                                    existing_ids = [t['call_id'] for t in st.session_state.knowledge_base["transcripts"]]
                                    if call['call_id'] not in existing_ids:
                                        st.session_state.knowledge_base["transcripts"].append({
                                            "call_id": call['call_id'],
                                            "timestamp": call['timestamp'],
                                            "content": formatted
                                        })
                                        st.success("Transcript fetched and added to knowledge base!")
                                    else:
                                        st.info("Transcript already in knowledge base.")
                                    st.text_area("Transcript", formatted, height=200)
                                else:
                                    st.warning("No transcript available yet. The call may still be in progress.")
                        else:
                            st.error("API key required to fetch transcript")
                    
                    if call.get("transcript"):
                        st.text_area("Saved Transcript", call["transcript"], height=200, key=f"saved_{call['call_id']}")
    
    with tab3:
        st.header("Knowledge Base Contents")
        
        st.subheader("🌐 Website Content")
        if st.session_state.knowledge_base["website_content"]:
            for url, content in st.session_state.knowledge_base["website_content"].items():
                with st.expander(f"📄 {url}"):
                    st.text_area("Content", content[:5000] + ("..." if len(content) > 5000 else ""), height=200, key=f"web_{url}")
        else:
            st.info("No website content in knowledge base yet.")
        
        st.subheader("💬 Call Transcripts")
        if st.session_state.knowledge_base["transcripts"]:
            for transcript in st.session_state.knowledge_base["transcripts"]:
                with st.expander(f"📝 Call on {transcript['timestamp']}"):
                    st.text_area("Transcript", transcript["content"], height=200, key=f"trans_{transcript['call_id']}")
        else:
            st.info("No transcripts saved yet. Fetch transcripts from completed calls in the Call History tab.")
        
        st.divider()
        st.subheader("📊 Combined Knowledge Preview")
        combined = build_knowledge_context()
        if combined:
            st.text_area("Full Knowledge Base (sent to AI on each call)", combined[:10000], height=300)
        else:
            st.info("Knowledge base is empty. Add a website URL when making a call to populate it.")

if __name__ == "__main__":
    main()
