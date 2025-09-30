# Firebase 설정 가이드

Firebase Storage에 이미지를 업로드하려면 다음 단계를 따라 설정하세요.

## 1. Firebase 프로젝트 생성

1. [Firebase Console](https://console.firebase.google.com/)에 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력 (예: `instagram-fetcher`)
4. Google Analytics는 선택사항

## 2. Storage 설정

1. Firebase Console에서 "Storage" 메뉴 클릭
2. "시작하기" 클릭
3. 보안 규칙을 "테스트 모드"로 설정 (개발용)
4. 위치 선택 (가까운 지역)

## 3. Service Account 생성

1. Firebase Console에서 "프로젝트 설정" (톱니바퀴 아이콘) 클릭
2. "서비스 계정" 탭 클릭
3. "새 비공개 키 생성" 클릭
4. JSON 파일 다운로드

## 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your_project_id_here
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com

# Service Account 정보 (다운로드한 JSON 파일에서 복사)
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key_here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your_service_account_email

# RapidAPI (Instagram 스크래핑용)
RAPIDAPI_KEY=your_rapidapi_key_here
```

## 5. Storage 보안 규칙 (선택사항)

Firebase Console > Storage > 규칙에서 다음 규칙을 설정:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if true; // 개발용 - 프로덕션에서는 더 엄격한 규칙 필요
    }
  }
}
```

## 6. 테스트

웹 애플리케이션에서 "Firebase 업로드" 체크박스를 선택하고 이미지를 업로드해보세요.

## 문제 해결

### "The specified bucket does not exist" 오류
- `FIREBASE_PROJECT_ID`가 올바른지 확인
- Firebase Console에서 Storage가 활성화되어 있는지 확인

### "Firebase not configured" 메시지
- `.env` 파일이 프로젝트 루트에 있는지 확인
- 환경 변수 이름이 정확한지 확인

### 권한 오류
- Service Account에 Storage 권한이 있는지 확인
- Storage 보안 규칙을 확인
