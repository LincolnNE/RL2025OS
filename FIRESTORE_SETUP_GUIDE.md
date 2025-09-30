# Firestore Database 설정 가이드

## ❌ 현재 문제
```
Firebase upload failed: 404 The database (default) does not exist for project abric-auth
```

Firestore 데이터베이스가 생성되지 않아서 메타데이터 저장이 실패하고 있습니다.

## ✅ 해결 방법

### 1. Firebase Console 접속
https://console.firebase.google.com/project/abric-auth/firestore

### 2. Firestore Database 생성

1. **"Create database" 버튼 클릭**

2. **모드 선택**
   - **Production mode** 선택 (보안 규칙 적용)
   - 또는 **Test mode** 선택 (개발 중)

3. **위치 선택**
   - 권장: `asia-northeast3` (서울)
   - 또는 가까운 지역 선택

4. **완료**

### 3. 보안 규칙 설정 (Production mode 선택 시)

Firestore → Rules 탭에서:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // instagram_media collection
    match /instagram_media/{mediaId} {
      allow read, write: if true;  // 테스트용 (모든 접근 허용)
    }
    
    // 기타 컬렉션
    match /{document=**} {
      allow read, write: if true;  // 테스트용
    }
  }
}
```

**게시(Publish) 버튼 클릭!**

### 4. 완료 확인

Firestore Database가 생성되면:
- Data 탭에서 빈 데이터베이스 확인
- 이제 Firebase 업로드 버튼이 작동합니다!

## 🎯 생성 후 테스트

웹 UI에서:
1. Instagram 이미지 가져오기
2. 🔥 Firebase 버튼 클릭
3. ✅ Uploaded 메시지 확인
4. Firebase Console → Firestore → Data에서 데이터 확인

## 📊 저장되는 데이터 구조

```javascript
instagram_media/{mediaId}
  ├─ media_id: "username_timestamp_id"
  ├─ instagram_id: "post_shortcode"
  ├─ url: "firebase_storage_url"
  ├─ username: "username"
  ├─ caption: "post_caption"
  ├─ media_type: "IMAGE"
  ├─ width: 1080
  ├─ height: 1080
  ├─ upload_method: "web_ui_upload"
  └─ timestamp: "2025-09-30T14:00:00"
```

## ⚠️ 주의사항

- **Test mode**는 30일 후 자동으로 만료됩니다
- 프로덕션 환경에서는 인증 규칙을 추가하세요
- 현재는 테스트용으로 모든 접근을 허용하고 있습니다
