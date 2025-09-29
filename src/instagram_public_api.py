#!/usr/bin/env python3
"""
Instagram public posts fetcher using alternative methods
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
import argparse
from datetime import datetime
from firebase_config import FirebaseManager

class InstagramPublicAPI:
    def __init__(self):
        """Initialize Instagram public API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_profile_info(self, username: str) -> Dict:
        """Get basic profile information"""
        try:
            # Try Instagram's public API endpoint
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data['data']['user']
                
                return {
                    'id': user_data.get('id', ''),
                    'username': user_data.get('username', ''),
                    'full_name': user_data.get('full_name', ''),
                    'biography': user_data.get('biography', ''),
                    'followers_count': user_data.get('edge_followed_by', {}).get('count', 0),
                    'following_count': user_data.get('edge_follow', {}).get('count', 0),
                    'posts_count': user_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'is_private': user_data.get('is_private', True),
                    'is_verified': user_data.get('is_verified', False),
                    'profile_pic_url': user_data.get('profile_pic_url_hd', '')
                }
            else:
                raise Exception(f"API request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"Error getting profile info: {e}")
            # Fallback to basic info
            return {
                'username': username,
                'full_name': username,
                'is_private': True,
                'posts_count': 0
            }
    
    def get_public_posts(self, username: str, max_posts: int = 12) -> List[Dict]:
        """Get public posts from a user's profile"""
        try:
            # Try Instagram's public API endpoint
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data['data']['user']
                
                if user_data.get('is_private', True):
                    print("This account is private. Cannot access posts.")
                    return []
                
                posts_data = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                
                posts = []
                for i, post in enumerate(posts_data[:max_posts]):
                    node = post['node']
                    
                    # Get image URL
                    if node.get('__typename') == 'GraphImage':
                        image_url = node.get('display_url', '')
                    elif node.get('__typename') == 'GraphVideo':
                        image_url = node.get('display_url', '')
                    elif node.get('__typename') == 'GraphSidecar':
                        image_url = node.get('display_url', '')
                    else:
                        continue
                    
                    if not image_url:
                        continue
                    
                    # Get caption
                    caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                    caption = caption_edges[0]['node']['text'] if caption_edges else ''
                    
                    post_data = {
                        'id': node.get('id', ''),
                        'shortcode': node.get('shortcode', ''),
                        'caption': caption,
                        'image_url': image_url,
                        'likes_count': node.get('edge_liked_by', {}).get('count', 0),
                        'comments_count': node.get('edge_media_to_comment', {}).get('count', 0),
                        'timestamp': datetime.fromtimestamp(node.get('taken_at_timestamp', 0)).isoformat(),
                        'permalink': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                        'media_type': node.get('__typename', '')
                    }
                    
                    posts.append(post_data)
                
                return posts
            else:
                print(f"API request failed with status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []
    
    def download_image(self, image_url: str, filename: str, download_dir: str = "downloads") -> str:
        """Download image from URL"""
        os.makedirs(download_dir, exist_ok=True)
        
        response = self.session.get(image_url)
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
            remote_path = f"instagram_public/{post_id}.{file_extension}"
            
            # Upload to Firebase Storage
            download_url = firebase_manager.upload_image(local_file_path, remote_path)
            
            # Save metadata to Firestore
            firebase_manager.save_media_metadata(post_data, download_url)
            
            return download_url
            
        except Exception as e:
            print(f"Firebase upload error: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Instagram public posts fetcher')
    parser.add_argument('--username', required=True, help='Instagram username (without @)')
    parser.add_argument('--limit', type=int, default=12, help='Number of posts to fetch (default: 12)')
    parser.add_argument('--download', action='store_true', help='Download images locally')
    parser.add_argument('--firebase', action='store_true', help='Upload to Firebase Storage')
    parser.add_argument('--output', default='public_posts.json', help='Output JSON filename')
    
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api = InstagramPublicAPI()
        
        # Initialize Firebase if needed
        firebase_manager = None
        if args.firebase:
            print("Initializing Firebase...")
            firebase_manager = FirebaseManager()
        
        # Get profile information
        print(f"Getting profile information for @{args.username}...")
        profile = api.get_profile_info(args.username)
        
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
        posts = api.get_public_posts(args.username, args.limit)
        
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
                        file_path = api.download_image(image_url, filename)
                        print(f"Download completed: {file_path}")
                        download_count += 1
                    
                    # Upload to Firebase if requested
                    if args.firebase and firebase_manager:
                        # Download temporarily if not already downloaded
                        if not args.download:
                            file_path = api.download_image(image_url, filename, "temp_downloads")
                        
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
