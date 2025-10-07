#!/usr/bin/env python3
"""
Firebase Web App Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_firebase_config():
    """
    Get Firebase web app configuration object
    
    Returns:
        dict: Firebase configuration object
    """
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }

def print_firebase_config():
    """Print Firebase configuration for web apps"""
    config = get_firebase_config()
    
    print("Firebase Web App Configuration:")
    print("=" * 40)
    for key, value in config.items():
        if value:
            print(f"{key}: {value}")
        else:
            print(f"{key}: NOT SET")
    print("=" * 40)

if __name__ == "__main__":
    print_firebase_config()
