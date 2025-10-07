#!/usr/bin/env python3
"""
Image Upscaling Services Integration
Supports multiple AI-powered upscaling APIs
"""

import requests
import base64
import os
import time
from typing import Dict, Optional, List
from PIL import Image
import io
from config.config import Config

class ImageUpscaler:
    """AI-powered image upscaling service"""
    
    def __init__(self):
        self.services = {
            'replicate': self._upscale_replicate,
            'deepai': self._upscale_deepai,
            'upscale_media': self._upscale_upscale_media,
            'lets_enhance': self._upscale_lets_enhance
        }
    
    def upscale_image(self, image_path: str, scale_factor: int = 2, service: str = 'replicate') -> Optional[str]:
        """
        Upscale an image using the specified service
        
        Args:
            image_path: Path to the input image
            scale_factor: Upscaling factor (2x, 4x, etc.)
            service: Upscaling service to use
            
        Returns:
            Path to upscaled image or None if failed
        """
        if service not in self.services:
            print(f"❌ Unknown upscaling service: {service}")
            return None
        
        try:
            print(f"🔄 Upscaling image with {service} (scale: {scale_factor}x)...")
            upscaled_path = self.services[service](image_path, scale_factor)
            
            if upscaled_path and os.path.exists(upscaled_path):
                print(f"✅ Upscaling successful: {upscaled_path}")
                return upscaled_path
            else:
                print(f"❌ Upscaling failed with {service}")
                return None
                
        except Exception as e:
            print(f"❌ Upscaling error with {service}: {e}")
            return None
    
    def _upscale_replicate(self, image_path: str, scale_factor: int) -> Optional[str]:
        """Upscale using Replicate Real-ESRGAN"""
        if not Config.REPLICATE_API_TOKEN:
            print("❌ Replicate API token not configured")
            return None
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Replicate API call
            headers = {
                'Authorization': f'Token {Config.REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'version': '42dc2c29-8d96-45a4-b16b-646ac6bd3661',  # Real-ESRGAN model
                'input': {
                    'image': f'data:image/jpeg;base64,{image_b64}',
                    'scale': scale_factor,
                    'face_enhance': True
                }
            }
            
            response = requests.post(
                'https://api.replicate.com/v1/predictions',
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 201:
                prediction_id = response.json()['id']
                
                # Poll for completion
                for _ in range(30):  # Wait up to 5 minutes
                    time.sleep(10)
                    
                    status_response = requests.get(
                        f'https://api.replicate.com/v1/predictions/{prediction_id}',
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        result = status_response.json()
                        if result['status'] == 'succeeded':
                            # Download upscaled image
                            upscaled_url = result['output']
                            return self._download_upscaled_image(upscaled_url, image_path, 'replicate')
                        elif result['status'] == 'failed':
                            print(f"❌ Replicate prediction failed: {result.get('error', 'Unknown error')}")
                            return None
                else:
                    print("❌ Replicate prediction timeout")
                    return None
            else:
                print(f"❌ Replicate API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Replicate upscaling error: {e}")
            return None
    
    def _upscale_deepai(self, image_path: str, scale_factor: int) -> Optional[str]:
        """Upscale using DeepAI Super Resolution API"""
        if not Config.DEEP_AI_API_KEY:
            print("❌ DeepAI API key not configured")
            return None
        
        try:
            headers = {'api-key': Config.DEEP_AI_API_KEY}
            
            with open(image_path, 'rb') as f:
                files = {'image': f}
                
                response = requests.post(
                    'https://api.deepai.org/api/torch-srgan',
                    headers=headers,
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                if 'output_url' in result:
                    return self._download_upscaled_image(result['output_url'], image_path, 'deepai')
                else:
                    print(f"❌ DeepAI response error: {result}")
                    return None
            else:
                print(f"❌ DeepAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ DeepAI upscaling error: {e}")
            return None
    
    def _upscale_upscale_media(self, image_path: str, scale_factor: int) -> Optional[str]:
        """Upscale using Upscale.media API"""
        if not Config.UPSCALE_MEDIA_API_KEY:
            print("❌ Upscale.media API key not configured")
            return None
        
        try:
            headers = {'Authorization': f'Bearer {Config.UPSCALE_MEDIA_API_KEY}'}
            
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'scale': scale_factor}
                
                response = requests.post(
                    'https://api.upscale.media/v1/upscale',
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                if 'upscaled_url' in result:
                    return self._download_upscaled_image(result['upscaled_url'], image_path, 'upscale_media')
                else:
                    print(f"❌ Upscale.media response error: {result}")
                    return None
            else:
                print(f"❌ Upscale.media API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Upscale.media upscaling error: {e}")
            return None
    
    def _upscale_lets_enhance(self, image_path: str, scale_factor: int) -> Optional[str]:
        """Upscale using Let's Enhance API"""
        if not Config.LETS_ENHANCE_API_KEY:
            print("❌ Let's Enhance API key not configured")
            return None
        
        try:
            headers = {'Authorization': f'Bearer {Config.LETS_ENHANCE_API_KEY}'}
            
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {
                    'scale': scale_factor,
                    'format': 'jpeg',
                    'quality': 95
                }
                
                response = requests.post(
                    'https://api.letsenhance.io/v1/enhance',
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                if 'enhanced_url' in result:
                    return self._download_upscaled_image(result['enhanced_url'], image_path, 'lets_enhance')
                else:
                    print(f"❌ Let's Enhance response error: {result}")
                    return None
            else:
                print(f"❌ Let's Enhance API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Let's Enhance upscaling error: {e}")
            return None
    
    def _download_upscaled_image(self, url: str, original_path: str, service: str) -> Optional[str]:
        """Download upscaled image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Generate upscaled filename
            base_name = os.path.splitext(original_path)[0]
            extension = os.path.splitext(original_path)[1]
            upscaled_path = f"{base_name}_upscaled_{service}{extension}"
            
            # Save upscaled image
            with open(upscaled_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded upscaled image: {upscaled_path}")
            return upscaled_path
            
        except Exception as e:
            print(f"❌ Failed to download upscaled image: {e}")
            return None
    
    def get_available_services(self) -> List[str]:
        """Get list of available upscaling services"""
        available = []
        
        if Config.REPLICATE_API_TOKEN:
            available.append('replicate')
        if Config.DEEP_AI_API_KEY:
            available.append('deepai')
        if Config.UPSCALE_MEDIA_API_KEY:
            available.append('upscale_media')
        if Config.LETS_ENHANCE_API_KEY:
            available.append('lets_enhance')
        
        return available
    
    def get_service_info(self) -> Dict[str, Dict]:
        """Get information about available services"""
        services_info = {
            'replicate': {
                'name': 'Replicate Real-ESRGAN',
                'description': 'High-quality AI upscaling with Real-ESRGAN',
                'max_scale': 4,
                'supported_formats': ['jpg', 'png', 'webp'],
                'available': bool(Config.REPLICATE_API_TOKEN)
            },
            'deepai': {
                'name': 'DeepAI Super Resolution',
                'description': 'Fast AI-powered image upscaling',
                'max_scale': 4,
                'supported_formats': ['jpg', 'png'],
                'available': bool(Config.DEEP_AI_API_KEY)
            },
            'upscale_media': {
                'name': 'Upscale.media',
                'description': 'Professional image upscaling service',
                'max_scale': 8,
                'supported_formats': ['jpg', 'png', 'webp'],
                'available': bool(Config.UPSCALE_MEDIA_API_KEY)
            },
            'lets_enhance': {
                'name': "Let's Enhance",
                'description': 'AI-powered image enhancement and upscaling',
                'max_scale': 16,
                'supported_formats': ['jpg', 'png'],
                'available': bool(Config.LETS_ENHANCE_API_KEY)
            }
        }
        
        return services_info
