"""Login and security utils"""

import streamlit as st
# Load secrets
users = st.secrets["usernames"]
passwords = st.secrets["passwords"]

# Simple authentication function
def authenticate(username, password):
    if username in users and users[username] == password:
        return roles[username]
    return None

# Login form
st.title("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    role = authenticate(username, password)
    if role:
        st.success(f"Welcome, {username}! Your role is: {role}")
        # Role-based actions
        if role == "admin":
            st.write("You have admin access.")
        elif role == "editor":
            st.write("You can edit content.")
        elif role == "viewer":
            st.write("You have view-only access.")
    else:
        st.error("Invalid username or password.")