#!/usr/bin/env python3
"""
Utility functions for Instagram Tools
"""

import os
import hashlib
from datetime import datetime
from PIL import Image
import requests
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_unique_filename(username, original_filename, timestamp=None):
    """Generate unique filename with timestamp"""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Extract extension
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        ext = f'.{ext}'
    else:
        name = original_filename
        ext = '.jpg'
    
    # Generate unique filename
    unique_filename = f"{username}_{timestamp}_{name}{ext}"
    return unique_filename

def download_image_with_retry(url, local_path, max_retries=3, timeout=30):
    """Download image with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            
            if response.status_code == 403:
                print(f"❌ Access forbidden (403) for: {url[:50]}...")
                return False
            elif response.status_code == 404:
                print(f"❌ Not found (404) for: {url[:50]}...")
                return False
            
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"❌ Not an image: {content_type}")
                return False
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > Config.MAX_IMAGE_SIZE:
                print(f"❌ File too large: {int(content_length)} bytes")
                return False
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {local_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Download attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return False
            continue
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    return False

def validate_image_resolution(image_path, min_resolution):
    """Validate image resolution"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width >= min_resolution and height >= min_resolution
    except Exception as e:
        print(f"❌ Error validating image: {e}")
        return False

def get_image_info(image_path):
    """Get image information"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            file_size = os.path.getsize(image_path)
            return {
                'width': width,
                'height': height,
                'size': file_size,
                'format': img.format
            }
    except Exception as e:
        print(f"❌ Error getting image info: {e}")
        return None

def create_user_folder(username, base_folder=None):
    """Create user folder for downloads"""
    if base_folder is None:
        base_folder = Config.UPLOAD_FOLDER
    
    user_folder = os.path.join(base_folder, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def format_file_size(bytes_size):
    """Format file size in human readable format"""
    if bytes_size == 0:
        return '0 B'
    
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB']
    i = 0
    
    while bytes_size >= k and i < len(sizes) - 1:
        bytes_size /= k
        i += 1
    
    return f"{bytes_size:.1f} {sizes[i]}"

def format_date(date_string):
    """Format date string for display"""
    try:
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            return '오늘'
        elif diff.days == 1:
            return '어제'
        elif diff.days < 7:
            return f'{diff.days}일 전'
        else:
            return date.strftime('%Y-%m-%d')
    except:
        return date_string
