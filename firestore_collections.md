# Firestore 컬렉션 구조 설계

## 📋 컬렉션 구조

### 1. **users** 컬렉션
사용자 프로필 및 계정 정보

```javascript
// 문서 ID: {userId} (Firebase Auth UID)
{
  "email": "user@example.com",
  "username": "john_doe",
  "displayName": "John Doe",
  "profileImage": "https://storage.googleapis.com/...",
  "createdAt": "2024-01-15T10:30:00Z",
  "lastLoginAt": "2024-01-20T15:45:00Z",
  "preferences": {
    "minResolution": 1080,
    "autoDownload": true,
    "notifications": true
  },
  "subscription": {
    "plan": "free", // free, premium, pro
    "expiresAt": null,
    "downloadLimit": 100
  }
}
```

### 2. **instagram_media** 컬렉션
Instagram 미디어 메타데이터

```javascript
// 문서 ID: 자동 생성
{
  "instagram_id": "1234567890123456789",
  "username": "natgeo",
  "caption": "Beautiful sunset...",
  "media_type": "IMAGE", // IMAGE, VIDEO, CAROUSEL
  "instagram_url": "https://instagram.com/p/ABC123/",
  "permalink": "https://instagram.com/p/ABC123/",
  "timestamp": "2024-01-15T10:30:00Z",
  "firebase_url": "https://storage.googleapis.com/...",
  "uploaded_at": "2024-01-15T10:35:00Z",
  "uploaded_by": "user123", // Firebase Auth UID
  "metadata": {
    "width": 1080,
    "height": 1080,
    "file_size": 245760,
    "format": "JPEG"
  },
  "engagement": {
    "likes": 1250,
    "comments": 45,
    "shares": 12
  },
  "tags": ["photography", "nature", "sunset"],
  "location": {
    "name": "Grand Canyon",
    "coordinates": {
      "lat": 36.1069,
      "lng": -112.1129
    }
  }
}
```

### 3. **downloads** 컬렉션
다운로드 히스토리 및 통계

```javascript
// 문서 ID: 자동 생성
{
  "user_id": "user123",
  "username": "natgeo",
  "downloaded_at": "2024-01-15T10:35:00Z",
  "media_count": 25,
  "total_size": 15728640, // bytes
  "resolution_filter": 1080,
  "method": "rapidapi", // rapidapi, scraper, manual
  "status": "completed", // pending, completed, failed
  "files": [
    {
      "filename": "natgeo_1.jpg",
      "firebase_url": "https://storage.googleapis.com/...",
      "size": 245760,
      "resolution": "1080x1080"
    }
  ]
}
```

### 4. **accounts** 컬렉션
발견된 Instagram 계정 정보

```javascript
// 문서 ID: {username}
{
  "username": "natgeo",
  "display_name": "National Geographic",
  "biography": "Bringing you the world...",
  "followers_count": 250000000,
  "following_count": 150,
  "posts_count": 15000,
  "is_verified": true,
  "is_private": false,
  "profile_image_url": "https://instagram.com/...",
  "external_url": "https://natgeo.com",
  "category": "photography",
  "discovered_at": "2024-01-15T10:30:00Z",
  "discovered_by": "user123",
  "last_scraped_at": "2024-01-15T10:35:00Z",
  "scrape_count": 1,
  "tags": ["photography", "nature", "travel", "wildlife"]
}
```

### 5. **public** 컬렉션
공개 데이터 (모든 사용자가 읽기 가능)

```javascript
// 문서 ID: 자동 생성
{
  "type": "featured_accounts",
  "title": "Featured Photography Accounts",
  "description": "Curated list of amazing photography accounts",
  "accounts": [
    {
      "username": "natgeo",
      "reason": "Stunning wildlife photography"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 6. **admin** 컬렉션
관리자 전용 데이터

```javascript
// 문서 ID: 자동 생성
{
  "type": "system_stats",
  "total_users": 1250,
  "total_downloads": 50000,
  "total_storage_used": 1073741824, // bytes
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## 🔍 쿼리 예시

### 사용자별 미디어 조회
```javascript
// 특정 사용자가 업로드한 미디어
db.collection('instagram_media')
  .where('uploaded_by', '==', userId)
  .orderBy('uploaded_at', 'desc')
  .limit(20)
```

### 해상도별 필터링
```javascript
// 1080p 이상 이미지만
db.collection('instagram_media')
  .where('metadata.width', '>=', 1080)
  .where('metadata.height', '>=', 1080)
  .orderBy('metadata.width', 'desc')
```

### 계정별 최신 미디어
```javascript
// 특정 계정의 최신 미디어
db.collection('instagram_media')
  .where('username', '==', 'natgeo')
  .orderBy('timestamp', 'desc')
  .limit(10)
```

### 사용자 다운로드 히스토리
```javascript
// 사용자의 다운로드 기록
db.collection('downloads')
  .where('user_id', '==', userId)
  .orderBy('downloaded_at', 'desc')
  .limit(50)
```

## 📊 필요한 색인

### instagram_media 컬렉션
```javascript
// 사용자별 최신 미디어
{
  "collectionGroup": "instagram_media",
  "queryScope": "COLLECTION",
  "fields": [
    {"fieldPath": "uploaded_by", "order": "ASCENDING"},
    {"fieldPath": "uploaded_at", "order": "DESCENDING"}
  ]
}

// 계정별 최신 미디어
{
  "collectionGroup": "instagram_media",
  "queryScope": "COLLECTION", 
  "fields": [
    {"fieldPath": "username", "order": "ASCENDING"},
    {"fieldPath": "timestamp", "order": "DESCENDING"}
  ]
}

// 해상도별 필터링
{
  "collectionGroup": "instagram_media",
  "queryScope": "COLLECTION",
  "fields": [
    {"fieldPath": "metadata.width", "order": "ASCENDING"},
    {"fieldPath": "metadata.height", "order": "ASCENDING"}
  ]
}
```

### downloads 컬렉션
```javascript
// 사용자별 다운로드 히스토리
{
  "collectionGroup": "downloads",
  "queryScope": "COLLECTION",
  "fields": [
    {"fieldPath": "user_id", "order": "ASCENDING"},
    {"fieldPath": "downloaded_at", "order": "DESCENDING"}
  ]
}
```

## 🚀 마이그레이션 계획

1. **기존 데이터 백업**
2. **새 컬렉션 구조 생성**
3. **데이터 마이그레이션 스크립트 작성**
4. **기존 코드 업데이트**
5. **테스트 및 검증**
