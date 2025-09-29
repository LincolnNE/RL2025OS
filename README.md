# Instagram Tools

A comprehensive toolset for downloading and managing Instagram content with resolution filtering and Firebase integration.

## 🏗️ Project Structure

```
instagram_tools/
├── main.py                 # Unified entry point
├── requirements.txt        # Dependencies
├── config/                 # Configuration files
│   └── .env.example       # Environment variables template
├── src/                    # Source code
│   ├── instagram_api.py           # Official Instagram Basic Display API
│   ├── instagram_rapidapi.py      # RapidAPI Instagram scraper
│   ├── instagram_account_finder.py # Account discovery tools
│   ├── batch_downloader.py        # Batch processing
│   ├── firebase_config.py         # Firebase integration
│   └── firebase_web_config.py     # Firebase web config
├── output/                 # Generated files
│   ├── images/            # Downloaded images
│   ├── found_accounts.json       # Discovered accounts
│   └── posts.json         # Post metadata
└── docs/                   # Documentation
```

## 🚀 Quick Start

### 1. Installation

```bash
cd instagram_tools
pip3 install -r requirements.txt
```

### 2. Configuration

```bash
# Setup configuration files
python3 main.py config --setup

# Test Firebase connection
python3 main.py config --test-firebase
```

### 3. Basic Usage

```bash
# Find photography accounts
python3 main.py find --method category --query photography --limit 10

# Download high-quality images
python3 main.py download natgeo --limit 20 --min-resolution 1080 --firebase

# Batch process multiple accounts
python3 main.py batch --input output/found_accounts.json --limit 5 --resolution 800
```

## 🎯 Main Features

### Account Discovery
- **Category-based search**: Find accounts by niche (photography, design, travel)
- **Exploration**: Discover popular accounts
- **Filtering**: Set minimum follower counts and verification status

### Content Download
- **Multiple sources**: Official API, RapidAPI, web scraping
- **Resolution filtering**: Download only high-quality images (800px+, 1080p+, 4K)
- **Metadata extraction**: Captions, likes, comments, timestamps

### Batch Processing
- **Multi-account support**: Process hundreds of accounts
- **Progress tracking**: Detailed statistics and error reporting
- **Resume capability**: Continue from interruption points

### Firebase Integration
- **Storage upload**: Automatically upload images to Firebase Storage
- **Metadata sync**: Save post information to Firestore
- **Organized structure**: Categorized storage paths

## 📋 Available Commands

### Account Discovery
```bash
# Find accounts by category
python3 main.py find --method category --query photography --limit 20

# Search explore pages
python3 main.py find --method explore --limit 15

# Filter by follower count
python3 main.py find --method category --query design --min-followers 50000
```

### Content Download
```bash
# Download with resolution filtering
python3 main.py download username --min-resolution 1080 --download-dir output/images

# Upload to Firebase
python3 main.py download username --firebase --limit 15

# Save metadata only
python3 main.py download username --output output/posts.json
```

### Batch Operations
```bash
# Process account list
python3 main.py batch --input output/found_accounts.json --limit 10 --resolution 1080

# Process subset of accounts
python3 main.py batch --input accounts.json --start-from 10 --max-accounts 50

# Full pipeline with Firebase
python3 main.py batch --input accounts.json --firebase --limit 5
```

### Configuration
```bash
# Setup environment
python3 main.py config --setup

# Test Firebase
python3 main.py config --test-firebase
```

## 🔧 Environment Setup

### Required Environment Variables

Create `config/.env`:

```bash
# RapidAPI (for public accounts)
RAPIDAPI_KEY=your_rapidapi_key

# Firebase (for storage)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nyour_key\\n-----END PRIVATE KEY-----\\n"
FIREBASE_CLIENT_EMAIL=your_service_account_email

# Official Instagram API (own account only)
INSTAGRAM_ACCESS_TOKEN=your_token
```

### API Keys

1. **RapidAPI**: Sign up at [rapidapi.com](https://rapidapi.com) for Instagram scraper APIs
2. **Firebase**: Create project at [firebase.google.com](https://firebase.google.com) and generate service account key
3. **Instagram**: Use for your own account content only

## 📊 Output Structure

### Image Organization
```
output/images/
├── username1_20250101_120000.jpg
├── username1_20250101_130000.jpg
├── username2_20250102_140000.jpg
└── username2_20250102_150000.jpg
```

### Metadata Files
- `found_accounts.json`: Discovered account information
- `posts.json`: Post metadata with Firebase URLs
- `batch_download_results.json`: Batch processing statistics

## ⚠️ Important Notes

### Legal & Ethical Guidelines
- **Respect terms of service**: Only download publicly available content
- **Rate limiting**: Built-in delays to prevent API abuse
- **Personal use**: Intended for personal projects, not commercial redistribution
- **Attribution**: Properly credit original content creators

### Performance Considerations
- **Resolution filtering**: Automatically skips low-quality images
- **Parallel processing**: Multiple accounts processed efficiently
- **Memory management**: Large images handled with streaming
- **Error recovery**: Automatic retry and error reporting

## 🛠️ Development

### Adding New Sources
1. Create new `instagram_*.py` in `src/`
2. Add entry point in `main.py`
3. Follow existing API patterns for consistency

### Customization
- **Categories**: Add new account categories in `instagram_account_finder.py`
- **Filters**: Extend resolution and quality filters
- **Storage**: Modify Firebase upload paths and organization

## 📞 Support

For issues and feature requests, please check:
1. Configuration setup (`python3 main.py config --setup`)
2. Firebase connectivity (`python3 main.py config --test-firebase`)
3. API key validity
4. Rate limiting adherence

---

**Note**: This tool is for educational and personal use. Always respect copyright laws and platform terms of service.
