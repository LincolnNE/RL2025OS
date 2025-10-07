# Vercel 배포 가이드

이 가이드는 Instagram Util Manager를 Vercel에 배포하는 방법을 설명합니다.

## 📋 사전 준비사항

1. **Vercel 계정**: [vercel.com](https://vercel.com)에서 계정 생성
2. **GitHub 저장소**: 프로젝트가 GitHub에 업로드되어 있어야 함
3. **API 키들**: 필요한 서비스들의 API 키 준비

## 🚀 배포 단계

### 1. GitHub에 코드 푸시

```bash
# 현재 디렉토리에서
git add .
git commit -m "Add Vercel deployment configuration"
git push origin main
```

### 2. Vercel에서 프로젝트 연결

1. [Vercel Dashboard](https://vercel.com/dashboard)에 로그인
2. "New Project" 클릭
3. GitHub 저장소 선택
4. 프로젝트 이름 설정 (예: `instagram-util-manager`)

### 3. 환경 변수 설정

Vercel 대시보드에서 **Settings > Environment Variables**에서 다음 변수들을 추가:

#### 필수 환경 변수
```
SECRET_KEY=your_secret_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

#### 선택적 환경 변수 (기능별)
```
# Firebase (이미지 저장용)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key_here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your_service_account_email

# 이미지 업스케일링 API들
REPLICATE_API_TOKEN=your_replicate_api_token
DEEP_AI_API_KEY=your_deepai_api_key
UPSCALE_MEDIA_API_KEY=your_upscale_media_api_key
LETS_ENHANCE_API_KEY=your_lets_enhance_api_key

# Instagram 공식 API
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
```

### 4. 빌드 설정 확인

Vercel이 자동으로 다음을 감지해야 합니다:
- **Framework**: Python
- **Build Command**: 자동 감지
- **Output Directory**: 자동 감지
- **Install Command**: `pip install -r requirements.txt`

### 5. 배포 실행

1. "Deploy" 버튼 클릭
2. 빌드 로그 확인
3. 배포 완료 후 URL 확인

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 빌드 실패
- **원인**: 의존성 설치 실패
- **해결**: `requirements.txt`의 패키지 버전 확인

#### 2. 환경 변수 오류
- **원인**: 환경 변수가 제대로 설정되지 않음
- **해결**: Vercel 대시보드에서 환경 변수 재확인

#### 3. Firebase 연결 실패
- **원인**: Firebase 서비스 계정 키 오류
- **해결**: Firebase 콘솔에서 새 서비스 계정 생성

#### 4. API 요청 실패
- **원인**: RapidAPI 키가 유효하지 않음
- **해결**: RapidAPI 대시보드에서 키 상태 확인

### 로그 확인 방법

1. Vercel 대시보드 > 프로젝트 > Functions 탭
2. 함수 실행 로그 확인
3. 에러 메시지 분석

## 📱 배포 후 테스트

배포가 완료되면 다음 기능들을 테스트해보세요:

1. **메인 페이지**: 웹 인터페이스 접근
2. **API 상태**: `/api/status` 엔드포인트 확인
3. **이미지 다운로드**: 테스트 계정으로 이미지 다운로드 테스트
4. **Firebase 업로드**: Firebase 연동 테스트 (설정된 경우)

## 🔄 업데이트 배포

코드 변경 후 재배포:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Vercel이 자동으로 새 배포를 시작합니다.

## 📊 모니터링

- **Vercel Analytics**: 트래픽 및 성능 모니터링
- **Function Logs**: 서버 로그 확인
- **Environment Variables**: 설정값 관리

## 💡 최적화 팁

1. **이미지 크기 제한**: 대용량 이미지 처리 시 타임아웃 주의
2. **API 호출 제한**: RapidAPI 사용량 모니터링
3. **캐싱**: 자주 사용되는 데이터 캐싱 고려
4. **CDN**: 정적 파일은 Vercel CDN 활용

## 🆘 지원

문제가 발생하면:
1. Vercel 문서: [vercel.com/docs](https://vercel.com/docs)
2. 프로젝트 이슈: GitHub Issues 활용
3. 로그 분석: Vercel 대시보드의 Function Logs 확인

---

**배포 완료 후 URL**: `https://your-project-name.vercel.app`
