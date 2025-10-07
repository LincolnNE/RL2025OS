#!/bin/bash
# Vercel 배포 스크립트

echo "🚀 Instagram Util Manager - Vercel 배포 준비"
echo "=============================================="

# 1. Git 상태 확인
echo "📋 Git 상태 확인..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  커밋되지 않은 변경사항이 있습니다."
    echo "다음 파일들이 변경되었습니다:"
    git status --porcelain
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 배포가 취소되었습니다."
        exit 1
    fi
fi

# 2. 필요한 파일들 확인
echo "📁 필요한 파일들 확인..."
required_files=("vercel.json" "requirements.txt" "web_app.py" "env.example")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 필수 파일이 없습니다: $file"
        exit 1
    else
        echo "✅ $file"
    fi
done

# 3. 환경 변수 파일 확인
echo ""
echo "🔧 환경 변수 설정 확인..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "env.example을 복사하여 .env 파일을 생성하세요:"
    echo "cp env.example .env"
    echo "그리고 필요한 API 키들을 설정하세요."
    exit 1
fi

# 4. Git 커밋 및 푸시
echo ""
echo "📤 Git 커밋 및 푸시..."
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main

echo ""
echo "✅ 배포 준비 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. https://vercel.com/dashboard 에서 새 프로젝트 생성"
echo "2. GitHub 저장소 연결"
echo "3. 환경 변수 설정 (VERCEL_DEPLOYMENT.md 참조)"
echo "4. 배포 실행"
echo ""
echo "📖 자세한 가이드는 VERCEL_DEPLOYMENT.md 파일을 참조하세요."
