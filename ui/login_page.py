"""
Login Page — Authentication UI with login and register tabs.
"""

import streamlit as st
from core.auth_manager import AuthManager


def render_login_page():
    """Render the login/register page. Returns True if authenticated."""

    auth = AuthManager()

    # Centered login container
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
    </style>
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:60vh;padding:40px;">
        <div style="text-align:center;margin-bottom:32px;">
            <span style="font-size:64px;">🧠</span>
            <h1 style="font-size:28px;font-weight:800;
                       background:linear-gradient(135deg,#667eea,#a78bfa,#ec4899);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       margin:12px 0 4px 0;">RAG Knowledge Assistant</h1>
            <p style="color:#64748b;font-size:13px;">Sign in to access your notebooks</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input("Username", key="login_username",
                                        placeholder="Enter your username")
            login_pass = st.text_input("Password", type="password", key="login_password",
                                        placeholder="Enter your password")

            if st.button("🔐 Sign In", use_container_width=True, type="primary", key="btn_login"):
                if login_user and login_pass:
                    success, msg, user_data = auth.login(login_user, login_pass)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_data = user_data
                        auth.save_session(user_data)  # persist across refresh
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter both username and password")

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_user = st.text_input("Username", key="reg_username",
                                      placeholder="Choose a username (min 3 chars)")
            reg_name = st.text_input("Display Name", key="reg_display_name",
                                      placeholder="Your display name")
            reg_pass = st.text_input("Password", type="password", key="reg_password",
                                      placeholder="Choose a password (min 4 chars)")
            reg_pass2 = st.text_input("Confirm Password", type="password", key="reg_password2",
                                       placeholder="Confirm your password")

            if st.button("📝 Create Account", use_container_width=True, type="primary", key="btn_register"):
                if not all([reg_user, reg_pass, reg_pass2]):
                    st.warning("Please fill in all fields")
                elif reg_pass != reg_pass2:
                    st.error("Passwords don't match")
                else:
                    success, msg, user_id = auth.register(reg_user, reg_name, reg_pass)
                    if success:
                        st.success(f"{msg} You can now sign in.")
                    else:
                        st.error(msg)
