#!/usr/bin/env python3
"""
Batch Instagram Downloader - Download posts from multiple accounts
"""

import json
import subprocess
import argparse
import os
import time
from typing import List, Dict

class BatchDownloader:
    def __init__(self):
        """Initialize Batch Downloader"""
        self.successful_downloads = []
        self.failed_downloads = []
        self.download_stats = {
            'total_accounts': 0,
            'successful_accounts': 0,
            'failed_accounts': 0,
            'total_images': 0
        }
    
    def download_from_accounts(self, accounts: List[Dict], per_account_limit: int = 10, 
                              min_resolution: int = 800, download_dir: str = "downloads"):
        """Download posts from multiple accounts"""
        
        print(f"Starting batch download from {len(accounts)} accounts...")
        print(f"Each account: max {per_account_limit} posts, min {min_resolution}px resolution")
        print("=" * 60)
        
        for i, account in enumerate(accounts, 1):
            username = account.get('username')
            if not username:
                continue
                
            print(f"\n[{i}/{len(accounts)}] Downloading from @{username}...")
            print(f"Account: {account.get('full_name', 'Unknown')}")
            
            try:
                # Run instagram_rapidapi.py command
                cmd = [
                    'python3', 'instagram_rapidapi.py',
                    '--username', username,
                    '--limit', str(per_account_limit),
                    '--download',
                    '--min-resolution', str(min_resolution),
                    '--output', f"{username}_posts.json"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✓ Successfully downloaded from @{username}")
                    
                    # Count downloaded images
                    download_folder = os.path.join(download_dir, f"{username}_*")
                    import glob
                    images = glob.glob(download_folder.replace('*', '*'))
                    image_count = len([f for f in images if f.endswith(('.jpg', '.jpeg', '.png'))])
                    
                    self.successful_downloads.append({
                        'username': username,
                        'full_name': account.get('full_name', ''),
                        'followers_count': account.get('followers_count', 0),
                        'image_count': image_count,
                        'posts_file': f"{username}_posts.json"
                    })
                    self.download_stats['successful_accounts'] += 1
                    self.download_stats['total_images'] += image_count
                    
                else:
                    print(f"✗ Failed to download from @{username}")
                    error_msg = result.stderr.split('\n')[-2] if result.stderr else "Unknown error"
                    print(f"  Error: {error_msg}")
                    
                    self.failed_downloads.append({
                        'username': username,
                        'full_name': account.get('full_name', ''),
                        'error': error_msg
                    })
                    self.download_stats['failed_accounts'] += 1
                
            except subprocess.TimeoutExpired:
                print(f"✗ Timeout downloading from @{username}")
                self.failed_downloads.append({
                    'username': username,
                    'full_name': account.get('full_name', ''),
                    'error': 'Timeout'
                })
                self.download_stats['failed_accounts'] += 1
                
            except Exception as e:
                print(f"✗ Error downloading from @{username}: {e}")
                self.failed_downloads.append({
                    'username': username,
                    'full_name': account.get('full_name', ''),
                    'error': str(e)
                })
                self.download_stats['failed_accounts'] += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(2)
        
        self.download_stats['total_accounts'] = len(accounts)
        self.print_summary()
    
    def print_summary(self):
        """Print download summary"""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total accounts processed: {self.download_stats['total_accounts']}")
        print(f"Successful downloads: {self.download_stats['successful_accounts']}")
        print(f"Failed downloads: {self.download_stats['failed_accounts']}")
        print(f"Total images downloaded: {self.download_stats['total_images']}")
        
        if self.successful_downloads:
            print(f"\nSuccessful accounts:")
            for acc in self.successful_downloads:
                followers = acc['followers_count']
                if followers >= 1000000:
                    followers_str = f"{followers/1000000:.1f}M"
                elif followers >= 1000:
                    followers_str = f"{followers/1000:.1f}K"
                else:
                    followers_str = str(followers)
                
                print(f"  @{acc['username']} ({followers_str} followers) - {acc['image_count']} images")
        
        if self.failed_downloads:
            print(f"\nFailed accounts:")
            for acc in self.failed_downloads:
                print(f"  @{acc['username']} - {acc['error']}")
        
        # Save results
        results = {
            'stats': self.download_stats,
            'successful_downloads': self.successful_downloads,
            'failed_downloads': self.failed_downloads
        }
        
        with open('batch_download_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nDetailed results saved to batch_download_results.json")

def main():
    parser = argparse.ArgumentParser(description='Batch Instagram Downloader')
    parser.add_argument('--input', '-i', required=True, help='JSON file with accounts list')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Posts per account (default: 10)')
    parser.add_argument('--resolution', '-r', type=int, default=800, help='Min resolution (default: 800)')
    parser.add_argument('--start-from', type=int, default=0, help='Start from account index (default: 0)')
    parser.add_argument('--max-accounts', type=int, help='Max accounts to process')
    
    args = parser.parse_args()
    
    try:
        # Load accounts from JSON file
        with open(args.input, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        # Limit accounts if specified
        if args.max_accounts:
            accounts = accounts[:args.max_accounts]
        
        # Start from specific index
        if args.start_from > 0:
            accounts = accounts[args.start_from:]
        
        print(f"Loaded {len(accounts)} accounts from {args.input}")
        
        # Initialize downloader
        downloader = BatchDownloader()
        
        # Start batch download
        downloader.download_from_accounts(
            accounts=accounts,
            per_account_limit=args.limit,
            min_resolution=args.resolution
        )
        
    except FileNotFoundError:
        print(f"Error: File {args.input} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {args.input}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
