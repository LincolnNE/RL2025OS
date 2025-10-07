#!/usr/bin/env python3
"""
Instagram Basic Display API tool for fetching user posts
"""

import requests
import json
import os
import time
from urllib.parse import urlencode
from typing import Dict, List, Optional
import argparse
from datetime import datetime
from config.firebase_config import FirebaseManager

class InstagramAPI:
    def __init__(self, access_token: str):
        """
        Initialize Instagram API client
        
        Args:
            access_token: Instagram Basic Display API access token
        """
        self.access_token = access_token
        self.base_url = "https://graph.instagram.com"
        self.api_version = "v18.0"
        
    def get_user_info(self) -> Dict:
        """Get user basic information"""
        url = f"{self.base_url}/{self.api_version}/me"
        params = {
            'fields': 'id,username,account_type,media_count',
            'access_token': self.access_token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_user_media(self, limit: int = 25, after: Optional[str] = None) -> Dict:
        """
        Get user media list
        
        Args:
            limit: Number of media to fetch (max 25)
            after: Pagination cursor
            
        Returns:
            Media data and pagination information
        """
        url = f"{self.base_url}/{self.api_version}/me/media"
        params = {
            'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp',
            'limit': limit,
            'access_token': self.access_token
        }
        
        if after:
            params['after'] = after
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_media_details(self, media_id: str) -> Dict:
        """Get detailed information for specific media"""
        url = f"{self.base_url}/{self.api_version}/{media_id}"
        params = {
            'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,children',
            'access_token': self.access_token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def download_media(self, media_url: str, filename: str, download_dir: str = "downloads") -> str:
        """
        Download media file
        
        Args:
            media_url: Media URL to download
            filename: Filename to save
            download_dir: Download directory
            
        Returns:
            Path to downloaded file
        """
        os.makedirs(download_dir, exist_ok=True)
        
        response = requests.get(media_url)
        response.raise_for_status()
        
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        return file_path
    
    def upload_to_firebase(self, media_data: Dict, local_file_path: str, firebase_manager: FirebaseManager) -> str:
        """
        Upload image to Firebase Storage and save metadata to Firestore
        
        Args:
            media_data: Instagram media data
            local_file_path: Local file path
            firebase_manager: Firebase manager instance
            
        Returns:
            Firebase download URL
        """
        try:
            # Generate remote path
            media_id = media_data.get('id')
            file_extension = local_file_path.split('.')[-1]
            remote_path = f"instagram_media/{media_id}.{file_extension}"
            
            # Upload to Firebase Storage
            download_url = firebase_manager.upload_image(local_file_path, remote_path)
            
            # Save metadata to Firestore
            firebase_manager.save_media_metadata(media_data, download_url)
            
            return download_url
            
        except Exception as e:
            print(f"Firebase upload error: {e}")
            raise
    
    def get_all_media(self, max_posts: int = 100) -> List[Dict]:
        """
        Get all media through pagination
        
        Args:
            max_posts: Maximum number of posts to fetch
            
        Returns:
            List of all media data
        """
        all_media = []
        after = None
        
        while len(all_media) < max_posts:
            remaining = max_posts - len(all_media)
            limit = min(25, remaining)  # API maximum limit
            
            try:
                response = self.get_user_media(limit=limit, after=after)
                media_data = response.get('data', [])
                
                if not media_data:
                    break
                    
                all_media.extend(media_data)
                
                # Check if there's a next page
                paging = response.get('paging', {})
                after = paging.get('cursors', {}).get('after')
                
                if not after:
                    break
                    
                # Wait for API rate limiting
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"API request error: {e}")
                break
                
        return all_media[:max_posts]

def save_media_data(media_list: List[Dict], filename: str = "instagram_media.json"):
    """Save media data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(media_list, f, ensure_ascii=False, indent=2)
    print(f"Media data saved to {filename}.")

def main():
    parser = argparse.ArgumentParser(description='Instagram post fetcher tool')
    parser.add_argument('--token', required=True, help='Instagram access token')
    parser.add_argument('--limit', type=int, default=25, help='Number of posts to fetch (default: 25)')
    parser.add_argument('--download', action='store_true', help='Download images locally')
    parser.add_argument('--firebase', action='store_true', help='Upload to Firebase Storage')
    parser.add_argument('--output', default='instagram_media.json', help='Output JSON filename')
    
    args = parser.parse_args()
    
    try:
        # Create Instagram API client
        api = InstagramAPI(args.token)
        
        # Initialize Firebase if needed
        firebase_manager = None
        if args.firebase:
            print("Initializing Firebase...")
            firebase_manager = FirebaseManager()
        
        # Get user information
        print("Fetching user information...")
        user_info = api.get_user_info()
        print(f"User: {user_info.get('username')} (ID: {user_info.get('id')})")
        print(f"Account type: {user_info.get('account_type')}")
        print(f"Media count: {user_info.get('media_count')}")
        print()
        
        # Get media data
        print(f"Fetching up to {args.limit} posts...")
        media_list = api.get_all_media(max_posts=args.limit)
        
        if not media_list:
            print("No posts to fetch.")
            return
            
        print(f"Fetched {len(media_list)} posts.")
        
        # Save media data
        save_media_data(media_list, args.output)
        
        # Download images (optional)
        if args.download or args.firebase:
            print("\nProcessing images...")
            download_count = 0
            firebase_count = 0
            
            for i, media in enumerate(media_list):
                media_type = media.get('media_type')
                media_url = media.get('media_url')
                
                if media_type in ['IMAGE', 'CAROUSEL_ALBUM'] and media_url:
                    # Generate filename
                    timestamp = media.get('timestamp', '')
                    if timestamp:
                        date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y%m%d_%H%M%S')
                    else:
                        date_str = f"post_{i+1}"
                    
                    file_extension = media_url.split('.')[-1].split('?')[0]
                    filename = f"{date_str}.{file_extension}"
                    
                    try:
                        # Download locally if requested
                        if args.download:
                            file_path = api.download_media(media_url, filename)
                            print(f"Download completed: {file_path}")
                            download_count += 1
                        
                        # Upload to Firebase if requested
                        if args.firebase and firebase_manager:
                            # Download temporarily if not already downloaded
                            if not args.download:
                                file_path = api.download_media(media_url, filename, "temp_downloads")
                            
                            firebase_url = api.upload_to_firebase(media, file_path, firebase_manager)
                            print(f"Firebase upload completed: {firebase_url}")
                            firebase_count += 1
                            
                            # Clean up temp file if not keeping local copy
                            if not args.download and os.path.exists(file_path):
                                os.remove(file_path)
                                
                    except Exception as e:
                        print(f"Processing failed: {filename} - {e}")
                        
            if args.download:
                print(f"\nTotal {download_count} images downloaded locally.")
            if args.firebase:
                print(f"Total {firebase_count} images uploaded to Firebase.")
        
        # Display post summary
        print("\n=== Post Summary ===")
        for i, media in enumerate(media_list[:5]):  # Show only first 5
            caption = media.get('caption', '')[:50] + '...' if media.get('caption') and len(media.get('caption', '')) > 50 else media.get('caption', 'No caption')
            media_type = media.get('media_type')
            timestamp = media.get('timestamp', '')
            
            print(f"{i+1}. [{media_type}] {caption}")
            if timestamp:
                date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                print(f"   Date: {date_str}")
            print()
            
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
