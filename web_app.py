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
from datetime import datetime
from werkzeug.utils import secure_filename
import io
from PIL import Image
from instagram_node_scraper import InstagramNodeScraper
from config import Config
from src.firebase_config import FirebaseManager
from src.utils import (
    download_image_with_retry, 
    validate_image_resolution, 
    get_image_info,
    create_user_folder,
    format_file_size,
    format_date,
    generate_unique_filename
)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Upload folder for images
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    
    def get_user_info_web(self, username, min_resolution=800):
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
                        
                        # 이미지 필터링 및 다운로드
                        images = self._process_images(data, min_resolution, username)
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
    
    def _process_images(self, data, min_resolution, username):
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
                    
                    if self._download_and_filter_image(image_url, local_path, min_resolution):
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
    
    def _download_and_filter_image(self, image_url, local_path, min_resolution):
        """이미지 다운로드 및 해상도 필터링"""
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # PIL로 해상도 확인
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            
            if width >= min_resolution and height >= min_resolution:
                # 해상도 조건 만족, 저장
                img.save(local_path, 'JPEG', quality=95)
                print(f"✅ Downloaded: {width}x{height} - {local_path}")
                return True
            else:
                print(f"❌ Resolution too low: {width}x{height}")
                return False
                
        except Exception as e:
            print(f"Download failed: {e}")
            return False

# Helper function for image download (deprecated - use utils.download_image_with_retry)
def download_image_simple(image_url: str, local_path: str) -> bool:
    """Simple image download function with better error handling"""
    return download_image_with_retry(image_url, local_path)

# Initialize APIs
instagram_api = InstagramWebAPI()  # RapidAPI (backup)
instagram_scraper = InstagramNodeScraper()  # Node.js scraper (primary)

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API 상태 확인"""
    status = instagram_api.test_api_status()
    return jsonify(status)

@app.route('/api/fetch', methods=['POST'])
def fetch_images():
    """이미지 가져오기 API"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    min_resolution = int(data.get('min_resolution', 800))
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'})
    
    print(f"🚀 Attempting Instagram fetching for @{username}")
    
    # Try multiple methods in order of preference
    methods_to_try = [
        ('nodejs_scraper', lambda: instagram_scraper.scrape_user_posts(username, count=25, min_resolution=min_resolution, download=True)),
    ]
    
    # Only add RapidAPI backup if API key is available
    if Config.RAPIDAPI_KEY:
        methods_to_try.append(('rapidapi_backup', lambda: instagram_api.get_user_info_web(username, min_resolution)))
    
    for method_name, method_func in methods_to_try:
        try:
            print(f"🔄 Trying {method_name}...")
            
            if method_name == 'nodejs_scraper':
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
                                
                                if download_image_simple(image_url, local_path):
                                    images.append({
                                        'url': image_url,
                                        'local_path': local_path,
                                        'filename': filename,
                                        'timestamp': datetime.now().isoformat(),
                                        'post_caption': post.get('description', '')[:100],
                                        'likes': post.get('likes', 0),
                                        'comments': post.get('comments', 0)
                                    })
                        except Exception as e:
                            print(f"Error processing post {i}: {e}")
                    
                    return jsonify({
                        'success': True,
                        'method': method_name,
                        'images': images,
                        'images_count': len(images),
                        'total_posts': len(posts)
                    })
            
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
        'message': 'All automated methods failed. Instagram may be blocking requests.',
        'suggestions': [
            'Try with different Instagram account',
            'Wait a few minutes and try again', 
            'Check if Instagram servers are accessible',
            'Consider using Instagram\'s official API'
        ],
        'error_type': 'all_methods_failed'
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
        
        images = []
        for filename in os.listdir(user_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                file_path = os.path.join(user_folder, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    images.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'download_url': f'/download/{username}/{filename}',
                        'gallery_url': f'/gallery/{username}'
                    })
        
        # 최신 순으로 정렬
        images.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'username': username,
            'images': images,
            'total_count': len(images)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual_upload', methods=['POST'])
def manual_upload():
    """수동 이미지 URL 업로드"""
    data = request.get_json()
    
    image_urls = data.get('image_urls', [])
    username = data.get('username', '').strip()
    min_resolution = int(data.get('min_resolution', 800))
    
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
                # Check resolution
                if validate_image_resolution(local_path, min_resolution):
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
                    # Remove low resolution image
                    os.remove(local_path)
                    print(f"❌ Removed low resolution image: {filename}")
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
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
