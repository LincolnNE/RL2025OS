#!/usr/bin/env python3
"""
Configuration management for Instagram Tools
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'instagram_fetcher_secret_key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    
    # File paths
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'output/downloads')
    TEMPLATE_FOLDER = os.getenv('TEMPLATE_FOLDER', 'templates')
    
    # Instagram API settings
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    
    # Image Upscaling API settings
    REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    DEEP_AI_API_KEY = os.getenv('DEEP_AI_API_KEY')
    UPSCALE_MEDIA_API_KEY = os.getenv('UPSCALE_MEDIA_API_KEY')
    LETS_ENHANCE_API_KEY = os.getenv('LETS_ENHANCE_API_KEY')
    
    # Firebase settings
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_PRIVATE_KEY_ID = os.getenv('FIREBASE_PRIVATE_KEY_ID')
    FIREBASE_PRIVATE_KEY = os.getenv('FIREBASE_PRIVATE_KEY')
    FIREBASE_CLIENT_EMAIL = os.getenv('FIREBASE_CLIENT_EMAIL')
    FIREBASE_CLIENT_ID = os.getenv('FIREBASE_CLIENT_ID')
    FIREBASE_CLIENT_X509_CERT_URL = os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
    
    # Image processing settings
    DEFAULT_MIN_RESOLUTION = int(os.getenv('DEFAULT_MIN_RESOLUTION', 800))
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    @classmethod
    def is_firebase_configured(cls):
        """Check if Firebase is properly configured"""
        required_fields = [
            cls.FIREBASE_PROJECT_ID,
            cls.FIREBASE_PRIVATE_KEY_ID,
            cls.FIREBASE_PRIVATE_KEY,
            cls.FIREBASE_CLIENT_EMAIL,
            cls.FIREBASE_CLIENT_ID,
            cls.FIREBASE_CLIENT_X509_CERT_URL
        ]
        return all(field for field in required_fields)
    
    @classmethod
    def get_firebase_config(cls):
        """Get Firebase configuration dictionary"""
        if not cls.is_firebase_configured():
            return None
            
        return {
            "type": "service_account",
            "project_id": cls.FIREBASE_PROJECT_ID,
            "private_key_id": cls.FIREBASE_PRIVATE_KEY_ID,
            "private_key": cls.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": cls.FIREBASE_CLIENT_EMAIL,
            "client_id": cls.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": cls.FIREBASE_CLIENT_X509_CERT_URL
        }
    
    @classmethod
    def get_storage_bucket(cls):
        """Get Firebase Storage bucket name"""
        return cls.FIREBASE_STORAGE_BUCKET or f"{cls.FIREBASE_PROJECT_ID}.appspot.com"
