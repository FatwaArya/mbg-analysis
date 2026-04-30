import streamlit as st

def require_auth():
    if st.session_state.get("authenticated"):
        return
    st.markdown("## MBG Research Dashboard")
    st.caption("Makan Bergizi Gratis  Twitter/X Discourse Study 20252026")
    st.markdown("---")
    pwd = st.text_input("Enter research password", type="password", key="_auth_pwd")
    if st.button("Unlock Dashboard", use_container_width=True):
        if pwd == st.secrets["dashboard_password"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
