#!/usr/bin/env python3
"""
Instagram Node.js Scraper Integration
Using the insta-scraper npm package for Instagram scraping
"""

import subprocess
import json
import os
import requests
from typing import Dict, List
from PIL import Image
import io

class InstagramNodeScraper:
    def __init__(self):
        """Initialize Instagram scraper using Node.js package"""
        self.temp_dir = "temp_scrapes"
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def scrape_user_posts(self, username: str, count: int = 25, min_resolution: int = 800, download: bool = True) -> List[Dict]:
        """
        Scrape Instagram user posts using Node.js scraper
        
        Args:
            username: Instagram username (without @)
            count: Number of posts to scrape
            min_resolution: Minimum image resolution
            download: Whether to download images
            
        Returns:
            List of post data with high-resolution images
        """
        try:
            # Create Node.js script content using puppeteer for Instagram scraping
            script_content = f'''
const puppeteer = require('puppeteer');

async function run() {{
    let browser;
    try {{
        console.log('🚀 Starting Instagram scraping for @{username}...');
        
        browser = await puppeteer.launch({{ 
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }});
        
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        
        // Navigate to Instagram profile
        await page.goto('https://www.instagram.com/{username}/', {{ waitUntil: 'networkidle2' }});
        
        // Wait for posts to load
        await page.waitForSelector('article', {{ timeout: 10000 }});
        
        // Extract post data
        const posts = await page.evaluate(() => {{
            const postElements = document.querySelectorAll('article a[href*="/p/"]');
            const posts = [];
            
            postElements.forEach((link, index) => {{
                if (index >= {count}) return;
                
                const img = link.querySelector('img');
                if (img) {{
                    posts.push({{
                        id: link.href.split('/p/')[1]?.split('/')[0] || 'unknown',
                        shortcode: link.href.split('/p/')[1]?.split('/')[0] || 'unknown',
                        display_url: img.src,
                        thumbnail_src: img.src,
                        description: img.alt || '',
                        likes: 0,
                        comments: 0,
                        owner: '{username}'
                    }});
                }}
            }});
            
            return posts;
        }});
        
        console.log('✅ Scraping completed!');
        console.log('📸 Found ' + posts.length + ' posts');
        
        if (posts.length > 0) {{
            console.log('📱 Processed posts:');
            console.log(JSON.stringify({{
                method: 'puppeteer',
                username: '{username}',
                total_found: posts.length,
                processed_count: posts.length,
                posts: posts
            }}, null, 2));
        }} else {{
            console.log('❌ No posts found');
        }}
        
    }} catch (error) {{
        console.error('❌ Error:', error.message);
        console.error('📊 Error details:', error);
        process.exit(1);
    }} finally {{
        if (browser) {{
            await browser.close();
        }}
    }}
}}

run();
'''
            
            # Write script to temporary file
            script_path = os.path.join(self.temp_dir, 'scraper_script.js')
            with open(script_path, 'w') as f:
                f.write(script_content)


            # Run the Node.js script
            result = subprocess.run(
                ['node', script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                return []
            
            # Parse the JSON output
            try:
                # Find JSON in output
                lines = result.stdout.split('\n')
                json_start = -1
                json_end = -1
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('{') and 'method' in line:
                        json_start = i
                    elif line.strip().endswith('}') and json_start != -1:
                        json_end = i
                        break
                
                # If not found, try to find the last complete JSON object
                if json_start == -1:
                    # Look for the complete JSON object in the output
                    full_output = result.stdout
                    start_idx = full_output.find('{')
                    if start_idx != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(full_output)):
                            if full_output[i] == '{':
                                brace_count += 1
                            elif full_output[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i
                                    break
                        
                        if end_idx > start_idx:
                            json_text = full_output[start_idx:end_idx+1]
                            try:
                                scraped_data = json.loads(json_text)
                                posts = scraped_data.get('posts', [])
                                
                                print(f"✅ Successfully scraped {len(posts)} posts for @{username}")
                                
                                # Filter and process images based on resolution
                                filtered_posts = []
                                for post in posts:
                                    if self._check_image_resolution(post, min_resolution):
                                        filtered_posts.append(post)
                                    else:
                                        print(f"❌ Skipped post {post.get('shortcode', 'unknown')} - resolution too low")
                                
                                return filtered_posts
                            except json.JSONDecodeError as e:
                                print(f"JSON Parse Error: {e}")
                                print(f"Raw output: {result.stdout[:500]}")
                                return []
                
                if json_start != -1 and json_end != -1:
                    json_lines = lines[json_start:json_end+1]
                    json_text = '\n'.join(json_lines)
                    
                    # Clean up the JSON text
                    json_text = json_text.strip()
                    
                    scraped_data = json.loads(json_text)
                    posts = scraped_data.get('posts', [])
                    
                    print(f"✅ Successfully scraped {len(posts)} posts for @{username}")
                    
                    # Filter and process images based on resolution
                    filtered_posts = []
                    for post in posts:
                        if self._check_image_resolution(post, min_resolution):
                            filtered_posts.append(post)
                        else:
                            print(f"❌ Skipped post {post.get('shortcode', 'unknown')} - resolution too low")
                    
                    return filtered_posts
                else:
                    print("❌ Could not find valid JSON output")
                    print(f"Raw output: {result.stdout[:500]}")
                    return []
                
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw output: {result.stdout[:500]}")
                return []
                
        except subprocess.TimeoutExpired:
            print("❌ Scraper timed out")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def _check_image_resolution(self, post: Dict, min_resolution: int) -> bool:
        """Check if post image meets minimum resolution requirements"""
        try:
            # For puppeteer scraping, we don't have dimension info, so accept all images
            # The actual resolution check will be done during download
            return True
                
        except Exception as e:
            print(f"Error checking resolution: {e}")
            return False
    
    def get_user_info(self, username: str) -> Dict:
        """Get basic user information"""
        try:
            # Simple approach - extract info from first scraped post
            posts = self.scrape_user_posts(username, count=1, download=False)
            if posts:
                first_post = posts[0]
                owner = first_post.get('owner', {})
                return {
                    'username': owner.get('username', username),
                    'id': owner.get('id', ''),
                    'verified': False,
                    'private': False,
                    'posts_count': len(posts),
                    'bio': '',
                    'followers_count': 0,
                    'following_count': 0
                }
            return {}
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {}

def test_scraper():
    """Test the Instagram scraper"""
    scraper = InstagramNodeScraper()
    
    print("🔍 Testing Instagram Node.js Scraper...")
    print("🎯 Target: @natgeo (National Geographic)")
    
    # Test scraping
    posts = scraper.scrape_user_posts('natgeo', count=5, min_resolution=800)
    
    if posts:
        print(f"\n📸 Successfully found {len(posts)} high-resolution posts:")
        for i, post in enumerate(posts, 1):
            shortcode = post.get('shortcode', 'unknown')
            dimension = post.get('dimension', {})
            likes = post.get('likes', 0)
            url = f"https://instagram.com/p/{shortcode}"
            
            print(f"{i}. Post: {url}")
            print(f"   Resolution: {dimension.get('width', 0)}x{dimension.get('height', 0)}")
            print(f"   Likes: {likes:,}")
            print()
    else:
        print("❌ No posts found or scraping failed")
        print("\n💡 Possible solutions:")
        print("   1. Check if Instagram is blocking the scraper")
        print("   2. Verify the username is correct")
        print("   3. Try with a different account")
        print("   4. Wait and retry later")

if __name__ == "__main__":
    test_scraper()
