#!/usr/bin/env python3
"""
Instagram Image Fetcher Web Application
Flask 기반 웹 인터페이스
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import requests
import json
import time
import re  # Added missing import
from datetime import datetime
from werkzeug.utils import secure_filename
import io
from PIL import Image
from typing import Dict, Any, List
from instagram_node_scraper import InstagramNodeScraper
from config.config import Config
from config.firebase_config import FirebaseManager
from src.utils import (
    download_image_with_retry, 
    validate_image_resolution, 
    get_image_info,
    create_user_folder,
    format_file_size,
    format_date,
    generate_unique_filename
)
from src.image_upscaler import ImageUpscaler

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Upload folder for images
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize services early to avoid scope issues
image_upscaler = ImageUpscaler()  # AI upscaling service
instagram_scraper = InstagramNodeScraper()  # Node.js scraper (primary)

class InstagramWebAPI:
    """웹 버전 Instagram API 클라이언트"""
    
    def __init__(self):
        self.api_key = Config.RAPIDAPI_KEY
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'instagram-scraper21.p.rapidapi.com'
        }
        self.base_url = "https://instagram-scraper21.p.rapidapi.com/api/v1"
    
    def test_api_status(self):
        """API 상태 테스트"""
        if not self.api_key:
            return {
                'status_code': 0,
                'message': "RapidAPI key not configured",
                'success': False
            }
        
        try:
            # 간단한 요청으로 기본 상태 확인
            response = requests.get(
                f"{self.base_url}/user-info",
                headers=self.headers,
                params={'username': 'natgeo'},
                timeout=10
            )
            return {
                'status_code': response.status_code,
                'message': response.text[:200] if response.status_code != 200 else "API Working",
                'success': response.status_code == 200
            }
        except Exception as e:
            return {
                'status_code': 0,
                'message': str(e),
                'success': False
            }
    
    def get_user_info_web(self, username):
        """웹용 사용자 정보 가져오기"""
        if not self.api_key:
            return {
                'success': False,
                'message': 'RapidAPI key not configured',
                'error_type': 'no_api_key'
            }
        
        try:
            # 여러 엔드포인트 시도
            endpoints = [
                ('user-posts', {'username': username}),
                ('user-profile', {'username': username}),
                ('user-full-posts', {'username': username})
            ]
            
            for endpoint_name, params in endpoints:
                try:
                    url = f"{self.base_url}/{endpoint_name}"
                    response = requests.get(url, headers=self.headers, params=params, timeout=15)
                    
                    print(f"Trying {endpoint_name}: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Success with {endpoint_name}")
                        
                        # 이미지 다운로드 (원본 품질, 필터링 없음)
                        images = self._process_images(data, username)
                        return {
                            'success': True,
                            'endpoint_used': endpoint_name,
                            'images': images,
                            'original_data': data
                        }
                    elif response.status_code == 429:
                        print(f"Rate limited on {endpoint_name}, waiting...")
                        time.sleep(5)
                        
                except Exception as e:
                    print(f"Error with {endpoint_name}: {e}")
                    
            return {'success': False, 'message': 'All endpoints failed'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _process_images(self, data, username):
        """이미지 데이터 처리"""
        images = []
        
        # 출력 폴더 생성
        user_folder = create_user_folder(username)
        
        # 이미지 추출 로직
        posts = []
        if isinstance(data, dict):
            if 'data' in data:
                posts = data['data']
            elif 'posts' in data:
                posts = data['posts']
        
        for i, post in enumerate(posts):
            try:
                # 게시물 이미지 찾기
                image_url = None
                if 'image' in post:
                    image_url = post['image']
                elif 'thumbnail' in post:
                    image_url = post['thumbnail']
                elif 'media_url' in post:
                    image_url = post['media_url']
                
                if image_url:
                    # 이미지 다운로드 및 해상도 확인 (unique filename with timestamp)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{username}_{timestamp}_{i+1}.jpg"
                    local_path = os.path.join(user_folder, filename)
                    
                    if self._download_image(image_url, local_path):
                        images.append({
                            'url': image_url,
                            'local_path': local_path,
                            'filename': filename,
                            'timestamp': datetime.now().isoformat(),
                            'post_caption': post.get('caption', '')[:100]
                        })
                        
            except Exception as e:
                print(f"Error processing post {i}: {e}")
        
        return images
    
    def _download_image(self, image_url, local_path):
        """이미지 다운로드 (원본 품질, 필터링 없음)"""
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 이미지 저장 (원본 품질)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded original image: {local_path}")
            return True
                
        except Exception as e:
            print(f"Download failed: {e}")
            return False

# Helper function for image download (deprecated - use utils.download_image_with_retry)
def download_image_simple(image_url: str, local_path: str) -> bool:
    """Simple image download function with better error handling"""
    return download_image_with_retry(image_url, local_path)

def discover_instagram_account(username: str) -> List[Dict]:
    """Discover Instagram account and provide manual upload option"""
    try:
        print(f"🔍 Discovering account @{username}...")
        
        # Try to access the profile page
        profile_url = f"https://www.instagram.com/{username}/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(profile_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Profile page accessible for @{username}")
            
            # Create a placeholder for manual upload
            return [{
                'id': f'{username}_manual_discovery',
                'shortcode': f'{username}_manual',
                'caption': f'Manual upload option for @{username}',
                'image_url': '',  # No image URL - user needs to upload manually
                'likes_count': 0,
                'comments_count': 0,
                'timestamp': datetime.now().isoformat(),
                'permalink': profile_url,
                'media_type': 'manual_upload',
                'content_type': 'manual',
                'is_manual': True,
                'profile_url': profile_url,
                'username': username
            }]
        else:
            print(f"❌ Profile page not accessible: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Account discovery error: {e}")
        return []

def scrape_instagram_alternative(username: str) -> List[Dict]:
    """Alternative Instagram scraping using multiple methods"""
    posts = []
    
    # Method 1: Try Instagram's public API endpoint
    try:
        print(f"🔍 Trying Instagram public API for @{username}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Try the web profile API
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {}).get('user', {})
            
            if not user_data.get('is_private', True):
                posts_data = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                
                for i, post_edge in enumerate(posts_data[:25]):
                    post = post_edge.get('node', {})
                    if post.get('__typename') == 'GraphImage':
                        display_url = post.get('display_url', '')
                        if display_url:
                            posts.append({
                                'id': post.get('id', f'{username}_api_{i}'),
                                'shortcode': post.get('shortcode', f'{username}_api_{i}'),
                                'display_url': display_url,
                                'thumbnail_src': display_url,
                                'description': post.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                                'likes': post.get('edge_media_preview_like', {}).get('count', 0),
                                'comments': post.get('edge_media_to_comment', {}).get('count', 0),
                                'owner': username
                            })
                
                print(f"✅ Instagram API found {len(posts)} posts")
                return posts
            else:
                print(f"❌ Account @{username} is private")
        else:
            print(f"❌ Instagram API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Instagram API error: {e}")
    
    # Method 2: Try scraping the HTML page directly
    try:
        print(f"🔍 Trying HTML scraping for @{username}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        url = f"https://www.instagram.com/{username}/"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Look for JSON-LD structured data
        json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
        json_ld_matches = re.findall(json_ld_pattern, response.text, re.DOTALL)
        
        for json_str in json_ld_matches:
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and 'image' in data:
                    image_url = data['image']
                    if isinstance(image_url, str) and image_url.startswith('http'):
                        posts.append({
                            'id': f'{username}_jsonld_{len(posts)}',
                            'shortcode': f'{username}_jsonld_{len(posts)}',
                            'display_url': image_url,
                            'thumbnail_src': image_url,
                            'description': data.get('description', ''),
                            'likes': 0,
                            'comments': 0,
                            'owner': username
                        })
            except json.JSONDecodeError:
                continue
        
        # Also look for meta tags
        meta_pattern = r'<meta property="og:image" content="([^"]+)"'
        meta_matches = re.findall(meta_pattern, response.text)
        
        for image_url in meta_matches:
            if image_url not in [p['display_url'] for p in posts]:
                posts.append({
                    'id': f'{username}_meta_{len(posts)}',
                    'shortcode': f'{username}_meta_{len(posts)}',
                    'display_url': image_url,
                    'thumbnail_src': image_url,
                    'description': '',
                    'likes': 0,
                    'comments': 0,
                    'owner': username
                })
        
        if posts:
            print(f"✅ HTML scraping found {len(posts)} posts")
            return posts[:25]  # Limit to 25 posts
                        
    except Exception as e:
        print(f"❌ HTML scraping error: {e}")
    
    # Method 3: Try Instagram's embed endpoint
    try:
        print(f"🔍 Trying Instagram embed endpoint for @{username}...")
        embed_url = f"https://www.instagram.com/{username}/embed/"
        embed_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instagram.com/',
        }
        
        embed_response = requests.get(embed_url, headers=embed_headers, timeout=10)
        if embed_response.status_code == 200:
            # Look for images in embed content
            img_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
            img_matches = re.findall(img_pattern, embed_response.text)
            
            for img_url in img_matches:
                if 'instagram' in img_url and img_url not in [p.get('image_url', '') for p in posts]:
                    posts.append({
                        'id': f'{username}_embed_{len(posts)}',
                        'image_url': img_url,
                        'caption': f'Embedded image from @{username}',
                        'likes': 0,
                        'comments': 0,
                        'owner': username
                    })
            
            if posts:
                print(f"✅ Embed endpoint found {len(posts)} images")
                return posts[:15]  # Limit to 15 posts
                
    except Exception as e:
        print(f"❌ Embed endpoint error: {e}")
    
    return posts

def process_image_with_upscaling(image_url: str, local_path: str, upscaling_service: str, upscaling_scale: int) -> Dict:
    """Download image and optionally upscale it"""
    try:
        # Download original image
        if download_image_simple(image_url, local_path):
            original_info = get_image_info(local_path)
            
            result = {
                'success': True,
                'original_path': local_path,
                'original_info': original_info,
                'upscaled_path': None,
                'upscaled_info': None
            }
            
            # Apply upscaling if requested
            if upscaling_service and upscaling_service in image_upscaler.get_available_services():
                print(f"🚀 Upscaling image with {upscaling_service} (scale: {upscaling_scale}x)...")
                
                upscaled_path = image_upscaler.upscale_image(local_path, upscaling_scale, upscaling_service)
                
                if upscaled_path and os.path.exists(upscaled_path):
                    upscaled_info = get_image_info(upscaled_path)
                    result['upscaled_path'] = upscaled_path
                    result['upscaled_info'] = upscaled_info
                    print(f"✅ Upscaling successful: {upscaled_info['width']}x{upscaled_info['height']}")
                else:
                    print("❌ Upscaling failed, using original image")
            
            return result
        else:
            return {'success': False, 'error': 'Failed to download image'}
                
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return {'success': False, 'error': str(e)}

# Initialize APIs
instagram_api = InstagramWebAPI()  # RapidAPI (backup)

# Initialize RapidAPI Instagram Scraper (primary)
if Config.RAPIDAPI_KEY:
    from src.instagram_rapidapi import InstagramRapidAPI
    instagram_rapidapi = InstagramRapidAPI(Config.RAPIDAPI_KEY)
    print(f"🚀 RapidAPI Instagram Scraper initialized")
else:
    instagram_rapidapi = None
    print(f"⚠️ RapidAPI key not found - using alternative methods only")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API 상태 확인"""
    status = instagram_api.test_api_status()
    return jsonify(status)

