#!/usr/bin/env python3
"""
Instagram Account Finder - Find accounts that post content you like
"""

import requests
import json
import argparse
from typing import List, Dict
import os

class InstagramAccountFinder:
    def __init__(self):
        """Initialize Instagram Account Finder"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_hashtag_accounts(self, hashtag: str, limit: int = 50) -> List[Dict]:
        """
        Find accounts that post content with specific hashtags
        
        Args:
            hashtag: Hashtag to search (without #)
            limit: Maximum number of accounts to return
            
        Returns:
            List of account information
        """
        try:
            # This is a simplified example - you'd need to implement actual hashtag search
            # Using mock data for demonstration
            print(f"Searching for accounts using #{hashtag}...")
            
            mock_accounts = [
                {
                    'username': 'naturephotographer',
                    'full_name': 'Nature Photographer',
                    'followers_count': 125000,
                    'biography': 'Capturing beauty of nature 🌿📸 | Outdoor enthusiast',
                    'is_verified': True,
                    'profile_pic_url': 'https://example.com/profile1.jpg'
                },
                {
                    'username': 'architecture_art',
                    'full_name': 'Architecture & Art',
                    'followers_count': 89000,
                    'biography': 'Modern architecture and contemporary art 🏗️🎨',
                    'is_verified': False,
                    'profile_pic_url': 'https://example.com/profile2.jpg'
                },
                {
                    'username': 'designinspiration',
                    'full_name': 'Design Inspiration',
                    'followers_count': 245000,
                    'biography': 'Daily design inspiration and creative ideas ✨',
                    'is_verified': True,
                    'profile_pic_url': 'https://example.com/profile3.jpg'
                }
            ]
            
            return mock_accounts[:limit]
            
        except Exception as e:
            print(f"Error searching hashtag accounts: {e}")
            return []
    
    def get_explore_accounts(self, category: str = "all", limit: int = 50) -> List[Dict]:
        """
        Get popular accounts from Instagram explore
        
        Args:
            category: Category filter (all, photography, design, travel, etc.)
            limit: Maximum number of accounts to return
            
        Returns:
            List of account information
        """
        try:
            print(f"Getting explore accounts for {category}...")
            
            explore_accounts = [
                {
                    'username': 'natgeo',
                    'full_name': 'National Geographic',
                    'followers_count': 235000000,
                    'biography': 'Inspiring people to care about the planet 🌍',
                    'is_verified': True,
                    'category': 'photography',
                    'profile_pic_url': 'https://example.com/natgeo.jpg'
                },
                {
                    'username': 'tastemade',
                    'full_name': 'Tastemade',
                    'followers_count': 5600000,
                    'biography': 'Food & lifestyle inspiration 🍽️',
                    'is_verified': True,
                    'category': 'food',
                    'profile_pic_url': 'https://example.com/tastemade.jpg'
                },
                {
                    'username': 'archilovers',
                    'full_name': 'Archilovers',
                    'followers_count': 1200000,
                    'biography': 'Architecture and design community 🏗️',
                    'is_verified': True,
                    'category': 'design',
                    'profile_pic_url': 'https://example.com/archil.jpg'
                }
            ]
            
            if category != "all":
                explore_accounts = [acc for acc in explore_accounts if acc.get('category') == category]
            
            return explore_accounts[:limit]
            
        except Exception as e:
            print(f"Error getting explore accounts: {e}")
            return []
    
    def get_category_accounts(self, category: str, min_followers: int = 10000) -> List[Dict]:
        """
        Get accounts from specific categories
        
        Args:
            category: Category (photography, design, travel, food, art, etc.)
            min_followers: Minimum follower count
            
        Returns:
            List of account information
        """
        categories = {
            'photography': [
                {'username': 'natgeo', 'full_name': 'National Geographic', 'followers_count': 235000000},
                {'username': 'earthpix', 'full_name': 'Earth Pictures', 'followers_count': 8900000},
                {'username': 'bbearth', 'full_name': 'BBC Earth', 'followers_count': 4200000},
                {'username': 'natgeo', 'full_name': 'National Geographic Travel', 'followers_count': 8900000}
            ],
            'design': [
                {'username': 'design', 'full_name': 'Design', 'followers_count': 1800000},
                {'username': 'dezeen', 'full_name': 'Dezeen', 'followers_count': 2300000},
                {'username': 'architecturaldigest', 'full_name': 'Architectural Digest', 'followers_count': 3800000},
                {'username': 'designmilk', 'full_name': 'Design Milk', 'followers_count': 1200000}
            ],
            'interior': [
                {'username': 'luxuryhome', 'full_name': 'Luxury Home', 'followers_count': 2800000},
                {'username': 'homepolish', 'full_name': 'HomePolish', 'followers_count': 1500000},
                {'username': 'interior', 'full_name': 'Interior Design', 'followers_count': 3200000}
            ],
            'food': [
                {'username': 'foodnetwork', 'full_name': 'Food Network', 'followers_count': 8900000},
                {'username': 'tastemade', 'full_name': 'Tastemade', 'followers_count': 5600000},
                {'username': 'bonappetitmag', 'full_name': 'Bon Appétit', 'followers_count': 4200000}
            ],
            'art': [
                {'username': 'metmuseum', 'full_name': 'The Metropolitan Museum', 'followers_count': 1800000},
                {'username': 'moma', 'full_name': 'The Museum of Modern Art', 'followers_count': 1200000},
                {'username': 'artgallery', 'full_name': 'Art Gallery', 'followers_count': 890000}
            ]
        }
        
        accounts = categories.get(category, [])
        
        # Filter by minimum followers
        filtered_accounts = [acc for acc in accounts if acc['followers_count'] >= min_followers]
        
        return filtered_accounts
    
    def save_accounts_list(self, accounts: List[Dict], filename: str = "found_accounts.json"):
        """Save found accounts to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(accounts)} accounts to {filename}")
    
    def display_accounts(self, accounts: List[Dict]):
        """Display accounts in a nice format"""
        print(f"\n=== Found {len(accounts)} Accounts ===")
        print("=" * 60)
        
        for i, account in enumerate(accounts, 1):
            followers = account.get('followers_count', 0)
            followers_str = f"{followers:,}" if followers >= 1000 else str(followers)
            
            if followers >= 1000000:
                followers_display = f"{followers/1000000:.1f}M"
            elif followers >= 1000:
                followers_display = f"{followers/1000:.1f}K"
            else:
                followers_display = str(followers)
            
            verified = "✓" if account.get('is_verified', False) else ""
            
            print(f"{i:2d}. @{account.get('username', 'unknown')} {verified}")
            print(f"     {account.get('full_name', 'No name')}")
            print(f"     Followers: {followers_display}")
            
            biography = account.get('biography', '')
            if biography:
                print(f"     Bio: {biography[:50]}{'...' if len(biography) > 50 else ''}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Instagram Account Finder')
    parser.add_argument('--method', choices=['hashtag', 'explore', 'category'], required=True,
                       help='Search method')
    parser.add_argument('--query', help='Hashtag/category to search')
    parser.add_argument('--limit', type=int, default=20, help='Number ofaccounts to find')
    parser.add_argument('--min-followers', type=int, default=10000, help='Minimum follower count')
    parser.add_argument('--output', default='found_accounts.json', help='Output file')
    
    args = parser.parse_args()
    
    finder = InstagramAccountFinder()
    accounts = []
    
    try:
        if args.method == 'hashtag':
            if not args.query:
                print("Error: --query is required for hashtag search")
                return
            accounts = finder.get_hashtag_accounts(args.query, args.limit)
            
        elif args.method == 'explore':
            accounts = finder.get_explore_accounts(args.query or 'all', args.limit)
            
        elif args.method == 'category':
            if not args.query:
                print("Available categories: photography, design, interior, food, art")
                return
            accounts = finder.get_category_accounts(args.query, args.min_followers)
        
        if accounts:
            finder.display_accounts(accounts)
            finder.save_accounts_list(accounts, args.output)
            
            print(f"\n=== Next Steps ===")
            print("To download posts from these accounts, use:")
            print("python3 instagram_rapidapi.py --username <username> --download --min-resolution 800")
            print(f"\nSelected accounts to try:")
            for account in accounts[:5]:
                print(f"python3 instagram_rapidapi.py --username {account['username']} --limit 10 --download --min-resolution 1080")
        else:
            print("No accounts found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
