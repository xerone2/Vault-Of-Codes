import streamlit as st
from argon2 import PasswordHasher
import json
import pandas as pd
# Initialize PasswordHasher with default parameters
ph = PasswordHasher()

def create_new_account():
    st.title("Create New Account")
    new_username = st.text_input("Enter new Username:", key="new_username")
    new_password = st.text_input("Enter new Password:", type="password", key="new_password")
    new_vault_pin = st.text_input("Enter 4-Digit Vault PIN", type="password", key="new_vault_pin")

    if st.button("Create Account"):
        if not new_username:
            st.error("Username cannot be empty.")
            return
        if not new_password:
            st.error("Password cannot be empty.")
            return
        if not new_vault_pin:
            st.error("Vault PIN cannot be empty.")
            return
        if not new_vault_pin.isdigit() or len(new_vault_pin) != 4:
            st.error("Invalid vault pin. It should be a 4-digit number.")
            return

        # Hash and salt the password using Argon2
        hashed_password = ph.hash(new_password)

        # Save user details to 'user_data.txt' file
        with open('user_data.txt', 'a') as file:
            file.write(f"{new_username}:{hashed_password}:{new_vault_pin}\n")

        st.success("Account created successfully.")

def login():
    st.title("Login")
    username = st.text_input("Enter username:", key="login_username")
    password = st.text_input("Enter password:", type="password", key="login_password")

    if st.button("Login"):
        if not username:
            st.error("Username cannot be empty.")
            return
        if not password:
            st.error("Password cannot be empty.")
            return

        # Verify the username and password using 'user_data.txt' file
        if verify_login(username, password):
            st.success("Login successful.")
            st.session_state.user_authenticated = True
            st.session_state.current_user = username
            main_menu()
        else:
            st.error("Invalid credentials. Please try again.")

def verify_login(username, password):
    # Verify the username and password using 'user_data.txt' file
    try:
        with open('user_data.txt', 'r') as file:
            for line in file:
                split_val = line.strip().split(":")
                stored_username, stored_hashed_password = split_val[0], split_val[1]
                if username == stored_username and ph.verify(stored_hashed_password, password):
                    return True
    except FileNotFoundError:
        return False
    return False


def main_menu():
    st.sidebar.title("Menu")
    menu_choice = st.sidebar.radio("Choose an option", ["Add Credentials", "Show Saved Credentials"])
    if menu_choice == "Add Credentials":
        add_credentials()
    elif menu_choice == "Show Saved Credentials":
        show_saved_credentials()

def sign_out():
    st.session_state.user_authenticated = False
    st.session_state.current_user = None
    st.success("You have been signed out.")

def add_credentials():
    st.title("Add Credentials")
    app_username = st.text_input("Enter app username:", key="app_username")
    app_password = st.text_input("Enter app password:", type="password", key="app_password")
    website = st.text_input("Enter website/url/app name:", key="website")
    email = st.text_input("Enter email (optional):", key="email")

    if st.button("Save Credentials"):
        if not app_username:
            st.error("App username cannot be empty.")
            return
        if not app_password:
            st.error("App password cannot be empty.")
            return
        if not website:
            st.error("Website/URL/App name cannot be empty.")
            return

        # Load existing data or initialize an empty list if there's a JSON decode error
        try:
            credentials_data = load_credentials_data()
        except json.JSONDecodeError:
            credentials_data = []

        # Save credentials to 'credentials_data.json' file
        credentials_data.append({
            "master_username": st.session_state.current_user,
            "app_username": app_username,
            "app_password": app_password,
            "website": website,
            "email": email
        })

        save_credentials_data(credentials_data)
        st.success("Credentials added successfully.")

def show_saved_credentials():
    user = st.text_input("Enter Username")
    vault_pin = st.text_input("Enter a 4-digit one-time vault pin:", type="password")

    if st.button("Show Credentials"):
        # Validate one-time vault pin format
        if not vault_pin.isdigit() or len(vault_pin) != 4:
            st.error("Invalid one-time vault pin. It should be a 4-digit number.")
            return

        # Verify the one-time vault pin
        if verify_vault_pin(user, vault_pin):
            # Display saved credentials for the given user from 'credentials_data.json' file using Pandas DataFrame
            try:
                data_list = load_credentials_data()

                user_credentials = [data for data in data_list if 'master_username' in data and data['master_username'] == user]

                if user_credentials:
                    df = pd.DataFrame(user_credentials)
                    st.write(df)
                else:
                    st.info(f"No credentials found for user '{user}' in the vault.")
            except FileNotFoundError:
                st.info("No credentials found in the vault.")

def verify_vault_pin(username, pin):
    # Verify the vault pin using 'user_data.txt' file
    try:
        with open('user_data.txt', 'r') as file:
            for line in file:
                data = line.strip().split(":")
                if data[0] == username and data[2] == pin:
                    return True
    except FileNotFoundError:
        return False
    return False

def load_credentials_data():
    try:
        with open('credentials_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_credentials_data(data):
    with open('credentials_data.json', 'w') as file:
        json.dump(data, file, indent=2)

# Streamlit widgets
if not st.session_state.get("user_authenticated", False):
    create_new_account()
    login()
else:
    main_menu()


if st.session_state.get("user_authenticated", False):
    st.sidebar.button("Sign Out", on_click=sign_out)