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
    from config.firebase_config import FirebaseManager
except ImportError:
    # For direct execution
    import sys
    sys.path.append('.')
    from config.firebase_config import FirebaseManager
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
        """Get posts from a user's profile with enhanced content types"""
        try:
            print(f"🔍 Trying RapidAPI Instagram Scraper for @{username}...")
            
            # Enhanced RapidAPI endpoints - trying all possible content types
            endpoints_to_try = [
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_info',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'username_or_id_or_url': username}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_posts',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'username_or_id_or_url': username, 'count': str(max_posts)}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_full_posts',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'username_or_id_or_url': username, 'count': str(max_posts)}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_stories',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'id': username}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_reels',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'username_or_id_or_url': username, 'count': str(max_posts)}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/user_igtv',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'username_or_id_or_url': username, 'count': str(max_posts)}
                },
                {
                    'url': 'https://instagram-scraper21.p.rapidapi.com/api/v1/post_info',
                    'host': 'instagram-scraper21.p.rapidapi.com',
                    'params': {'shortcode': username}
                }
            ]
            
            # Try with different usernames (remove @ if present)
            usernames_to_try = [username, username.replace('@', '')]
            
            # Try multiple times with different parameters - more conservative approach
            for attempt in range(2):  # Reduce attempts to avoid rate limiting
                print(f"🔄 RapidAPI attempt {attempt + 1}/2...")
                
                # Only try most reliable endpoints first
                reliable_endpoints = endpoints_to_try[:3]  # Only user_info, user_posts, user_full_posts
                
                for username_var in usernames_to_try:
                    for endpoint in reliable_endpoints:
                        try:
                            headers = {
                                'X-RapidAPI-Key': self.api_key,
                                'X-RapidAPI-Host': endpoint['host'],
                                'X-RapidAPI-Proxy-Secret': 'optional-proxy-secret',
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                            }
                            
                            # Update params with current username
                            params = endpoint['params'].copy()
                            if 'username_or_id_or_url' in params:
                                params['username_or_id_or_url'] = username_var
                            if 'hashtag' in params:
                                params['hashtag'] = username_var
                            
                            print(f"🔄 Trying {endpoint['url']} with username '{username_var}'...")
                            response = requests.get(endpoint['url'], headers=headers, params=params, timeout=30)
                            
                            print(f"📊 Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                print(f"✅ Success! Got data: {json.dumps(data, indent=2)[:300]}...")
                                
                                # Parse different response formats
                                posts = []
                                
                                # Check if it's user_posts format
                                if 'data' in data and isinstance(data['data'], list):
                                    for post_data in data['data'][:max_posts]:
                                        # Check for carousel (multiple images in one post)
                                        if post_data.get('children') or post_data.get('edge_sidecar_to_children'):
                                            # Carousel album - extract all images
                                            children = post_data.get('children', {}).get('data', []) or post_data.get('edge_sidecar_to_children', {}).get('edges', [])
                                            
                                            for idx, child in enumerate(children):
                                                # Handle different child formats
                                                child_node = child.get('node', child)
                                                
                                                # Process both images and videos
                                                media_type = child_node.get('media_type', child_node.get('__typename', ''))
                                                is_image = (media_type in [1, 'IMAGE', 'GraphImage'])
                                                is_video = (media_type in [2, 'VIDEO', 'GraphVideo'])
                                                
                                                if is_image or is_video:
                                                    # Get media URL (video thumbnail or image)
                                                    media_url = child_node.get('display_url', child_node.get('media_url', child_node.get('image_url', '')))
                                                    video_url = child_node.get('video_url', '') if is_video else ''
                                                    
                                                    posts.append({
                                                        'id': f"{post_data.get('id', '')}_{idx}",
                                                        'shortcode': post_data.get('shortcode', ''),
                                                        'caption': post_data.get('caption', ''),
                                                        'image_url': media_url,  # Thumbnail for videos
                                                        'video_url': video_url,  # Video URL if available
                                                        'likes_count': post_data.get('like_count', 0),
                                                        'comments_count': post_data.get('comment_count', 0),
                                                        'timestamp': post_data.get('taken_at_timestamp', ''),
                                                        'permalink': f"https://www.instagram.com/p/{post_data.get('shortcode', '')}/",
                                                        'media_type': 'carousel_video' if is_video else 'carousel',
                                                        'content_type': 'video' if is_video else 'image',
                                                        'carousel_index': idx + 1,
                                                        'carousel_total': len(children),
                                                        'duration': child_node.get('video_duration', 0) if is_video else None,
                                                        'view_count': child_node.get('video_view_count', 0) if is_video else None
                                                    })
                                        elif post_data.get('media_type') in [1, 2]:  # Single image or video post
                                            media_type = post_data.get('media_type')
                                            is_video = (media_type == 2)
                                            
                                            posts.append({
                                                'id': post_data.get('id', ''),
                                                'shortcode': post_data.get('shortcode', ''),
                                                'caption': post_data.get('caption', ''),
                                                'image_url': post_data.get('display_url', post_data.get('image_url', '')),  # Thumbnail for videos
                                                'video_url': post_data.get('video_url', '') if is_video else '',
                                                'likes_count': post_data.get('like_count', 0),
                                                'comments_count': post_data.get('comment_count', 0),
                                                'timestamp': post_data.get('taken_at_timestamp', ''),
                                                'permalink': f"https://www.instagram.com/p/{post_data.get('shortcode', '')}/",
                                                'media_type': media_type,
                                                'content_type': 'video' if is_video else 'image',
                                                'duration': post_data.get('video_duration', 0) if is_video else None,
                                                'view_count': post_data.get('video_view_count', 0) if is_video else None
                                            })
                                
                                # Check if it's user_info format
                                elif 'data' in data and 'edge_owner_to_timeline_media' in data['data']:
                                    edges = data['data']['edge_owner_to_timeline_media']['edges'][:max_posts]
                                    for edge in edges:
                                        node = edge['node']
                                        
                                        # Check for carousel (GraphSidecar)
                                        if node.get('__typename') == 'GraphSidecar':
                                            # Carousel album - extract all images from children
                                            children = node.get('edge_sidecar_to_children', {}).get('edges', [])
                                            
                                            for idx, child_edge in enumerate(children):
                                                child_node = child_edge.get('node', {})
                                                
                                                # Only process images (skip videos)
                                                if child_node.get('__typename') == 'GraphImage':
                                                    posts.append({
                                                        'id': f"{node.get('id', '')}_{idx}",
                                                        'shortcode': node.get('shortcode', ''),
                                                        'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                                                        'image_url': child_node.get('display_url', ''),
                                                        'likes_count': node.get('edge_liked_by', {}).get('count', 0),
                                                        'comments_count': node.get('edge_media_to_comment', {}).get('count', 0),
                                                        'timestamp': node.get('taken_at_timestamp', ''),
                                                        'permalink': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                                                        'media_type': 'carousel',
                                                        'carousel_index': idx + 1,
                                                        'carousel_total': len(children)
                                                    })
                                        elif node.get('__typename') == 'GraphImage':
                                            # Single image
                                            posts.append({
                                                'id': node.get('id', ''),
                                                'shortcode': node.get('shortcode', ''),
                                                'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                                                'image_url': node.get('display_url', ''),
                                                'likes_count': node.get('edge_liked_by', {}).get('count', 0),
                                                'comments_count': node.get('edge_media_to_comment', {}).get('count', 0),
                                                'timestamp': node.get('taken_at_timestamp', ''),
                                                'permalink': f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                                                'media_type': 1
                                            })
                                
                                if posts:
                                    print(f"🎉 Found {len(posts)} posts from RapidAPI!")
                                    return posts
                                else:
                                    print(f"⚠️ No posts found in response format")
                            
                            elif response.status_code == 403:
                                print(f"❌ Access forbidden - trying next endpoint...")
                                continue
                            elif response.status_code == 429:
                                print(f"⏳ Rate limited - waiting 15 seconds...")
                                time.sleep(15)
                                continue
                            else:
                                print(f"❌ Failed with status {response.status_code}: {response.text[:200]}")
                                continue
                                
                        except requests.exceptions.Timeout:
                            print(f"⏰ Timeout for {endpoint['url']} - trying next...")
                            continue
                        except Exception as e:
                            print(f"❌ Error with {endpoint['url']}: {e}")
                            continue
                
                # Wait between attempts
                if attempt < 1:
                    print(f"⏳ Waiting 20 seconds before next attempt...")
                    time.sleep(20)
            
            print(f"❌ All RapidAPI endpoints failed for @{username}")
            return []
                
        except Exception as e:
            print(f"❌ Error getting posts: {e}")
            return []
    
    def get_stories(self, username: str) -> List[Dict]:
        """Get user stories"""
        try:
            print(f"📖 Getting stories for @{username}...")
            
            url = "https://instagram-scraper21.p.rapidapi.com/api/v1/user_stories"
            params = {'id': username}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                stories = []
                
                if 'data' in data and isinstance(data['data'], list):
                    for story in data['data']:
                        stories.append({
                            'id': story.get('id', ''),
                            'shortcode': story.get('shortcode', ''),
                            'caption': story.get('caption', ''),
                            'image_url': story.get('display_url', story.get('thumbnail_url', '')),
                            'video_url': story.get('video_url', ''),
                            'timestamp': story.get('taken_at_timestamp', ''),
                            'media_type': 'story',
                            'content_type': 'video' if story.get('video_url') else 'image',
                            'duration': story.get('video_duration', 0),
                            'view_count': story.get('view_count', 0),
                            'expires_at': story.get('expires_at', '')
                        })
                
                print(f"✅ Found {len(stories)} stories")
                return stories
            else:
                print(f"❌ Stories API failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting stories: {e}")
            return []
    
    def get_reels(self, username: str, max_posts: int = 12) -> List[Dict]:
        """Get user reels"""
        try:
            print(f"🎬 Getting reels for @{username}...")
            
            url = "https://instagram-scraper21.p.rapidapi.com/api/v1/user_reels"
            params = {'username_or_id_or_url': username, 'count': str(max_posts)}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                reels = []
                
                if 'data' in data and isinstance(data['data'], list):
                    for reel in data['data']:
                        reels.append({
                            'id': reel.get('id', ''),
                            'shortcode': reel.get('shortcode', ''),
                            'caption': reel.get('caption', ''),
                            'image_url': reel.get('display_url', reel.get('thumbnail_url', '')),
                            'video_url': reel.get('video_url', ''),
                            'likes_count': reel.get('like_count', 0),
                            'comments_count': reel.get('comment_count', 0),
                            'timestamp': reel.get('taken_at_timestamp', ''),
                            'permalink': f"https://www.instagram.com/reel/{reel.get('shortcode', '')}/",
                            'media_type': 'reel',
                            'content_type': 'video',
                            'duration': reel.get('video_duration', 0),
                            'view_count': reel.get('play_count', 0),
                            'music_info': reel.get('music_info', {}),
                            'is_reel': True
                        })
                
                print(f"✅ Found {len(reels)} reels")
                return reels
            else:
                print(f"❌ Reels API failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting reels: {e}")
            return []
    
    def get_igtv(self, username: str, max_posts: int = 12) -> List[Dict]:
        """Get user IGTV videos"""
        try:
            print(f"📺 Getting IGTV for @{username}...")
            
            url = "https://instagram-scraper21.p.rapidapi.com/api/v1/user_igtv"
            params = {'username_or_id_or_url': username, 'count': str(max_posts)}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                igtv_videos = []
                
                if 'data' in data and isinstance(data['data'], list):
                    for video in data['data']:
                        igtv_videos.append({
                            'id': video.get('id', ''),
                            'shortcode': video.get('shortcode', ''),
                            'caption': video.get('caption', ''),
                            'image_url': video.get('display_url', video.get('thumbnail_url', '')),
                            'video_url': video.get('video_url', ''),
                            'likes_count': video.get('like_count', 0),
                            'comments_count': video.get('comment_count', 0),
                            'timestamp': video.get('taken_at_timestamp', ''),
                            'permalink': f"https://www.instagram.com/tv/{video.get('shortcode', '')}/",
                            'media_type': 'igtv',
                            'content_type': 'video',
                            'duration': video.get('video_duration', 0),
                            'view_count': video.get('play_count', 0),
                            'is_igtv': True
                        })
                
                print(f"✅ Found {len(igtv_videos)} IGTV videos")
                return igtv_videos
            else:
                print(f"❌ IGTV API failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting IGTV: {e}")
            return []
    
    def get_all_content(self, username: str, max_posts: int = 12) -> Dict[str, List[Dict]]:
        """Get all content types for a user"""
        try:
            print(f"🎯 Getting all content for @{username}...")
            
            all_content = {
                'posts': [],
                'stories': [],
                'reels': [],
                'igtv': []
            }
            
            # Get regular posts
            all_content['posts'] = self.get_posts(username, max_posts)
            
            # Get stories
            all_content['stories'] = self.get_stories(username)
            
            # Get reels
            all_content['reels'] = self.get_reels(username, max_posts)
            
            # Get IGTV
            all_content['igtv'] = self.get_igtv(username, max_posts)
            
            total_items = sum(len(content) for content in all_content.values())
            print(f"🎉 Total content found: {total_items} items")
            
            return all_content
            
        except Exception as e:
            print(f"❌ Error getting all content: {e}")
            return {'posts': [], 'stories': [], 'reels': [], 'igtv': []}

    def enhance_image_url_quality(self, image_url: str) -> str:
        """Enhance Instagram image URL to get higher quality"""
        try:
            if 'scontent' not in image_url or 'instagram.com' not in image_url:
                return image_url
            
            # Parse URL parameters
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(image_url)
            query_params = parse_qs(parsed.query)
            
            # Enhance quality parameters
            if 'stp' in query_params:
                # Replace low quality stp parameter with high quality
                stp_value = query_params['stp'][0]
                if 'e15' in stp_value:
                    # Replace e15 (low quality) with e35 (high quality)
                    stp_value = stp_value.replace('e15', 'e35')
                elif 'e35' not in stp_value:
                    # Add e35 if not present
                    stp_value = stp_value.replace('dst-jpg', 'dst-jpg_e35')
                
                query_params['stp'] = [stp_value]
            
            # Add high quality parameters
            if 'efg' not in query_params:
                # Add high quality encoding parameters
                query_params['efg'] = ['eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0uaW1hZ2VfdXJsZ2VuLjE0NDB4MTgwMC5zZHIuZjgyNzg3LmRlZmF1bHRfaW1hZ2UuYzIifQ']
            
            # Rebuild URL
            new_query = urlencode(query_params, doseq=True)
            enhanced_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            
            print(f"🔄 Enhanced image URL quality: {enhanced_url[:100]}...")
            return enhanced_url
            
        except Exception as e:
            print(f"❌ URL enhancement failed: {e}")
            return image_url

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
    
    def download_image(self, image_url: str, filename: str, download_dir: str = "downloads") -> str:
        """Download image from URL with quality enhancement (no resolution filtering)"""
        os.makedirs(download_dir, exist_ok=True)
        
        # Enhance image URL quality first
        enhanced_url = self.enhance_image_url_quality(image_url)
        
        # Download with enhanced quality (always download, no resolution check)
        response = requests.get(enhanced_url)
        response.raise_for_status()
        
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Log file size for comparison
        file_size = os.path.getsize(file_path)
        print(f"✅ Downloaded original image: {file_size:,} bytes")
            
        return file_path
    
    def upload_to_firebase(self, post_data: Dict, local_file_path: str, firebase_manager: FirebaseManager) -> str:
        """Upload media to Firebase Storage and save metadata to Firestore"""
        try:
            # Generate remote path based on content type
            post_id = post_data.get('id', 'unknown')
            content_type = post_data.get('content_type', 'image')
            media_type = post_data.get('media_type', 'post')
            file_extension = local_file_path.split('.')[-1]
            
            # Create organized folder structure
            remote_path = f"instagram_rapidapi/{media_type}/{content_type}/{post_id}.{file_extension}"
            
            # Upload to Firebase Storage
            if content_type == 'video':
                download_url = firebase_manager.upload_video(local_file_path, remote_path)
            else:
                download_url = firebase_manager.upload_image(local_file_path, remote_path)
            
            # Enhanced metadata with all content information
            enhanced_metadata = {
                **post_data,
                'firebase_url': download_url,
                'local_path': local_file_path,
                'upload_timestamp': datetime.now().isoformat(),
                'file_size': os.path.getsize(local_file_path) if os.path.exists(local_file_path) else 0,
                'content_category': media_type,
                'media_source': 'rapidapi'
            }
            
            # Save metadata to Firestore
            firebase_manager.save_media_metadata(enhanced_metadata, download_url)
            
            return download_url
            
        except Exception as e:
            print(f"Firebase upload error: {e}")
            raise
    
    def download_video(self, video_url: str, filename: str, download_dir: str = "downloads") -> str:
        """Download video from URL (always download, no filtering)"""
        try:
            os.makedirs(download_dir, exist_ok=True)
            
            print(f"🎥 Downloading video: {video_url}")
            
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            file_path = os.path.join(download_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            print(f"✅ Video downloaded: {file_size:,} bytes")
            
            return file_path
            
        except Exception as e:
            print(f"❌ Video download error: {e}")
            raise
    
    def process_and_upload_content(self, content_data: Dict, username: str, download_dir: str = "downloads", 
                                 firebase_manager: FirebaseManager = None, upload_to_firebase: bool = False) -> List[Dict]:
        """Process and upload all content types (images, videos, etc.)"""
        try:
            processed_items = []
            
            # Process different content types
            for content_type, items in content_data.items():
                if not items:
                    continue
                    
                print(f"🔄 Processing {len(items)} {content_type} items...")
                
                for i, item in enumerate(items):
                    try:
                        # Determine media URL and type
                        media_url = item.get('image_url', '') or item.get('video_url', '')
                        is_video = item.get('content_type') == 'video' and item.get('video_url')
                        
                        if not media_url:
                            continue
                        
                        # Generate filename
                        timestamp = item.get('timestamp', '')
                        if timestamp:
                            try:
                                date_str = datetime.fromtimestamp(int(timestamp)).strftime('%Y%m%d_%H%M%S')
                            except:
                                date_str = f"item_{i+1}"
                        else:
                            date_str = f"item_{i+1}"
                        
                        # Create filename with content type prefix
                        if item.get('carousel_index'):
                            filename = f"{username}_{content_type}_{date_str}_{item.get('carousel_index', '')}"
                        else:
                            filename = f"{username}_{content_type}_{date_str}"
                        
                        # Add appropriate extension
                        if is_video:
                            filename += ".mp4"
                        else:
                            filename += ".jpg"
                        
                        # Download media (always download, no filtering)
                        if is_video:
                            local_path = self.download_video(media_url, filename, download_dir)
                        else:
                            local_path = self.download_image(media_url, filename, download_dir)
                        
                        # Upload to Firebase if requested
                        firebase_url = None
                        if upload_to_firebase and firebase_manager:
                            try:
                                firebase_url = self.upload_to_firebase(item, local_path, firebase_manager)
                                print(f"🔥 Firebase upload successful: {firebase_url}")
                            except Exception as e:
                                print(f"❌ Firebase upload failed: {e}")
                        
                        processed_item = {
                            **item,
                            'local_path': local_path,
                            'firebase_url': firebase_url,
                            'processed': True,
                            'content_type': content_type
                        }
                        
                        processed_items.append(processed_item)
                        
                    except Exception as e:
                        print(f"❌ Processing failed for {content_type} item {i+1}: {e}")
                        continue
            
            print(f"✅ Successfully processed {len(processed_items)} items")
            return processed_items
            
        except Exception as e:
            print(f"❌ Error processing content: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='Enhanced Instagram content fetcher using RapidAPI')
    parser.add_argument('--username', required=True, help='Instagram username (without @)')
    parser.add_argument('--limit', type=int, default=12, help='Number of posts to fetch (default: 12)')
    parser.add_argument('--download', action='store_true', help='Download media locally')
    parser.add_argument('--firebase', action='store_true', help='Upload to Firebase Storage')
    parser.add_argument('--output', default='rapidapi_content.json', help='Output JSON filename')
    parser.add_argument('--api-key', help='RapidAPI key (or set RAPIDAPI_KEY env var)')
    parser.add_argument('--min-resolution', type=int, default=800, help='Minimum image resolution in pixels (default: 800)')
    parser.add_argument('--content-types', nargs='+', 
                       choices=['posts', 'stories', 'reels', 'igtv', 'all'], 
                       default=['posts'], 
                       help='Content types to fetch (default: posts)')
    parser.add_argument('--include-videos', action='store_true', help='Include video downloads (if available)')
    
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
        
        # Get content based on requested types
        print(f"Fetching content for @{args.username}...")
        
        if 'all' in args.content_types:
            # Get all content types
            content_data = api.get_all_content(args.username, args.limit)
        else:
            # Get specific content types
            content_data = {
                'posts': [],
                'stories': [],
                'reels': [],
                'igtv': []
            }
            
            if 'posts' in args.content_types:
                content_data['posts'] = api.get_posts(args.username, args.limit)
            if 'stories' in args.content_types:
                content_data['stories'] = api.get_stories(args.username)
            if 'reels' in args.content_types:
                content_data['reels'] = api.get_reels(args.username, args.limit)
            if 'igtv' in args.content_types:
                content_data['igtv'] = api.get_igtv(args.username, args.limit)
        
        # Count total items
        total_items = sum(len(items) for items in content_data.values())
        if total_items == 0:
            print("No content found.")
            return
            
        print(f"Found {total_items} total items:")
        for content_type, items in content_data.items():
            if items:
                print(f"  - {content_type}: {len(items)} items")
        
        # Save content data
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)
        print(f"Content data saved to {args.output}.")
        
        # Process and upload content
        if args.download or args.firebase:
            print("\nProcessing and uploading content...")
            
            # Use the new enhanced processing method
            processed_items = api.process_and_upload_content(
                content_data, 
                args.username, 
                "downloads", 
                firebase_manager, 
                args.firebase
            )
            
            # Summary
            download_count = len([item for item in processed_items if item.get('local_path')])
            firebase_count = len([item for item in processed_items if item.get('firebase_url')])
            
            if args.download:
                print(f"\n✅ Total {download_count} media files downloaded locally.")
            if args.firebase:
                print(f"🔥 Total {firebase_count} media files uploaded to Firebase.")
            
            # Content type breakdown
            content_breakdown = {}
            for item in processed_items:
                content_type = item.get('content_type', 'unknown')
                content_breakdown[content_type] = content_breakdown.get(content_type, 0) + 1
            
            print("\n📊 Content breakdown:")
            for content_type, count in content_breakdown.items():
                print(f"  - {content_type}: {count} items")
        
        # Display content summary
        print("\n=== Content Summary ===")
        sample_count = 0
        for content_type, items in content_data.items():
            if items and sample_count < 5:
                for item in items[:2]:  # Show first 2 items of each type
                    caption = item.get('caption', '')[:50] + '...' if item.get('caption') and len(item.get('caption', '')) > 50 else item.get('caption', 'No caption')
                    likes = item.get('likes_count', 0)
                    comments = item.get('comments_count', 0)
                    content_type_display = item.get('media_type', content_type)
                    
                    print(f"{sample_count+1}. [{content_type_display}] {caption}")
                    print(f"   Likes: {likes:,} | Comments: {comments:,}")
                    
                    if item.get('content_type') == 'video':
                        duration = item.get('duration', 0)
                        views = item.get('view_count', 0)
                        print(f"   Video: {duration}s | Views: {views:,}")
                    print()
                    sample_count += 1
            
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
