from user_service import register_user
from database import get_all_users

def main():
    print("===User Registration===")

    while True:
        print("\nEnter new user details:")

        name=input("Name: ").strip()
        email=input("Email: ").strip()

        if not name or not email:
            print("[ERROR]Name and email are required. Try again.")
            continue
        user_data={
            "name":name,
            "email":email
        }

        print("\n [INFO]Registering user...")
        registered_user=register_user(user_data)

        print(f"[SUCCESS] User registered: {registered_user}")

        print("\n [INFO] All users in the database:")
        for user in get_all_users():
            print(f"- {user["name"]} ({user['email']})")

        cont= input("\n Do you want to register another user? (y/n): ").strip().lower()
        if dont !="y":
            print("\n [INFO] Exiting the registration system.")
            break

if __name__=="__main__":
    main()