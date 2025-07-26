import secrets
import argparse
from fastapi import Depends
from sqlalchemy.orm import Session

from configs.database import get_db
from src.auth.utils import hash_password

from src.auth.models import ApiKey, User


def generate_key(db: Session = Depends(get_db), show: str = "n"):
    """Generates a new API key."""
    new_key = secrets.token_urlsafe(32)  # Generate a random key
    api_key = ApiKey(key=new_key)

    db.add(api_key)
    db.commit()
    print("API key generated successfully.")
    if show == "y":
        print(f"API key: {api_key.key}")


def create_superuser(db: Session = Depends(get_db), name: str = None, email: str = None, phone: str = None, password: str = None, check_exist: str = None):
    # Check if a superuser already exists
    if bool(check_exist):
        existing_user = db.query(User).filter(
            User.is_superuser == True).first()
        if existing_user:
            print(
                "A superuser already exists. Remove check_exist argument to create a new superuser.")
            return

    """Creates a new superuser."""
    if not name:
        name = input("Name: ")
    if not email:
        email = input("Email: ")
    if not phone:
        phone = input("Phone: ")
    if not password:
        password = input("Password: ")

    if not name or not email or not phone or not password:
        print("All fields are required.")
        return
    hashed_password = hash_password(password)

    user = User(name=name, email=email, phone=phone,
                password=hashed_password, is_superuser=True)
    db.add(user)
    db.commit()

    print(f"Superuser created: ID={user.id}, Name={user.name}")


def main():
    db = next(get_db())
    parser = argparse.ArgumentParser(description="Management Commands")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate Key command
    generate_key_parser = subparsers.add_parser(
        "generate_key", help="Generates a new API key")
    generate_key_parser.add_argument(
        "--show", type=str, default="n", help="Show the API key (y/n)")

    # Create Superuser command
    create_superuser_parser = subparsers.add_parser(
        "create_superuser", help="Creates a new superuser")
    create_superuser_parser.add_argument(
        "--name", type=str, help="Superuser name")
    create_superuser_parser.add_argument(
        "--email", type=str, help="Superuser email")
    create_superuser_parser.add_argument(
        "--phone", type=str, help="Superuser phone")
    create_superuser_parser.add_argument(
        "--password", type=str, help="Superuser password")
    create_superuser_parser.add_argument(
        "--check_exist", type=bool, default=False, help="Check if superuser exists")

    args = parser.parse_args()

    if args.command == "generate_key":
        generate_key(db, show=args.show)
    elif args.command == "create_superuser":
        create_superuser(db, name=args.name, email=args.email,
                         phone=args.phone, password=args.password, check_exist=args.check_exist)


if __name__ == "__main__":
    main()
