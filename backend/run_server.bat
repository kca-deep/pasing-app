@echo off
REM UTF-8 인코딩 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo   FastAPI 백엔드 서버 시작
echo ========================================
echo.
echo UTF-8 인코딩 설정 완료
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo FastAPI 서버 시작 중...
echo   주소: http://localhost:8000
echo   API 문서: http://localhost:8000/docs
echo.
echo 종료하려면 Ctrl+C를 누르세요
echo.

REM Uvicorn 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
