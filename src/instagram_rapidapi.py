#!/usr/bin/env python3
"""
Instagram posts fetcher using RapidAPI services
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
import argparse
from datetime import datetime
try:
    from .firebase_config import FirebaseManager
except ImportError:
    # For direct execution
    import sys
    sys.path.append('.')
    from src.firebase_config import FirebaseManager
from PIL import Image
import io

class InstagramRapidAPI:
    def __init__(self, api_key: str):
        """Initialize Instagram RapidAPI client"""
        self.api_key = api_key
        self.base_url = "https://instagram-scraper21.p.rapidapi.com/api/v1"
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'instagram-scraper21.p.rapidapi.com'
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_profile_info(self, username: str) -> Dict:
        """Get profile information"""
        try:
            # Use the exact endpoint from the screenshot
            url = f"{self.base_url}/user-stories"
            params = {'id': '305701719'}  # Test with the ID from screenshot
            
            response = requests.get(url, headers=self.headers, params=params)
            
            print(f"Trying {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response data: {json.dumps(data, indent=2)[:500]}...")
                
                # For now, return basic info since we're testing
                return {
                    'id': '305701719',
                    'username': username,
                    'full_name': username,
                    'biography': '',
                    'followers_count': 0,
                    'following_count': 0,
                    'posts_count': 0,
                    'is_private': False,
                    'is_verified': False,
                    'profile_pic_url': ''
                }
            else:
                print(f"Failed: {response.status_code} - {response.text[:200]}")
                return {}
                
        except Exception as e:
            print(f"Error getting profile info: {e}")
            return {}
    
    def get_posts(self, username: str, max_posts: int = 12) -> List[Dict]:
        """Get posts from a user's profile"""
        try:
            # For testing, return mock data
            print("Returning mock posts for testing...")
            
            mock_posts = [
                {
                    'id': 'test_post_1',
                    'shortcode': 'test123',
                    'caption': 'Test post 1 - This is a sample Instagram post for testing purposes.',
                    'image_url': 'https://picsum.photos/1200/1200?random=1',
                    'likes_count': 150,
                    'comments_count': 25,
                    'timestamp': datetime.now().isoformat(),
                    'permalink': 'https://www.instagram.com/p/test123/',
                    'media_type': 1
                },
                {
                    'id': 'test_post_2',
                    'shortcode': 'test456',
                    'caption': 'Test post 2 - Another sample post with different content.',
                    'image_url': 'https://picsum.photos/1200/1200?random=2',
                    'likes_count': 89,
                    'comments_count': 12,
                    'timestamp': datetime.now().isoformat(),
                    'permalink': 'https://www.instagram.com/p/test456/',
                    'media_type': 1
                },
                {
                    'id': 'test_post_3',
                    'shortcode': 'test789',
                    'caption': 'Test post 3 - Low resolution image for testing.',
                    'image_url': 'https://picsum.photos/400/400?random=3',
                    'likes_count': 50,
                    'comments_count': 5,
                    'timestamp': datetime.now().isoformat(),
                    'permalink': 'https://www.instagram.com/p/test789/',
                    'media_type': 1
                }
            ]
            
            return mock_posts[:max_posts]
                
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []
    
    def get_image_dimensions(self, image_url: str) -> tuple:
        """Get image dimensions from URL"""
        try:
            response = self.session.head(image_url, allow_redirects=True)
            
            # Try to get dimensions from response headers
            if 'content-length' in response.headers:
                # For some URLs, we might get dimensions in headers
                pass
            
            # Download image to check dimensions
            response = self.session.get(image_url)
            response.raise_for_status()
            
            from PIL import Image
            import io
            
            # Open image from bytes
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            
            return width, height
            
        except Exception as e:
            print(f"Error getting image dimensions: {e}")
            return 0, 0
    
    def download_image(self, image_url: str, filename: str, download_dir: str = "downloads", min_resolution: int = 800) -> str:
        """Download image from URL with resolution filtering"""
        os.makedirs(download_dir, exist_ok=True)
        
        # Check image dimensions first
        width, height = self.get_image_dimensions(image_url)
        
        if width < min_resolution or height < min_resolution:
            raise Exception(f"Image resolution too low: {width}x{height} (minimum: {min_resolution}px)")
        
        print(f"Image resolution OK: {width}x{height}")
        
        response = requests.get(image_url)
        response.raise_for_status()
        
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        return file_path
    
    def upload_to_firebase(self, post_data: Dict, local_file_path: str, firebase_manager: FirebaseManager) -> str:
        """Upload image to Firebase Storage and save metadata to Firestore"""
        try:
            # Generate remote path
            post_id = post_data.get('id', 'unknown')
            file_extension = local_file_path.split('.')[-1]
            remote_path = f"instagram_rapidapi/{post_id}.{file_extension}"
            
            # Upload to Firebase Storage
            download_url = firebase_manager.upload_image(local_file_path, remote_path)
            
            # Save metadata to Firestore
            firebase_manager.save_media_metadata(post_data, download_url)
            
            return download_url
            
        except Exception as e:
            print(f"Firebase upload error: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Instagram posts fetcher using RapidAPI')
    parser.add_argument('--username', required=True, help='Instagram username (without @)')
    parser.add_argument('--limit', type=int, default=12, help='Number of posts to fetch (default: 12)')
    parser.add_argument('--download', action='store_true', help='Download images locally')
    parser.add_argument('--firebase', action='store_true', help='Upload to Firebase Storage')
    parser.add_argument('--output', default='rapidapi_posts.json', help='Output JSON filename')
    parser.add_argument('--api-key', help='RapidAPI key (or set RAPIDAPI_KEY env var)')
    parser.add_argument('--min-resolution', type=int, default=800, help='Minimum image resolution in pixels (default: 800)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('RAPIDAPI_KEY')
    if not api_key:
        print("Error: RapidAPI key is required. Set RAPIDAPI_KEY environment variable or use --api-key")
        return
    
    try:
        # Initialize API client
        api = InstagramRapidAPI(api_key)
        
        # Initialize Firebase if needed
        firebase_manager = None
        if args.firebase:
            print("Initializing Firebase...")
            firebase_manager = FirebaseManager()
        
        # Get profile information
        print(f"Getting profile information for @{args.username}...")
        profile = api.get_profile_info(args.username)
        
        if not profile:
            print("Failed to get profile information")
            return
        
        print(f"Profile: {profile.get('full_name', 'Unknown')} (@{profile.get('username', 'unknown')})")
        print(f"Followers: {profile.get('followers_count', 0):,}")
        print(f"Following: {profile.get('following_count', 0):,}")
        print(f"Posts: {profile.get('posts_count', 0):,}")
        print(f"Private: {profile.get('is_private', True)}")
        print(f"Verified: {profile.get('is_verified', False)}")
        print()
        
        if profile.get('is_private', True):
            print("This account is private. Cannot access posts.")
            return
        
        # Get posts
        print(f"Fetching up to {args.limit} posts...")
        posts = api.get_posts(args.username, args.limit)
        
        if not posts:
            print("No posts found.")
            return
            
        print(f"Found {len(posts)} posts.")
        
        # Save posts data
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"Posts data saved to {args.output}.")
        
        # Process images
        if args.download or args.firebase:
            print("\nProcessing images...")
            download_count = 0
            firebase_count = 0
            
            for i, post in enumerate(posts):
                image_url = post.get('image_url')
                if not image_url:
                    continue
                
                # Generate filename
                timestamp = post.get('timestamp', '')
                if timestamp:
                    try:
                        date_str = datetime.fromisoformat(timestamp).strftime('%Y%m%d_%H%M%S')
                    except:
                        date_str = f"post_{i+1}"
                else:
                    date_str = f"post_{i+1}"
                
                filename = f"{args.username}_{date_str}.jpg"
                
                try:
                    # Download locally if requested
                    if args.download:
                        file_path = api.download_image(image_url, filename, "downloads", args.min_resolution)
                        print(f"Download completed: {file_path}")
                        download_count += 1
                    
                    # Upload to Firebase if requested
                    if args.firebase and firebase_manager:
                        # Download temporarily if not already downloaded
                        if not args.download:
                            file_path = api.download_image(image_url, filename, "temp_downloads", args.min_resolution)
                        
                        firebase_url = api.upload_to_firebase(post, file_path, firebase_manager)
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
        for i, post in enumerate(posts[:5]):  # Show only first 5
            caption = post.get('caption', '')[:50] + '...' if post.get('caption') and len(post.get('caption', '')) > 50 else post.get('caption', 'No caption')
            likes = post.get('likes_count', 0)
            comments = post.get('comments_count', 0)
            
            print(f"{i+1}. {caption}")
            print(f"   Likes: {likes:,} | Comments: {comments:,}")
            print()
            
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
