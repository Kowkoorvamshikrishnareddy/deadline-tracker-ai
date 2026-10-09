import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ensure Windows stdout/stderr handles UTF-8 cleanly
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import streamlit as st
from PIL import Image
import google.generativeai as genai
from prompts import SYSTEM_PROMPT, DIGEST_PROMPT_TEMPLATE

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Deadline Tracker AI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-success {
        background-color: #DEF7EC;
        color: #03543F;
    }
    .badge-warning {
        background-color: #FEF08A;
        color: #854D0E;
    }
    .card-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "student_email" not in st.session_state:
    st.session_state.student_email = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "extracted_deadlines_text" not in st.session_state:
    st.session_state.extracted_deadlines_text = ""

# ---------------------------------------------------------
# Helper Functions: Secrets & Configuration
# ---------------------------------------------------------
def get_secret(key: str, default: str = "") -> str:
    """Retrieve secret from st.secrets or os.environ safely without raising errors."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)

GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")
GMAIL_ADDRESS = get_secret("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = get_secret("GMAIL_APP_PASSWORD", "")

# ---------------------------------------------------------
# Helper Function: Action Tool (Gmail via SMTP)
# ---------------------------------------------------------
def send_email(to_address: str, subject: str, body: str, sender_email: str = None, sender_password: str = None):
    """
    Sends an email using Python's built-in smtplib over SSL via Gmail SMTP.
    """
    from_address = sender_email or GMAIL_ADDRESS
    app_password = sender_password or GMAIL_APP_PASSWORD

    if not from_address or not app_password:
        raise ValueError("Missing Gmail address or App Password. Please configure secrets or sidebar settings.")

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = f"Deadline Tracker AI <{from_address}>"
    msg["To"] = to_address

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_address, app_password)
        server.send_message(msg)

# ---------------------------------------------------------
# Sidebar: User Profile & API Settings
# ---------------------------------------------------------
with st.sidebar:
    st.title("📌 Student Profile")
    
    if st.session_state.onboarded:
        st.success(f"👤 **{st.session_state.student_name}**")
        st.info(f"📧 Destination: `{st.session_state.student_email}`")
        
        with st.expander("✏️ Edit Profile"):
            new_name = st.text_input("Name", value=st.session_state.student_name, key="edit_name")
            new_email = st.text_input("Email", value=st.session_state.student_email, key="edit_email")
            if st.button("Update Profile", key="btn_update_profile"):
                if new_name.strip() and new_email.strip():
                    st.session_state.student_name = new_name.strip()
                    st.session_state.student_email = new_email.strip()
                    st.success("Profile updated!")
                    st.rerun()
                else:
                    st.error("Name and email cannot be empty.")
    else:
        st.write("Please complete the onboarding step in the main view.")

    st.markdown("---")
    st.subheader("⚙️ Integrations & Keys")
    
    # Check Gemini API Key
    has_gemini = bool(GEMINI_API_KEY)
    st.markdown(
        f"**Gemini Vision AI:** "
        f"<span class='status-badge {'badge-success' if has_gemini else 'badge-warning'}'>"
        f"{'Connected ✅' if has_gemini else 'Key Needed ⚠️'}</span>",
        unsafe_allow_html=True
    )

    # Check Gmail SMTP
    has_gmail = bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)
    st.markdown(
        f"**Gmail SMTP Tool:** "
        f"<span class='status-badge {'badge-success' if has_gmail else 'badge-warning'}'>"
        f"{'Configured ✅' if has_gmail else 'Credentials Needed ⚠️'}</span>",
        unsafe_allow_html=True
    )

    with st.expander("🔑 Override API Keys / Credentials"):
        custom_gemini = st.text_input("Gemini API Key", value=GEMINI_API_KEY, type="password", key="custom_gemini")
        custom_gmail = st.text_input("Gmail Address", value=GMAIL_ADDRESS, key="custom_gmail")
        custom_pwd = st.text_input("Gmail App Password", value=GMAIL_APP_PASSWORD, type="password", key="custom_pwd")
        if custom_gemini:
            GEMINI_API_KEY = custom_gemini
        if custom_gmail:
            GMAIL_ADDRESS = custom_gmail
        if custom_pwd:
            GMAIL_APP_PASSWORD = custom_pwd

    st.markdown("---")
    if st.button("🔄 Reset Conversation / Clear History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.extracted_deadlines_text = ""
        st.success("Session reset!")
        st.rerun()

    st.markdown("---")
    st.caption("Built with Google Gemini Vision & Streamlit 🚀")

# ---------------------------------------------------------
# View 1: Onboarding Screen (if not yet onboarded)
# ---------------------------------------------------------
if not st.session_state.onboarded:
    st.markdown("<div class='main-header'>🎯 Welcome to Deadline Tracker AI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Never miss an assignment, quiz, or exam again. "
        "Snap a photo of your syllabus or schedule, and let AI organize your deadlines and email you a digest!</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 🎓 Quick Onboarding")
        st.write("Let's configure where your deadline reminders and email digests should be sent.")
        
        with st.form("onboarding_form"):
            name_input = st.text_input("Your Full Name", placeholder="e.g., Alex Johnson")
            email_input = st.text_input("Your Email Address (where reminders will be delivered)", placeholder="e.g., alex.johnson@gmail.com")
            course_input = st.text_input("Current Term / Program (Optional)", placeholder="e.g., Semester 4 - CS")
            
            submit_btn = st.form_submit_button("🚀 Start Tracking Deadlines", use_container_width=True)
            if submit_btn:
                if not name_input.strip() or not email_input.strip():
                    st.error("Please provide both your name and an email address.")
                elif "@" not in email_input or "." not in email_input:
                    st.error("Please provide a valid email address.")
                else:
                    st.session_state.student_name = name_input.strip()
                    st.session_state.student_email = email_input.strip()
                    st.session_state.onboarded = True
                    st.success("Onboarding complete! Loading tracker workspace...")
                    st.rerun()

    with col2:
        st.markdown("### 💡 How It Works")
        st.markdown(
            """
            1. **📸 Snap or Upload**: Take a photo of your syllabus, exam routine, or assignment sheet.
            2. **🤖 AI Extraction**: Gemini Vision extracts all due dates, deliverables, weights, and priorities.
            3. **💬 Ask Questions**: Clarify exam rules, ask for weekly breakdowns, or study suggestions.
            4. **📧 One-Click Email**: Click **Send Digest to Email** to get an organized reminder delivered right to your inbox!
            """
        )
    st.stop()

# ---------------------------------------------------------
# View 2: Main Application (Once Onboarded)
# ---------------------------------------------------------
st.markdown(f"<div class='main-header'>🎯 Deadline Tracker AI</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='sub-header'>Tracking for **{st.session_state.student_name}** | Destination: `{st.session_state.student_email}`</div>",
    unsafe_allow_html=True
)

# Tab structure for clean UX
tab_scan, tab_chat = st.tabs(["📸 Scan Syllabus / Schedule", "💬 Deadline Chat & Q&A"])

# ---------------------------------------------------------
# TAB 1: Scan Syllabus / Timetable
# ---------------------------------------------------------
with tab_scan:
    st.write("Upload an image of your course syllabus, exam timetable, blackboard schedule, or assignment brief:")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        uploaded_file = st.file_uploader(
            "Upload Image (PNG, JPG, JPEG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            key="syllabus_uploader"
        )
    with col_input2:
        camera_file = st.camera_input("Or Take a Live Photo using Camera", key="syllabus_camera")

    target_file = camera_file or uploaded_file

    sample_col1, sample_col2 = st.columns([1, 3])
    with sample_col1:
        use_sample = st.button("🧪 Use Sample Syllabus Text")

    image = None
    if target_file is not None:
        try:
            image = Image.open(target_file)
            st.image(image, caption="Uploaded Document Preview", use_container_width=False, width=450)
        except Exception as e:
            st.error(f"Error reading image: {e}")

    # Process Document button
    if st.button("🔍 Extract & Analyze Deadlines", type="primary", use_container_width=True):
        if not GEMINI_API_KEY:
            st.error("⚠️ Gemini API Key is missing! Please enter your key in the sidebar or `.streamlit/secrets.toml`.")
        elif image is None and not use_sample:
            st.warning("Please upload a photo or click 'Use Sample Syllabus Text' first.")
        else:
            with st.spinner("🤖 Gemini Vision is analyzing your schedule and extracting deadlines..."):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    # Use gemini-1.5-flash for fast and accurate multimodal processing
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=SYSTEM_PROMPT
                    )

                    if image is not None:
                        response = model.generate_content([
                            image,
                            "Please identify the course/subject, extract all dates, assignment deadlines, quizzes, exams, submission modes, and weights from this document into a structured tracker."
                        ])
                    else:
                        sample_text = (
                            "CS101: Introduction to Computer Science Syllabus - Fall 2026\n"
                            "Week 2 (Oct 15, 2026): Quiz 1 - Python Basics (5%)\n"
                            "Week 5 (Nov 05, 2026): Midterm Exam - In-class (25%)\n"
                            "Week 8 (Nov 26, 2026): Programming Project 1 (Canvas submission, 20%)\n"
                            "Week 11 (Dec 17, 2026): Final Project Presentation (15%)\n"
                            "Week 12 (Dec 22, 2026): Final Exam (35%)\n"
                            "Late policy: 10% penalty per day late."
                        )
                        response = model.generate_content([
                            f"Sample Syllabus Data:\n{sample_text}\n\nPlease parse this course syllabus into a structured deadline tracker."
                        ])

                    response_text = response.text
                    st.session_state.extracted_deadlines_text = response_text
                    
                    # Append to messages history
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Uploaded a new syllabus/schedule document for analysis."
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    st.success("✅ Deadlines successfully extracted! View the details below or ask questions in the Chat tab.")
                except Exception as e:
                    st.error(f"Error calling Gemini API: {e}")

    # Display Extracted Deadlines if available
    if st.session_state.extracted_deadlines_text:
        st.markdown("### 📋 Extracted Deadlines & Action Plan")
        st.markdown(st.session_state.extracted_deadlines_text)

# ---------------------------------------------------------
# Action Tool: Email Digest Section (Available across app)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📬 Action Tool: Send Reminder Digest to Email")

col_mail_info, col_mail_btn = st.columns([3, 2])
with col_mail_info:
    st.write(
        f"Ready to get an offline reminder? Click below to generate an executive reminder digest and send it directly to **{st.session_state.student_email}**."
    )
with col_mail_btn:
    send_email_clicked = st.button("📧 Send Deadline Digest to Email", type="primary", use_container_width=True)

if send_email_clicked:
    if not st.session_state.extracted_deadlines_text and not st.session_state.messages:
        st.warning("Please scan or extract deadlines from a syllabus first so there is content to send!")
    elif not GEMINI_API_KEY:
        st.error("Please configure your Gemini API Key in the sidebar or `.streamlit/secrets.toml`.")
    elif not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        st.error("⚠️ Gmail SMTP credentials not found!")
        st.info(
            """
            **How to configure Gmail SMTP (Completely Free):**
            1. Open [Google Account Security](https://myaccount.google.com/security) and ensure **2-Step Verification** is turned ON.
            2. Visit [App Passwords](https://myaccount.google.com/apppasswords).
            3. Generate an App Password for 'Mail' / 'Streamlit App'.
            4. Enter your Gmail address and 16-character App Password in the sidebar or in `.streamlit/secrets.toml`.
            """
        )
    else:
        with st.spinner("✉️ Generating personalized email digest and sending via Gmail SMTP..."):
            try:
                # Compile context from messages and extracted deadlines
                chat_context = st.session_state.extracted_deadlines_text
                if not chat_context and st.session_state.messages:
                    chat_context = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])

                genai.configure(api_key=GEMINI_API_KEY)
                digest_model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt_content = DIGEST_PROMPT_TEMPLATE.format(
                    student_name=st.session_state.student_name,
                    student_email=st.session_state.student_email,
                    chat_context=chat_context
                )
                
                digest_response = digest_model.generate_content(prompt_content)
                digest_output = digest_response.text

                # Parse Subject and Body
                subject = f"📅 Upcoming Academic Deadlines Digest for {st.session_state.student_name}"
                body = digest_output

                if "SUBJECT:" in digest_output and "BODY:" in digest_output:
                    parts = digest_output.split("BODY:", 1)
                    subject_part = parts[0].replace("SUBJECT:", "").strip()
                    if subject_part:
                        subject = subject_part
                    body = parts[1].strip()

                # Dispatch Email
                send_email(
                    to_address=st.session_state.student_email,
                    subject=subject,
                    body=body,
                    sender_email=GMAIL_ADDRESS,
                    sender_password=GMAIL_APP_PASSWORD
                )

                st.success(f"🎉 Email successfully dispatched to **{st.session_state.student_email}**!")
                with st.expander("👀 Preview Sent Email Content", expanded=True):
                    st.markdown(f"**Subject:** {subject}")
                    st.text(body)

            except Exception as e:
                st.error(f"Failed to send email: {e}")

# ---------------------------------------------------------
# TAB 2: Interactive Chat & Q&A
# ---------------------------------------------------------
with tab_chat:
    st.write("Ask any questions about your timetable, upcoming due dates, or request study tips:")

    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_query = st.chat_input("e.g., Which assignment has the highest weight? When is the midterm?")
    if user_query:
        if not GEMINI_API_KEY:
            st.error("Please configure your Gemini API Key in the sidebar or `.streamlit/secrets.toml`.")
        else:
            # Display user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate Gemini response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        chat_model = genai.GenerativeModel(
                            model_name="gemini-1.5-flash",
                            system_instruction=SYSTEM_PROMPT
                        )

                        # Construct context
                        history_prompt = "You are the student's Deadline Tracker AI assistant.\n\n"
                        if st.session_state.extracted_deadlines_text:
                            history_prompt += f"Known Syllabus / Deadlines Context:\n{st.session_state.extracted_deadlines_text}\n\n"
                        
                        history_prompt += "Conversation history:\n"
                        for m in st.session_state.messages[-6:]:
                            history_prompt += f"{m['role'].upper()}: {m['content']}\n"
                        
                        history_prompt += f"\nUser's latest question: {user_query}\nPlease provide a clear, helpful response."

                        resp = chat_model.generate_content(history_prompt)
                        st.markdown(resp.text)
                        st.session_state.messages.append({"role": "assistant", "content": resp.text})
                    except Exception as e:
                        err_msg = f"Sorry, could not process request: {e}"
                        st.error(err_msg)
                        st.session_state.messages.append({"role": "assistant", "content": err_msg})
