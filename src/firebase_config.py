#!/usr/bin/env python3
"""
Firebase configuration and authentication
"""

import os
import firebase_admin
from firebase_admin import credentials, storage, firestore
from config import Config

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
            # Check if Firebase is configured
            if not Config.is_firebase_configured():
                print("⚠️ Firebase not configured. Set required Firebase environment variables to enable Firebase features.")
                print("See FIREBASE_SETUP.md for setup instructions.")
                self.app = None
                self.bucket = None
                self.db = None
                return
            
            # Get Firebase config
            firebase_config = Config.get_firebase_config()
            storage_bucket = Config.get_storage_bucket()
            
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
            # Use 'abric' database instead of default
            self.db = firestore.client(database_id='abric')
            
            print(f"✅ Firebase initialized successfully (Project: {Config.FIREBASE_PROJECT_ID}, Bucket: {storage_bucket})")
            
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            print("Firebase features will be disabled.")
            self.app = None
            self.bucket = None
            self.db = None
    
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
            # Check if Firebase is initialized
            if not self.bucket:
                raise RuntimeError("Firebase Storage is not initialized. Please configure Firebase environment variables.")
            
            # Check if file exists
            if not os.path.exists(local_file_path):
                raise FileNotFoundError(f"Local file not found: {local_file_path}")
            
            # Get file size for logging
            file_size = os.path.getsize(local_file_path)
            print(f"📤 Uploading {os.path.basename(local_file_path)} ({file_size} bytes) to {remote_path}")
            
            # Create blob and upload
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_file_path)
            
            # Make the blob publicly accessible
            blob.make_public()
            
            print(f"✅ Successfully uploaded to Firebase Storage: {blob.public_url}")
            return blob.public_url
            
        except Exception as e:
            print(f"❌ Firebase Storage upload error: {e}")
            raise
    
    def save_media_metadata(self, media_data: dict, download_url: str, user_id: str = None):
        """
        Save media metadata to Firestore
        
        Args:
            media_data: Instagram media data
            download_url: Firebase Storage download URL
            user_id: Firebase Auth UID (optional)
        """
        try:
            # Check if Firestore is initialized
            if not self.db:
                raise RuntimeError("Firestore is not initialized. Please configure Firebase environment variables.")
            
            # Prepare document data with new structure
            doc_data = {
                'instagram_id': media_data.get('instagram_id', ''),
                'username': media_data.get('username', ''),
                'caption': media_data.get('caption', ''),
                'media_type': media_data.get('media_type', 'IMAGE'),
                'instagram_url': media_data.get('url', ''),
                'permalink': media_data.get('permalink', ''),
                'timestamp': media_data.get('timestamp'),
                'firebase_url': download_url,
                'uploaded_at': firestore.SERVER_TIMESTAMP,
                'uploaded_by': user_id,
                'upload_method': media_data.get('upload_method', 'manual_upload'),
                'metadata': {
                    'width': media_data.get('width', 0),
                    'height': media_data.get('height', 0),
                    'file_size': media_data.get('file_size', 0),
                    'format': media_data.get('format', 'JPEG')
                },
                'engagement': {
                    'likes': media_data.get('likes', 0),
                    'comments': media_data.get('comments', 0),
                    'shares': media_data.get('shares', 0)
                },
                'tags': media_data.get('tags', []),
                'location': media_data.get('location', {})
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('instagram_media').add(doc_data)
            print(f"✅ Metadata saved to Firestore: {doc_ref[1].id}")
            
            return doc_ref[1].id
            
        except Exception as e:
            print(f"❌ Firestore save error: {e}")
            raise
    
    def get_media_collection(self, user_id: str = None, username: str = None, limit: int = 50):
        """Get media from Firestore collection with filters"""
        try:
            query = self.db.collection('instagram_media')
            
            # Filter by user if provided
            if user_id:
                query = query.where('uploaded_by', '==', user_id)
            
            # Filter by username if provided
            if username:
                query = query.where('username', '==', username)
            
            # Order by upload date and limit
            query = query.order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Firestore read error: {e}")
            raise
    
    def save_download_record(self, user_id: str, username: str, media_count: int, 
                           total_size: int, resolution_filter: int, method: str, files: list):
        """Save download record to Firestore"""
        try:
            doc_data = {
                'user_id': user_id,
                'username': username,
                'downloaded_at': firestore.SERVER_TIMESTAMP,
                'media_count': media_count,
                'total_size': total_size,
                'resolution_filter': resolution_filter,
                'method': method,
                'status': 'completed',
                'files': files
            }
            
            doc_ref = self.db.collection('downloads').add(doc_data)
            print(f"Download record saved: {doc_ref[1].id}")
            return doc_ref[1].id
            
        except Exception as e:
            print(f"Download record save error: {e}")
            raise
    
    def save_account_info(self, account_data: dict, discovered_by: str = None):
        """Save Instagram account information"""
        try:
            doc_data = {
                'username': account_data.get('username'),
                'display_name': account_data.get('display_name', ''),
                'biography': account_data.get('biography', ''),
                'followers_count': account_data.get('followers_count', 0),
                'following_count': account_data.get('following_count', 0),
                'posts_count': account_data.get('posts_count', 0),
                'is_verified': account_data.get('is_verified', False),
                'is_private': account_data.get('is_private', False),
                'profile_image_url': account_data.get('profile_image_url', ''),
                'external_url': account_data.get('external_url', ''),
                'category': account_data.get('category', ''),
                'discovered_at': firestore.SERVER_TIMESTAMP,
                'discovered_by': discovered_by,
                'last_scraped_at': firestore.SERVER_TIMESTAMP,
                'scrape_count': 1,
                'tags': account_data.get('tags', [])
            }
            
            # Use username as document ID
            doc_ref = self.db.collection('accounts').document(account_data.get('username')).set(doc_data)
            print(f"Account info saved: {account_data.get('username')}")
            return account_data.get('username')
            
        except Exception as e:
            print(f"Account info save error: {e}")
            raise
    
    def get_user_downloads(self, user_id: str, limit: int = 20):
        """Get user's download history"""
        try:
            docs = self.db.collection('downloads')\
                .where('user_id', '==', user_id)\
                .order_by('downloaded_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Get user downloads error: {e}")
            raise
