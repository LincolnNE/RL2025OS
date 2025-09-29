#!/usr/bin/env python3
"""
Firebase configuration and authentication
"""

import os
import firebase_admin
from firebase_admin import credentials, storage, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseManager:
    def __init__(self):
        """Initialize Firebase services"""
        self.app = None
        self.bucket = None
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase app and services"""
        try:
            # Get Firebase config from environment variables
            firebase_config = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
            }
            
            # Get storage bucket from environment or use default
            storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET") or f"{firebase_config['project_id']}.appspot.com"
            
            # Initialize Firebase app
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config)
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': storage_bucket
                })
            else:
                self.app = firebase_admin.get_app()
            
            # Initialize Storage and Firestore
            self.bucket = storage.bucket()
            self.db = firestore.client()
            
            print("Firebase initialized successfully")
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            raise
    
    def upload_image(self, local_file_path: str, remote_path: str) -> str:
        """
        Upload image to Firebase Storage
        
        Args:
            local_file_path: Local file path
            remote_path: Remote path in Firebase Storage
            
        Returns:
            Download URL of uploaded file
        """
        try:
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_file_path)
            
            # Make the blob publicly accessible
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            print(f"Upload error: {e}")
            raise
    
    def save_media_metadata(self, media_data: dict, download_url: str):
        """
        Save media metadata to Firestore
        
        Args:
            media_data: Instagram media data
            download_url: Firebase Storage download URL
        """
        try:
            # Prepare document data
            doc_data = {
                'instagram_id': media_data.get('id'),
                'caption': media_data.get('caption', ''),
                'media_type': media_data.get('media_type'),
                'instagram_url': media_data.get('media_url'),
                'permalink': media_data.get('permalink'),
                'timestamp': media_data.get('timestamp'),
                'firebase_url': download_url,
                'uploaded_at': firestore.SERVER_TIMESTAMP
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('instagram_media').add(doc_data)
            print(f"Metadata saved to Firestore: {doc_ref[1].id}")
            
            return doc_ref[1].id
            
        except Exception as e:
            print(f"Firestore save error: {e}")
            raise
    
    def get_media_collection(self):
        """Get all media from Firestore collection"""
        try:
            docs = self.db.collection('instagram_media').stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Firestore read error: {e}")
            raise
