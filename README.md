# Instagram Image Fetcher

A web-based tool for downloading and managing Instagram content with resolution filtering and Firebase integration.

## 🌐 Web Interface

Modern, minimalist web interface with dark theme.

### Quick Start
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies (for Puppeteer scraper)
npm install

# Start web server
python3 web_app.py
```

Then visit: **http://localhost:8080**

### Features
- ✅ **Instagram Account Scraping** (via Puppeteer)
- ✅ **Manual Image Upload** by URL
- ✅ **Resolution Filtering** (400px - 1920px)
- ✅ **Account Management** (view existing downloads)
- ✅ **Image Preview & Gallery**
- ✅ **Firebase Storage Integration** (optional)
- ✅ **Dark Minimalist UI**

## 🏗️ Project Structure

```
Abric Util Manager/
├── web_app.py                      # Main Flask web application
├── config.py                       # Centralized configuration
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies (Puppeteer)
├── .env                           # Environment variables (create from env.example)
├── env.example                    # Environment variables template
│
├── src/                           # Source modules
│   ├── instagram_scraper.py       # Web scraper wrapper
│   ├── firebase_config.py         # Firebase integration
│   ├── utils.py                   # Utility functions
│   └── ...
│
├── instagram_node_scraper.py      # Puppeteer-based scraper
│
├── templates/                     # HTML templates
│   ├── index.html                # Main page
│   └── gallery.html              # Gallery view
│
├── output/                        # Output directory
│   └── downloads/                # Downloaded images by username
│       ├── username1/
│       ├── username2/
│       └── ...
│
├── config/                        # Configuration files
│   ├── config_example.py         # Config template
│   └── firebase_env_example.txt  # Firebase setup example
│
├── docs/                          # Documentation
├── FIREBASE_SETUP.md             # Firebase setup guide
└── firestore.rules               # Firestore security rules
```

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.8+
- Node.js 14+ (for Puppeteer scraper)
- pip & npm

### 2. Install Dependencies

```bash
# Python dependencies
pip3 install -r requirements.txt

# Node.js dependencies (Puppeteer)
npm install
```

### 3. Environment Configuration

Create `.env` file from template:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
# Flask Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8080

# File Paths
UPLOAD_FOLDER=output/downloads
TEMPLATE_FOLDER=templates

# Instagram API (Optional - for RapidAPI backup)
RAPIDAPI_KEY=your_rapidapi_key_here

# Firebase Configuration (Optional)
FIREBASE_PROJECT_ID=your_project_id_here
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key_here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_CLIENT_ID=your_client_id

# Image Processing Settings
DEFAULT_MIN_RESOLUTION=800
MAX_IMAGE_SIZE=10485760
```

### 4. Firebase Setup (Optional)

For Firebase Storage integration, follow the guide in `FIREBASE_SETUP.md`.

## 📖 Usage

### Start the Server

```bash
python3 web_app.py
```

Server will start at `http://localhost:8080`

### Fetch Images from Instagram

1. Enter Instagram username
2. Select minimum resolution
3. Click "Fetch Images"
4. Preview and download images

### Manual Image Upload

1. Click "Manual Image Upload"
2. Select existing account or enter new username
3. Paste image URLs (one per line)
4. Optionally enable Firebase upload
5. Click "Upload"

### View Gallery

After downloading images, click "View Full Gallery" to see all images for a user.

## 🔧 Configuration

### Resolution Options
- 400px (Low quality)
- 800px (Default)
- 1200px (High quality)
- 1920px (Full HD)

### Scraping Methods
1. **Puppeteer (Primary)**: Headless browser scraping
2. **RapidAPI (Backup)**: API-based scraping (requires API key)

## 📊 API Endpoints

- `GET /` - Main page
- `GET /api/status` - API status check
- `GET /api/accounts` - List all downloaded accounts
- `GET /api/account/<username>/images` - Get images for specific account
- `POST /api/fetch` - Fetch images from Instagram
- `POST /api/manual_upload` - Upload images from URLs
- `GET /gallery/<username>` - Gallery view for user
- `GET /download/<username>/<filename>` - Download specific image

## 🎨 UI Features

### Dark Theme
- Background: `#121212`
- Text: `#f5f5f5`
- Borders: `1.2px solid #f5f5f5`
- Minimalist "skeleton" design
- Hover effects with color inversion

### Account Management
- View existing accounts
- See total images and storage size
- Check last update time
- Preview recent images

## ⚠️ Important Notes

### Legal & Ethical Guidelines
- **Respect Terms of Service**: Only download publicly available content
- **Rate Limiting**: Built-in delays to prevent abuse
- **Personal Use**: For personal projects, not commercial redistribution
- **Attribution**: Credit original content creators

### Technical Considerations
- Puppeteer requires Chrome/Chromium
- Instagram may block repeated requests
- Firebase is optional but recommended for backup
- Large downloads may take time

## 🐛 Troubleshooting

### Puppeteer Issues
```bash
# Reinstall Puppeteer
npm install puppeteer --force
```

### Port Already in Use
```bash
# Change PORT in .env
PORT=8081
```

### Firebase Errors
- Check `FIREBASE_SETUP.md`
- Verify environment variables
- Ensure service account has proper permissions

## 📝 Development

### File Organization
- Keep downloaded images in `output/downloads/<username>/`
- Temporary scraper files in `temp_scrapes/` (auto-cleaned)
- Cache in `__pycache__/` (gitignored)

### Adding Features
1. Update `web_app.py` for backend logic
2. Modify `templates/index.html` for UI
3. Add utilities to `src/utils.py`

## 🔒 Security

- Never commit `.env` file
- Keep Firebase credentials secure
- Use environment variables for sensitive data
- `.gitignore` configured for security

## 📞 Support

For issues:
1. Check console logs in terminal
2. Verify environment variables
3. Test API connectivity
4. Review browser developer console

---

**Note**: This tool is for educational and personal use. Always respect copyright laws and platform terms of service.