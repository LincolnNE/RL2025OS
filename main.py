#!/usr/bin/env python3
"""
Instagram Tools - Main Entry Point
Unified interface for all Instagram tools
"""

import sys
import os
import argparse
from src import (
    InstagramAPI,
    InstagramRapidAPI,
    InstagramAccountFinder, 
    BatchDownloader
)

# Module imports for execution
import src.instagram_account_finder as instagram_account_finder
import src.instagram_rapidapi as instagram_rapidapi
import src.batch_downloader as batch_downloader

def main():
    parser = argparse.ArgumentParser(
        description='Instagram Tools - Unified interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find photography accounts
  {prog} find --method category --query photography --limit 10
  
  # Download from specific user
  {prog} download --username natgeo --limit 10 --min-resolution 1080
  
  # Batch download from found accounts
  {prog} batch --input output/found_accounts.json --limit 5 --resolution 800
  
  # Use official Instagram API (requires token)
  {prog} official --token YOUR_TOKEN --limit 10 --firebase
        """.format(prog=os.path.basename(__file__))
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Find accounts command
    find_parser = subparsers.add_parser('find', help='Find Instagram accounts')
    find_parser.add_argument('--method', choices=['hashtag', 'explore', 'category'], 
                            required=True, help='Search method')
    find_parser.add_argument('--query', help='Hashtag/category to search')
    find_parser.add_argument('--limit', type=int, default=20, help='Number of accounts to find')
    find_parser.add_argument('--min-followers', type=int, default=10000, help='Minimum follower count')
    find_parser.add_argument('--output', default='output/found_accounts.json', help='Output file')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search Instagram accounts by keywords')
    search_parser.add_argument('keywords', nargs='+', help='Keywords to search for')
    search_parser.add_argument('--limit', type=int, default=20, help='Number of accounts to find')
    search_parser.add_argument('--output', default='output/search_results.json', help='Output file')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download posts from Instagram accounts')
    download_parser.add_argument('username', help='Instagram username (without @)')
    download_parser.add_argument('--limit', type=int, default=10, help='Maximum posts to download')
    download_parser.add_argument('--min-resolution', type=int, default=800,
                               help='Minimum image resolution in pixels')
    download_parser.add_argument('--download-dir', default='output/images',
                               help='Directory to save downloaded images')
    download_parser.add_argument('--firebase', action='store_true',
                               help='Upload images to Firebase Storage')
    download_parser.add_argument('--output', default='output/posts.json',
                               help='Save metadata to this file')
    
    # Batch download command
    batch_parser = subparsers.add_parser('batch', help='Batch download from multiple accounts')
    batch_parser.add_argument('--input', '-i', required=True, help='JSON file with accounts list')
    batch_parser.add_argument('--limit', '-l', type=int, default=10, help='Posts per account')
    batch_parser.add_argument('--resolution', '-r', type=int, default=800, help='Min resolution')
    batch_parser.add_argument('--start-from', type=int, default=0, help='Start from account index')
    batch_parser.add_argument('--max-accounts', type=int, help='Max accounts to process')
    batch_parser.add_argument('--firebase', action='store_true', help='Upload to Firebase')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--setup', action='store_true', help='Setup configuration files')
    config_parser.add_argument('--test-firebase', action='store_true', help='Test Firebase connection')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Change to tools directory
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(tools_dir)
        
        if args.command == 'find':
            # Import and run instagram_account_finder
            sys.argv = ['instagram_account_finder.py', 
                       '--method', args.method,
                       '--query', args.query or '',
                       '--limit', args.limit,
                       '--min-followers', args.min_followers,
                       '--output', args.output]
            instagram_account_finder.main()
            
        elif args.command == 'download':
            # Build API key from environment
            api_key = os.getenv('RAPIDAPI_KEY')
            
            sys.argv = ['instagram_rapidapi.py',
                       '--username', args.username,
                       '--limit', str(args.limit),
                       '--download',
                       '--min-resolution', str(args.min_resolution),
                       '--output', args.output]
            
            if args.firebase:
                sys.argv.append('--firebase')
                
            # Execute with proper API key
            original_env = os.environ.copy()
            if api_key:
                os.environ['RAPIDAPI_KEY'] = api_key
                
            instagram_rapidapi.main()
            
        elif args.command == 'batch':
            sys.argv = ['batch_downloader.py',
                       '--input', args.input,
                       '--limit', str(args.limit),
                       '--resolution', str(args.resolution)]
            
            if args.start_from:
                sys.argv.extend(['--start-from', str(args.start_from)])
            if args.max_users:
                sys.argv.extend(['--max-accounts', str(args.max_accounts)])
                
            batch_downloader.main()
            
        elif args.command == 'config':
            if args.setup:
                setup_configuration()
            elif args.test_firebase:
                test_firebase_connection()
            else:
                config_parser.print_help()
                
    except Exception as e:
        print(f"Error: {e}")
        return 1

def setup_configuration():
    """Setup configuration files"""
    print("Setting up Instagram Tools configuration...")
    
    # Create config files if they don't exist
    config_dir = 'config'
    os.makedirs(config_dir, exist_ok=True)
    
    # Create .env file template
    instagram_tools_env_template = """# Instagram RapidAPI Configuration  
RAPIDAPI_KEY=your_rapidapi_key_here

# Firebase Configuration
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id  
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nyour_private_key_here\\n-----END PRIVATE KEY-----\\n"
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your_service_account_email

# Instagram Official API (for your own account)
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
"""
    
    env_file = os.path.join(config_dir, '.env')
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write(instagram_tools_env_template)
        print(f"Created {env_file}")
        print("Please edit this file with your actual API keys.")
    else:
        print(f"{env_file} already exists.")
    

def test_firebase_connection():
    """Test Firebase configuration"""
    try:
        from config.firebase_config import FirebaseManager
        print("Testing Firebase connection...")
        fb_manager = FirebaseManager()
        print("✓ Firebase connection successful!")
    except Exception as e:
        print(f"✗ Firebase connection failed: {e}")
        print("Please check your Firebase configuration.")

if __name__ == '__main__':
    sys.exit(main())