@app.route('/api/upscaling/status')
def upscaling_status():
    """업스케일링 서비스 상태 확인"""
    try:
        services_info = image_upscaler.get_service_info()
        available_services = image_upscaler.get_available_services()
        
        return jsonify({
            'success': True,
            'available_services': available_services,
            'services_info': services_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fetch', methods=['POST'])
def fetch_images():
    """이미지 가져오기 API"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    # Remove resolution filtering - always download original quality
    upscaling_service = data.get('upscaling_service', '')
    upscaling_scale = int(data.get('upscaling_scale', 2))
    upload_to_firebase = data.get('upload_to_firebase', False)
    content_types = data.get('content_types', ['posts'])  # Default to posts only
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    print(f"🚀 Attempting Instagram fetching for @{username}")
    
    # Initialize Firebase if requested
    firebase_manager = None
    firebase_uploads = []
    if upload_to_firebase:
        try:
            from config.firebase_config import FirebaseManager
            firebase_manager = FirebaseManager()
            print(f"🔥 Firebase initialized for @{username}")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            upload_to_firebase = False
    
    # Try multiple methods in order of preference - RapidAPI FIRST!
    methods_to_try = []
    
    # Priority 1: Enhanced RapidAPI Instagram Scraper (if available)
    if Config.RAPIDAPI_KEY:
        def get_selected_content():
            if 'all' in content_types:
                return instagram_rapidapi.get_all_content(username, 20)
            else:
                content_data = {'posts': [], 'stories': [], 'reels': [], 'igtv': []}
                if 'posts' in content_types:
                    content_data['posts'] = instagram_rapidapi.get_posts(username, 20)
                if 'stories' in content_types:
                    content_data['stories'] = instagram_rapidapi.get_stories(username)
                if 'reels' in content_types:
                    content_data['reels'] = instagram_rapidapi.get_reels(username, 20)
                if 'igtv' in content_types:
                    content_data['igtv'] = instagram_rapidapi.get_igtv(username, 20)
                return content_data
        
        methods_to_try.append(('rapidapi_enhanced', get_selected_content))
    
    # Priority 2: Node.js scraper (only if RapidAPI fails)
    methods_to_try.append(('nodejs_scraper', lambda: instagram_scraper.scrape_user_posts(username, count=25, download=True)))
    
    # Priority 3: Alternative scraper (HTML scraping)
    methods_to_try.append(('alternative_scraper', lambda: scrape_instagram_alternative(username)))
    
    # Priority 4: Manual account discovery (for private accounts)
    methods_to_try.append(('manual_discovery', lambda: discover_instagram_account(username)))
    
    for method_name, method_func in methods_to_try:
        try:
            print(f"🔄 Trying {method_name}...")
            
            if method_name == 'rapidapi_enhanced':
                # Handle enhanced RapidAPI with multiple content types
                content_data = method_func()
                if content_data and any(content_data.values()):
                    images = []
                    user_folder = create_user_folder(username)
                    
                    # Process all content types
                    for content_type, posts in content_data.items():
                        if not posts:
                            continue
                            
                        print(f"📱 Processing {len(posts)} {content_type} items...")
                        
                        for i, post in enumerate(posts):
                            try:
                                # Get media URL (image or video thumbnail)
                                image_url = post.get('image_url', '') or post.get('display_url', '')
                                video_url = post.get('video_url', '')
                                is_video = post.get('content_type') == 'video' and video_url
                                
                                if image_url:
                                    # Generate unique filename with content type
                                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                    if post.get('carousel_index'):
                                        filename = f"{username}_{content_type}_{timestamp}_{i+1}_{post.get('carousel_index', '')}.jpg"
                                    else:
                                        filename = f"{username}_{content_type}_{timestamp}_{i+1}.jpg"
                                    
                                    local_path = os.path.join(user_folder, filename)
                                    
                                    # Process image (thumbnail for videos)
                                    result = process_image_with_upscaling(image_url, local_path, upscaling_service, upscaling_scale)
                                    
                                    if result['success']:
                                        image_data = {
                                            'url': image_url,
                                            'video_url': video_url if is_video else None,
                                            'local_path': result['upscaled_path'] or result['original_path'],
                                            'filename': filename,
                                            'timestamp': datetime.now().isoformat(),
                                            'post_caption': post.get('caption', '')[:100],
                                            'likes': post.get('likes_count', 0),
                                            'comments': post.get('comments_count', 0),
                                            'shortcode': post.get('shortcode', ''),
                                            'content_type': content_type,
                                            'media_type': post.get('media_type', ''),
                                            'is_video': is_video,
                                            'duration': post.get('duration', 0) if is_video else None,
                                            'view_count': post.get('view_count', 0) if is_video else None,
                                            'permalink': post.get('permalink', '')
                                        }
                                        images.append(image_data)
                                        
                                        # Upload to Firebase if requested
                                        if upload_to_firebase and firebase_manager:
                                            try:
                                                firebase_url = firebase_manager.upload_image(
                                                    image_data['local_path'], 
                                                    f"instagram/{username}/{content_type}/{filename}"
                                                )
                                                firebase_uploads.append({
                                                    'local_path': image_data['local_path'],
                                                    'firebase_url': firebase_url,
                                                    'metadata': image_data
                                                })
                                            except Exception as e:
                                                print(f"❌ Firebase upload failed for {filename}: {e}")
                                
                            except Exception as e:
                                print(f"❌ Error processing {content_type} item {i+1}: {e}")
                                continue
                    
                    if images:
                        print(f"✅ Enhanced RapidAPI found {len(images)} total items across all content types")
                        return jsonify({
                            'success': True,
                            'method': method_name,
                            'images': images,
                            'firebase_uploads': firebase_uploads,
                            'total_items': len(images),
                            'content_breakdown': {k: len(v) for k, v in content_data.items() if v}
                        })
            
            elif method_name == 'manual_discovery':
                # Handle manual discovery - provide upload option
                posts = method_func()
                if posts:
                    # Create user folder
                    user_folder = create_user_folder(username)
                    
                    return jsonify({
                        'success': True,
                        'method': method_name,
                        'images': [],  # No images to display
                        'firebase_uploads': [],
                        'total_items': 0,
                        'manual_upload_available': True,
                        'username': username,
                        'profile_url': posts[0].get('profile_url', ''),
                        'message': f'Account @{username} discovered but requires manual image upload. Use the manual upload section below.'
                    })
            
            elif method_name in ['alternative_scraper', 'nodejs_scraper']:
                posts = method_func()
                if posts:
                    images = []
                    user_folder = create_user_folder(username)
                    
                    for i, post in enumerate(posts):
                        try:
                            image_url = post.get('display_url') or post.get('thumbnail_src', '')
                            if image_url:
                                # Generate unique filename with timestamp to avoid overwriting
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f"{username}_{timestamp}_{i+1}_{post.get('shortcode', 'post')}.jpg"
                                local_path = os.path.join(user_folder, filename)
                                
                                # Process image with optional upscaling
                                result = process_image_with_upscaling(image_url, local_path, upscaling_service, upscaling_scale)
                                
                                if result['success']:
                                    image_data = {
                                        'url': image_url,
                                        'local_path': result['upscaled_path'] or result['original_path'],
                                        'filename': filename,
                                        'timestamp': datetime.now().isoformat(),
                                        'post_caption': post.get('description', '')[:100],
                                        'likes': post.get('likes', 0),
                                        'comments': post.get('comments', 0),
                                        'original_info': result['original_info'],
                                        'upscaled_info': result['upscaled_info'],
                                        'upscaling_applied': bool(result['upscaled_path'])
                                    }
                                    images.append(image_data)
                        except Exception as e:
                            print(f"Error processing post {i}: {e}")
                    
                    # Upload to Firebase if requested
                    if upload_to_firebase and firebase_manager and images:
                        print(f"🔥 Starting Firebase upload for {len(images)} scraped images...")
                        for image_data in images:
                            try:
                                # Create metadata for Firebase
                                media_id = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(firebase_uploads)+1}"
                                
                                local_path = image_data.get('local_path', '')
                                if local_path and os.path.exists(local_path):
                                    file_extension = local_path.split('.')[-1]
                                    remote_path = f"instagram_media/{username}/{media_id}.{file_extension}"
                                    
                                    # Upload to Firebase Storage
                                    firebase_url = firebase_manager.upload_image(local_path, remote_path)
                                    
                                    # Save metadata to Firestore
                                    metadata = {
                                        'instagram_id': media_id,
                                        'username': username,
                                        'caption': image_data.get('post_caption', ''),
                                        'media_type': 'IMAGE',
                                        'width': image_data.get('width', 0),
                                        'height': image_data.get('height', 0),
                                        'upload_method': 'scraping',
                                        'timestamp': datetime.now().isoformat(),
                                        'likes': image_data.get('likes', 0),
                                        'comments': image_data.get('comments', 0)
                                    }
                                    
                                    firebase_manager.save_media_metadata(metadata, firebase_url)
                                    
                                    firebase_uploads.append({
                                        'filename': image_data.get('filename', ''),
                                        'firebase_url': firebase_url,
                                        'metadata_id': media_id
                                    })
                                    
                                    print(f"🔥 Firebase upload success: {firebase_url}")
                                    
                            except Exception as e:
                                print(f"❌ Firebase upload failed for {image_data.get('filename', '')}: {e}")
                    
                    response_data = {
                        'success': True,
                        'method': method_name,
                        'images': images,
                        'images_count': len(images),
                        'total_posts': len(posts),
                        'uploaded_count': len(images)
                    }
                    
                    if upload_to_firebase:
                        response_data['firebase_uploads'] = firebase_uploads
                        response_data['firebase_enabled'] = True
                        response_data['firebase_count'] = len(firebase_uploads)
                    else:
                        response_data['firebase_enabled'] = False
                    
                    return jsonify(response_data)
            
            elif method_name == 'rapidapi_backup':
                result = method_func()
                if result.get('success'):
                    return jsonify(result)
                    
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
            continue
    
    # All methods failed - return helpful message
    return jsonify({
        'success': False,
        'message': f'All scraping methods failed for @{username}. This could be due to:\n• Account is private\n• No public posts available\n• Instagram rate limiting\n• Network connectivity issues\n\nTry using the manual upload option below or check if the username is correct.',
        'suggestions': [
            'Verify the username is correct',
            'Check if the account is public', 
            'Try again later (rate limiting)',
            'Use manual upload option'
        ],
        'error_type': 'all_methods_failed',
        'manual_upload_available': True,
        'username': username
    })

@app.route('/download/<username>/<filename>')
def download_image(username, filename):
    """이미지 다운로드"""
    file_path = os.path.join(UPLOAD_FOLDER, username, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/gallery/<username>')
def gallery(username):
    """사용자 갤러리 페이지"""
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    
    if not os.path.exists(user_folder):
        return f"No images found for @{username}"
    
    images = []
    for filename in os.listdir(user_folder):
        file_path = os.path.join(user_folder, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            images.append(filename)
    
    return render_template('gallery.html', username=username, images=images)

@app.route('/api/accounts')
def get_accounts():
    """다운로드된 계정 목록과 통계 가져오기"""
    try:
        accounts = []
        
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({'accounts': [], 'total_accounts': 0})
        
        for username in os.listdir(UPLOAD_FOLDER):
            user_folder = os.path.join(UPLOAD_FOLDER, username)
            
            if os.path.isdir(user_folder):
                # 이미지 파일 개수 계산
                image_files = []
                for filename in os.listdir(user_folder):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        file_path = os.path.join(user_folder, filename)
                        if os.path.isfile(file_path):
                            # 파일 크기와 수정 시간 가져오기
                            stat = os.stat(file_path)
                            image_files.append({
                                'filename': filename,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'path': f'/download/{username}/{filename}'
                            })
                
                # 최신 이미지 3개 미리보기용
                recent_images = sorted(image_files, key=lambda x: x['modified'], reverse=True)[:3]
                
                accounts.append({
                    'username': username,
                    'total_images': len(image_files),
                    'recent_images': recent_images,
                    'last_updated': max([img['modified'] for img in image_files]) if image_files else None,
                    'total_size': sum([img['size'] for img in image_files])
                })
        
        # 최신 업데이트 순으로 정렬
        accounts.sort(key=lambda x: x['last_updated'] or '', reverse=True)
        
        return jsonify({
            'accounts': accounts,
            'total_accounts': len(accounts),
            'total_images': sum([acc['total_images'] for acc in accounts])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/<username>/images')
def get_account_images(username):
    """특정 계정의 모든 이미지 가져오기"""
    try:
        user_folder = os.path.join(UPLOAD_FOLDER, username)
        
        if not os.path.exists(user_folder):
            return jsonify({'images': [], 'username': username})
        
        local_images = []
        for filename in os.listdir(user_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                file_path = os.path.join(user_folder, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    local_images.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'download_url': f'/download/{username}/{filename}',
                        'gallery_url': f'/gallery/{username}',
                        'source': 'local'
                    })
        
        # Get Firebase images
        firebase_images = []
        try:
            from src.firebase_config import FirebaseManager
            firebase_manager = FirebaseManager()
            if firebase_manager.db:
                firebase_data = firebase_manager.get_media_collection(username=username, limit=100)
                
                for doc in firebase_data:
                    # Handle Firebase timestamp format
                    upload_time = doc.get('uploaded_at')
                    if isinstance(upload_time, dict) and '_seconds' in upload_time:
                        modified_time = datetime.fromtimestamp(upload_time['_seconds']).isoformat()
                    else:
                        modified_time = datetime.now().isoformat()
                    
                    firebase_images.append({
                        'filename': doc.get('instagram_id', 'unknown') + '.jpg',
                        'size': doc.get('metadata', {}).get('file_size', 0),
                        'modified': modified_time,
                        'download_url': doc.get('firebase_url', ''),
                        'gallery_url': f'/gallery/{username}',
                        'source': 'firebase',
                        'width': doc.get('metadata', {}).get('width', 0),
                        'height': doc.get('metadata', {}).get('height', 0)
                    })
        except Exception as e:
            print(f"❌ Firebase images fetch error: {e}")
        
        # Combine and sort all images
        all_images = local_images + firebase_images
        all_images.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'username': username,
            'images': all_images,
            'total_count': len(all_images),
            'local_count': len(local_images),
            'firebase_count': len(firebase_images)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual_upload', methods=['POST'])
def manual_upload():
    """수동 이미지 URL 업로드"""
    data = request.get_json()
    
    image_urls = data.get('image_urls', [])
    username = data.get('username', '').strip()
    # Remove resolution filtering - always download original quality
    
    if not username or not image_urls:
        return jsonify({'success': False, 'message': 'Username and image URLs required'})
    
    user_folder = create_user_folder(username)
    
    uploaded_images = []
    firebase_uploads = []
    upload_to_firebase = data.get('upload_to_firebase', False)
    
    # Initialize Firebase if requested
    firebase_manager = None
    if upload_to_firebase:
        try:
            from src.firebase_config import FirebaseManager
            firebase_manager = FirebaseManager()
            print(f"🔥 Firebase initialized for @{username}")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            upload_to_firebase = False
    
    for i, image_url in enumerate(image_urls):
        try:
            # Clean and validate URL
            image_url = image_url.strip()
            if not image_url or not image_url.startswith('http'):
                print(f"❌ Invalid URL: {image_url}")
                continue
                
            # Generate unique filename with timestamp to avoid overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{username}_manual_{timestamp}_{i+1}.jpg"
            local_path = os.path.join(user_folder, filename)
            
            print(f"🔄 Processing image {i+1}/{len(image_urls)}: {image_url[:50]}...")
            
            # Download and check resolution
            if download_image_with_retry(image_url, local_path):
                # Always accept downloaded images (no resolution filtering)
                image_info = get_image_info(local_path)
                if image_info:
                    image_data = {
                        'url': image_url,
                        'local_path': local_path,
                        'filename': filename,
                        'width': image_info['width'],
                        'height': image_info['height'],
                        'size': image_info['size']
                    }
                    uploaded_images.append(image_data)
                    print(f"✅ Added to upload list: {filename} ({image_info['width']}x{image_info['height']})")
                else:
                    os.remove(local_path)
                    print(f"❌ Failed to get image info: {filename}")
            else:
                print(f"❌ Failed to download: {image_url[:50]}...")
                    
        except Exception as e:
            print(f"❌ Error processing image {i+1}: {e}")
    
    # Upload to Firebase for successfully downloaded images
    if upload_to_firebase and firebase_manager and uploaded_images:
        print(f"🔥 Starting Firebase upload for {len(uploaded_images)} images...")
        for image_data in uploaded_images:
            try:
                # Create metadata for Firebase
                media_id = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(firebase_uploads)+1}"
                
                file_extension = image_data['local_path'].split('.')[-1]
                remote_path = f"instagram_media/{username}/{media_id}.{file_extension}"
                
                # Upload to Firebase Storage
                firebase_url = firebase_manager.upload_image(image_data['local_path'], remote_path)
                
                # Save metadata to Firestore
                metadata = {
                    'instagram_id': media_id,
                    'username': username,
                    'caption': f'Manual upload from {image_data["url"][:50]}...',
                    'media_type': 'IMAGE',
                    'width': image_data['width'],
                    'height': image_data['height'],
                    'upload_method': 'manual_upload',
                    'timestamp': datetime.now().isoformat()
                }
                
                firebase_manager.save_media_metadata(metadata, firebase_url)
                
                firebase_uploads.append({
                    'filename': image_data['filename'],
                    'firebase_url': firebase_url,
                    'metadata_id': media_id
                })
                
                print(f"🔥 Firebase upload success: {firebase_url}")
                
            except Exception as e:
                print(f"❌ Firebase upload failed for {image_data['filename']}: {e}")
    
    response_data = {
        'success': True,
        'uploaded_count': len(uploaded_images),
        'images': uploaded_images
    }
    
    if upload_to_firebase:
        response_data['firebase_uploads'] = firebase_uploads
        response_data['firebase_enabled'] = True
        response_data['firebase_count'] = len(firebase_uploads)
    else:
        response_data['firebase_enabled'] = False
    
    return jsonify(response_data)

@app.route('/api/folder_upload', methods=['POST'])
def folder_upload():
    """Upload multiple images from a folder"""
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        # Remove resolution filtering - always download original quality
        upload_to_firebase = request.form.get('upload_to_firebase', '').lower() == 'true'
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username is required'
            }), 400
        
        # Get uploaded files
        uploaded_files = request.files.getlist('images')
        if not uploaded_files:
            return jsonify({
                'success': False,
                'message': 'No images uploaded'
            }), 400
        
        # Filter image files
        image_files = []
        for file in uploaded_files:
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                image_files.append(file)
        
        if not image_files:
            return jsonify({
                'success': False,
                'message': 'No valid image files found'
            }), 400
        
        # Create user folder
        user_folder = create_user_folder(username)
        
        uploaded_images = []
        firebase_uploads = []
        
        # Initialize Firebase if requested
        firebase_manager = None
        if upload_to_firebase:
            try:
                firebase_manager = FirebaseManager()
                print(f"🔥 Firebase initialized for folder upload @{username}")
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                upload_to_firebase = False
        
        print(f"📂 Processing {len(image_files)} images from folder for @{username}")
        
        # Process each image
        for i, file in enumerate(image_files):
            try:
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_extension = file.filename.split('.')[-1].lower()
                filename = f"{username}_folder_{timestamp}_{i+1}.{file_extension}"
                local_path = os.path.join(user_folder, filename)
                
                print(f"🔄 Processing image {i+1}/{len(image_files)}: {file.filename}")
                
                # Save file temporarily
                file.save(local_path)
                
                # Always accept uploaded images (no resolution filtering)
                image_info = get_image_info(local_path)
                if image_info:
                    image_data = {
                        'filename': filename,
                        'local_path': local_path,
                        'original_filename': file.filename,
                        'width': image_info['width'],
                        'height': image_info['height'],
                        'size': image_info['size']
                    }
                    uploaded_images.append(image_data)
                    print(f"✅ Added to upload list: {filename} ({image_info['width']}x{image_info['height']})")
                else:
                    os.remove(local_path)
                    print(f"❌ Failed to get image info: {filename}")
                    
            except Exception as e:
                print(f"❌ Error processing image {i+1}: {e}")
                # Clean up if file was saved
                try:
                    if 'local_path' in locals() and os.path.exists(local_path):
                        os.remove(local_path)
                except:
                    pass
        
        # Upload to Firebase for successfully processed images
        if upload_to_firebase and firebase_manager and uploaded_images:
            print(f"🔥 Starting Firebase upload for {len(uploaded_images)} images...")
            for image_data in uploaded_images:
                try:
                    # Create metadata for Firebase
                    media_id = f"{username}_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(firebase_uploads)+1}"
                    
                    file_extension = image_data['local_path'].split('.')[-1]
                    remote_path = f"instagram_media/{username}/{media_id}.{file_extension}"
                    
                    # Upload to Firebase Storage
                    firebase_url = firebase_manager.upload_image(image_data['local_path'], remote_path)
                    
                    # Save metadata to Firestore
                    metadata = {
                        'instagram_id': media_id,
                        'username': username,
                        'caption': f'Folder upload: {image_data["original_filename"]}',
                        'media_type': 'IMAGE',
                        'width': image_data['width'],
                        'height': image_data['height'],
                        'upload_method': 'folder_upload',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    firebase_manager.save_media_metadata(metadata, firebase_url)
                    
                    firebase_uploads.append({
                        'filename': image_data['filename'],
                        'firebase_url': firebase_url,
                        'metadata_id': media_id
                    })
                    
                    print(f"🔥 Firebase upload success: {firebase_url}")
                    
                except Exception as e:
                    print(f"❌ Firebase upload failed for {image_data['filename']}: {e}")
        
        response_data = {
            'success': True,
            'uploaded_count': len(uploaded_images),
            'total_files': len(image_files),
            'images': uploaded_images
        }
        
        if upload_to_firebase:
            response_data['firebase_uploads'] = firebase_uploads
            response_data['firebase_enabled'] = True
            response_data['firebase_count'] = len(firebase_uploads)
        else:
            response_data['firebase_enabled'] = False
        
        print(f"✅ Folder upload completed: {len(uploaded_images)}/{len(image_files)} images processed")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Folder upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/upload_to_firebase', methods=['POST'])
def upload_to_firebase():
    """Upload a single image to Firebase Storage"""
    try:
        data = request.json
        username = data.get('username')
        filename = data.get('filename')
        
        if not username or not filename:
            return jsonify({
                'success': False,
                'message': 'Username and filename required'
            }), 400
        
        # Check if Firebase is configured
        firebase_manager = FirebaseManager()
        if not firebase_manager.bucket or not firebase_manager.db:
            return jsonify({
                'success': False,
                'message': 'Firebase not configured'
            }), 503
        
        # Get local file path
        local_path = os.path.join(Config.UPLOAD_FOLDER, username, filename)
        
        if not os.path.exists(local_path):
            return jsonify({
                'success': False,
                'message': 'Image file not found'
            }), 404
        
        # Upload to Firebase
        remote_path = f'instagram_images/{username}/{filename}'
        firebase_url = firebase_manager.upload_image(local_path, remote_path)
        
        if not firebase_url:
            return jsonify({
                'success': False,
                'message': 'Firebase upload failed'
            }), 500
        
        # Save metadata to Firestore (optional)
        try:
            media_id = f"{username}_{filename.replace('.jpg', '')}"
            
            # Get image info
            from PIL import Image
            with Image.open(local_path) as img:
                width, height = img.size
            
            metadata = {
                'media_id': media_id,
                'instagram_id': filename.replace('.jpg', '').split('_')[-1],
                'url': firebase_url,
                'username': username,
                'caption': f'Uploaded from @{username}',
                'media_type': 'IMAGE',
                'width': width,
                'height': height,
                'upload_method': 'web_ui_upload',
                'timestamp': datetime.now().isoformat()
            }
            
            firebase_manager.save_media_metadata(metadata, firebase_url)
        except Exception as e:
            print(f"⚠️ Warning: Could not save metadata to Firestore: {e}")
            print("   (Image uploaded to Storage successfully)")
        
        return jsonify({
            'success': True,
            'firebase_url': firebase_url,
            'metadata_id': media_id,
            'message': 'Successfully uploaded to Firebase'
        })
        
    except Exception as e:
        print(f"❌ Firebase upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Vercel 배포를 위한 WSGI 애플리케이션
# Vercel은 이 변수를 찾아서 애플리케이션을 실행합니다
application = app

if __name__ == '__main__':
    # 템플릿 폴더 생성
    os.makedirs(Config.TEMPLATE_FOLDER, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    print("🚀 Instagram Web App 시작")
    print(f"📱 브라우저에서 http://localhost:{Config.PORT} 방문")
    print("\n✨ 기능:")
    print("   - Instagram 사용자명으로 이미지 검색")
    print("   - 해상도 필터링 (800px 이상)")
    print("   - 이미지 미리보기 및 다운로드")
    print("   - 갤러리 보기")
    print("   - Firebase Storage 업로드")
    
    # Use default values if Config attributes are not set
    host = getattr(Config, 'HOST', '0.0.0.0')
    port = getattr(Config, 'PORT', 5000)
    debug = getattr(Config, 'DEBUG', True)
    
    app.run(debug=debug, host=host, port=port)
