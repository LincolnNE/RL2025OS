#!/usr/bin/env python3
"""
Instagram public profile scraper for other users' posts
Note: This is for educational purposes only. Use responsibly and respect Instagram's terms of service.
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
import argparse
from datetime import datetime
from config.firebase_config import FirebaseManager

class InstagramScraper:
    def __init__(self):
        """Initialize Instagram scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_public_profile(self, username: str) -> Dict:
        """
        Get public profile information
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            Profile information
        """
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Try multiple methods to extract data
            content = response.text
            
            # Method 1: Look for window._sharedData
            start = content.find('window._sharedData = ')
            if start != -1:
                start += len('window._sharedData = ')
                end = content.find(';</script>', start)
                if end != -1:
                    json_str = content[start:end]
                    try:
                        data = json.loads(json_str)
                        if 'entry_data' in data and 'ProfilePage' in data['entry_data']:
                            profile_data = data['entry_data']['ProfilePage'][0]['graphql']['user']
                            return self._extract_profile_data(profile_data)
                    except:
                        pass
            
            # Method 2: Look for additionalData
            start = content.find('"additionalData":')
            if start != -1:
                start = content.find('{', start)
                end = content.find('}</script>', start)
                if end != -1:
                    json_str = content[start:end+1]
                    try:
                        data = json.loads(json_str)
                        if 'user' in data:
                            return self._extract_profile_data(data['user'])
                    except:
                        pass
            
            # Method 3: Look for __additionalDataLoaded
            start = content.find('__additionalDataLoaded')
            if start != -1:
                start = content.find('{', start)
                end = content.find('}', start)
                if end != -1:
                    json_str = content[start:end+1]
                    try:
                        data = json.loads(json_str)
                        if 'user' in data:
                            return self._extract_profile_data(data['user'])
                    except:
                        pass
            
            raise Exception("Could not extract profile data with any method")
            
        except Exception as e:
            print(f"Error getting profile: {e}")
            raise
    
    def _extract_profile_data(self, profile_data: Dict) -> Dict:
        """Extract profile data from Instagram response"""
        return {
            'id': profile_data.get('id', ''),
            'username': profile_data.get('username', ''),
            'full_name': profile_data.get('full_name', ''),
            'biography': profile_data.get('biography', ''),
            'followers_count': profile_data.get('edge_followed_by', {}).get('count', 0),
            'following_count': profile_data.get('edge_follow', {}).get('count', 0),
            'posts_count': profile_data.get('edge_owner_to_timeline_media', {}).get('count', 0),
            'is_private': profile_data.get('is_private', True),
            'is_verified': profile_data.get('is_verified', False)
        }
    
    def get_public_posts(self, username: str, max_posts: int = 12) -> List[Dict]:
        """
        Get public posts from a user's profile
        
        Args:
            username: Instagram username (without @)
            max_posts: Maximum number of posts to fetch
            
        Returns:
            List of post data
        """
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract JSON data from HTML
            content = response.text
            start = content.find('window._sharedData = ') + len('window._sharedData = ')
            end = content.find(';</script>', start)
            
            if start == -1 or end == -1:
                raise Exception("Could not extract posts data")
            
            json_str = content[start:end]
            data = json.loads(json_str)
            
            posts_data = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
            
            posts = []
            for i, post in enumerate(posts_data[:max_posts]):
                node = post['node']
                
                # Check for carousel (GraphSidecar)
                if node['__typename'] == 'GraphSidecar':
                    # Carousel album - extract all images from children
                    children = node.get('edge_sidecar_to_children', {}).get('edges', [])
                    
                    for idx, child_edge in enumerate(children):
                        child_node = child_edge.get('node', {})
                        
                        # Only process images (skip videos)
                        if child_node.get('__typename') == 'GraphImage':
                            post_data = {
                                'id': f"{node['id']}_{idx}",
                                'shortcode': node['shortcode'],
                                'caption': node['edge_media_to_caption']['edges'][0]['node']['text'] if node['edge_media_to_caption']['edges'] else '',
                                'image_url': child_node.get('display_url', ''),
                                'likes_count': node['edge_liked_by']['count'],
                                'comments_count': node['edge_media_to_comment']['count'],
                                'timestamp': datetime.fromtimestamp(node['taken_at_timestamp']).isoformat(),
                                'permalink': f"https://www.instagram.com/p/{node['shortcode']}/",
                                'media_type': 'carousel',
                                'carousel_index': idx + 1,
                                'carousel_total': len(children)
                            }
                            posts.append(post_data)
                
                # Single image
                elif node['__typename'] == 'GraphImage':
                    image_url = node['display_url']
                    post_data = {
                        'id': node['id'],
                        'shortcode': node['shortcode'],
                        'caption': node['edge_media_to_caption']['edges'][0]['node']['text'] if node['edge_media_to_caption']['edges'] else '',
                        'image_url': image_url,
                        'likes_count': node['edge_liked_by']['count'],
                        'comments_count': node['edge_media_to_comment']['count'],
                        'timestamp': datetime.fromtimestamp(node['taken_at_timestamp']).isoformat(),
                        'permalink': f"https://www.instagram.com/p/{node['shortcode']}/",
                        'media_type': node['__typename']
                    }
                    posts.append(post_data)
                
                # Video (keep single thumbnail)
                elif node['__typename'] == 'GraphVideo':
                    image_url = node['display_url']
                    post_data = {
                        'id': node['id'],
                        'shortcode': node['shortcode'],
                        'caption': node['edge_media_to_caption']['edges'][0]['node']['text'] if node['edge_media_to_caption']['edges'] else '',
                        'image_url': image_url,
                        'likes_count': node['edge_liked_by']['count'],
                        'comments_count': node['edge_media_to_comment']['count'],
                        'timestamp': datetime.fromtimestamp(node['taken_at_timestamp']).isoformat(),
                        'permalink': f"https://www.instagram.com/p/{node['shortcode']}/",
                        'media_type': node['__typename']
                    }
                    posts.append(post_data)
            
            return posts
            
        except Exception as e:
            print(f"Error getting posts: {e}")
            raise
    
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
            post_id = post_data.get('id')
            file_extension = local_file_path.split('.')[-1]
            remote_path = f"instagram_scraped/{post_id}.{file_extension}"
            
            # Upload to Firebase Storage
            download_url = firebase_manager.upload_image(local_file_path, remote_path)
            
            # Save metadata to Firestore
            firebase_manager.save_media_metadata(post_data, download_url)
            
            return download_url
            
        except Exception as e:
            print(f"Firebase upload error: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Instagram public profile scraper')
    parser.add_argument('--username', required=True, help='Instagram username (without @)')
    parser.add_argument('--limit', type=int, default=12, help='Number of posts to fetch (default: 12)')
    parser.add_argument('--download', action='store_true', help='Download images locally')
    parser.add_argument('--firebase', action='store_true', help='Upload to Firebase Storage')
    parser.add_argument('--output', default='scraped_posts.json', help='Output JSON filename')
    
    args = parser.parse_args()
    
    try:
        # Initialize scraper
        scraper = InstagramScraper()
        
        # Initialize Firebase if needed
        firebase_manager = None
        if args.firebase:
            print("Initializing Firebase...")
            firebase_manager = FirebaseManager()
        
        # Get profile information
        print(f"Getting profile information for @{args.username}...")
        profile = scraper.get_public_profile(args.username)
        
        print(f"Profile: {profile['full_name']} (@{profile['username']})")
        print(f"Followers: {profile['followers_count']:,}")
        print(f"Following: {profile['following_count']:,}")
        print(f"Posts: {profile['posts_count']:,}")
        print(f"Private: {profile['is_private']}")
        print(f"Verified: {profile['is_verified']}")
        print()
        
        if profile['is_private']:
            print("This account is private. Cannot access posts.")
            return
        
        # Get posts
        print(f"Fetching up to {args.limit} posts...")
        posts = scraper.get_public_posts(args.username, args.limit)
        
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
                    date_str = datetime.fromisoformat(timestamp).strftime('%Y%m%d_%H%M%S')
                else:
                    date_str = f"post_{i+1}"
                
                # Add carousel index if it's a carousel post
                if post.get('carousel_index'):
                    filename = f"{args.username}_{date_str}_{post.get('carousel_index', '')}.jpg"
                else:
                    filename = f"{args.username}_{date_str}.jpg"
                
                try:
                    # Download locally if requested
                    if args.download:
                        file_path = scraper.download_image(image_url, filename)
                        print(f"Download completed: {file_path}")
                        download_count += 1
                    
                    # Upload to Firebase if requested
                    if args.firebase and firebase_manager:
                        # Download temporarily if not already downloaded
                        if not args.download:
                            file_path = scraper.download_image(image_url, filename, "temp_downloads")
                        
                        firebase_url = scraper.upload_to_firebase(post, file_path, firebase_manager)
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
