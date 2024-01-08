import getpass
import secrets
import base64
import mysql.connector
from prettytable import PrettyTable
from argon2 import PasswordHasher
from passlib.hash import argon2
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# myDB
host = "host"
user = "user-name"
password = "database-password"
database = "database-name"

# Initialize PasswordHasher with default parameters
ph = PasswordHasher()

# Define symmetric key variables
KDF_ALGORITHM = hashes.SHA256()
KDF_LENGTH = 32
KDF_ITERATIONS = 120000

with open('salt_file.txt', 'r') as file:
    # Reading the salt from a file
    salt_key = file.read()


# NEW ACCOUNT
def create_new_account():
    while True:
        master_username = input("Enter username: ")
        master_password = getpass.getpass("Enter password: ")

        if master_username and master_password:
            if check_existing_username(master_username):
                return print("Username already exists. Choose a different username.")

            vault_pin = input("Enter a 4-digit one-time vault pin: ")

            if vault_pin.isdigit():
                if len(vault_pin) == 4:
                    email = input('Enter email: ')
                    break
                else:
                    return print("Invalid one-time vault pin. It should be a 4-digit number.")

        else:
            return print("Enter a valid Username/Password")

    # Hash and salt the password using Argon2
    hashed_password = ph.hash(master_password)
    query = "INSERT INTO master (username, password, vault_key, email) VALUES (%s, %s, %s, %s)"
    values = (master_username, hashed_password, vault_pin, email)
    cursor.execute(query, values)
    connection.commit()
    print("Account Created Successfully")
    cursor.close()


def check_existing_username(username):
    try:
        cursor = connection.cursor()
        query = "SELECT username FROM master WHERE username = %s"
        cursor.execute(query, (username,))
        existing_username = cursor.fetchone()
        if existing_username:
            print("Username already exists, Try again!")
            cursor.close()
            return True
        else:
            cursor.close()
            return False

    except mysql.connector.errors as e:
        print(f"Error: {e}")


def login():
    master_username = input("Enter username: ")
    master_password = getpass.getpass("Enter password: ")
    if verify_login(master_username, master_password):
        vault_menu(master_username)
    else:
        ask = input("Invalid credentials. Do you want to re-try (y/n):")
        if ask == "y":
            login()
        elif ask == "n":
            return


def verify_login(username, password):
    try:
        cursor = connection.cursor()
        # Check if the username exists
        query = "SELECT password FROM master WHERE username = %s"
        cursor.execute(query, (username,))
        stored_password = cursor.fetchone()

        if stored_password:
            # Verify the password using a password hashing library (e.g., passlib)
            if argon2.verify(password, stored_password[0]):
                print("Login successful")
                cursor.close()
                return True
        cursor.close()
    except mysql.connector.errors as e:
        print(f"Error: {e}")


def vault_menu(master_username):
    while True:
        print("\nVault Menu:")
        print("1. Add Credentials")
        print("2. Show Saved Credentials")
        print("3. Delete")
        print("4. Exit Vault Menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            add_credentials(master_username)
        elif choice == '2':
            show_saved_credentials(master_username)
        elif choice == '3':
            delete_credentials()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")
    cursor.close()


def encrypt(plaintext: str, password: str) -> (bytes, bytes):
    # Derive a symmetric key using the password and a fresh random salt.
    salt = secrets.token_bytes(16)
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM, length=KDF_LENGTH, salt=salt,
        iterations=KDF_ITERATIONS)
    key = kdf.derive(password.encode("utf-8"))

    # Encrypt the message.
    f = Fernet(base64.urlsafe_b64encode(key))
    ciphertext = f.encrypt(plaintext.encode("utf-8"))

    return ciphertext, salt


def decrypt(ciphertext: bytes, password: str, salt: bytes) -> str:
    # Derive the symmetric key using the password and provided salt.
    kdf = PBKDF2HMAC(
        algorithm=KDF_ALGORITHM, length=KDF_LENGTH, salt=salt,
        iterations=KDF_ITERATIONS)
    key = kdf.derive(password.encode("utf-8"))

    # Decrypt the message
    f = Fernet(base64.urlsafe_b64encode(key))
    plaintext = f.decrypt(ciphertext)

    return plaintext.decode("utf-8")


def generate_random_password(length=12):
    import random
    import string

    # Define the characters to include in the password
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate the random password
    app_password = ''.join(random.choice(characters) for _ in range(length))

    return app_password


def add_credentials(username):
    try:
        while True:
            app_username = input("Enter app username: ")
            if app_username:
                break
            else:
                print("This field CAN NOT be empty! Please Enter a valid app username")
        # Password choice
        ask = input("Do you want to generate a random password?(y/n): ")
        if ask == "y":
            app_password = generate_random_password(length=12)
        elif ask == "n":
            app_password = getpass.getpass("Enter app password: ")
        else:
            print("Enter valid choice")
            return
        website = input("Enter website/url/app name: ")
        email = input("Enter email (optional): ") or "N/A"
        # Encryption
        encrypted, salt = encrypt(app_password, salt_key)
        # Add data
        with connection.cursor() as cursor:
            query = ("INSERT INTO vault (app_username, app_password, master_username, website, app_email, salt) "
                     "VALUES (%s, %s, %s, %s, %s, %s)")

            values = (app_username, encrypted, username, website, email, salt)
            cursor.execute(query, values)
            connection.commit()
            print("Credentials Saved Successfully")

    except mysql.connector.errors as e:
        print(f"Error: {e}")


# Retrieving saved data
def show_saved_credentials(username):
    try:
        vault_pin = int(input("Enter a 4-digit one-time vault pin: "))
        cursor1 = connection.cursor()
        cursor2 = connection.cursor()
        query1 = "SELECT vault_key FROM master WHERE username = %s"
        cursor1.execute(query1, (username,))
        result1 = cursor1.fetchone()
        if vault_pin == result1[0]:
            print("PIN Status: OK")
            query2 = "SELECT * FROM vault"
            cursor2.execute(query2)
            result2 = cursor2.fetchall()
            if not result2:
                print("No saved Records!")
            else:
                table = PrettyTable()
                table.field_names = ["App Username", "App Password", "Website/URL/App Name", "Email"]

                for row in result2:
                    try:
                        bytes_salt = bytes(row[5])
                        bytes_app_password = bytes(row[1])
                        decrypted_password = decrypt(bytes_app_password, salt_key, bytes_salt)

                        table.add_row([row[0], decrypted_password, row[3], row[4]])

                    except InvalidToken as e:
                        print(f"Error: Invalid token. Failed to decrypt the password.{e}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                print(table)
        else:
            ask = input("Invalid PIN. Do you want to re-try(y/n): ")
            if ask == "y":
                show_saved_credentials(username)
            elif ask == "n":
                pass

    except mysql.connector.errors as e:
        print(f"Error: {e}")
    except TypeError:
        print("Invalid one-time vault pin. It should be a 4-digit integer.")
    except InvalidToken:
        print("Error: Invalid token. Failed to decrypt the password.")
    finally:
        cursor1.close()
        cursor2.close()


def delete_credentials():
    # same username collision to be handled later
    try:
        cursor1 = connection.cursor()
        username = input("Enter username to be deleted :")
        query1 = "SELECT app_username from vault WHERE app_username = %s"
        cursor1.execute(query1, (username,))
        result = cursor1.fetchone()
        if username in result:
            ask = input(f"Records found! \n WARNING! all data associated with '{username}' will be deleted.\n"
                        f"Do you want to continue (y/n):")
            if ask == "y":
                cursor2 = connection.cursor()
                query2 = "DELETE FROM vault WHERE app_username = %s"
                cursor2.execute(query2, (username,))
                connection.commit()
                print("Records DELETED!!")
                cursor2.close()
            elif ask == "n":
                pass
            else:
                print("Invalid input")
                return
        else:
            print(f"No Records Found for '{username}'")
    except TypeError:
        print("Invalid input")
    except Exception as e:
        print(f"Error :{e}")
    except mysql.connector.errors as e:
        print(f"Error: {e}")
    finally:
        cursor1.close()


if __name__ == "__main__":
    # Establish a connection to the MySQL server
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
            )
        cursor = connection.cursor()
        if connection.is_connected():
            print("Connected to MySQL database")

            while True:
                # Create a cursor object to execute SQL queries

                print("\nPassword Manager Menu:")
                print("1. Create New Account")
                print("2. Login")
                print("3. Quit")
                choice = input("Enter your choice: ")

                if choice == '1':
                    create_new_account()
                elif choice == '2':
                    login()
                elif choice == '3':
                    break
                else:
                    print("Invalid choice. Please try again.")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        # Close the connection when done
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("Connection closed")
