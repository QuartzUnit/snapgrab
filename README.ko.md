# Snapgrab

[![PyPI](https://img.shields.io/pypi/v/snapgrab)](https://pypi.org/project/snapgrab/)
[![Python](https://img.shields.io/pypi/pyversions/snapgrab)](https://pypi.org/project/snapgrab/)
[![License](https://img.shields.io/github/license/QuartzUnit/snapgrab)](https://github.com/QuartzUnit/snapgrab/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen)]()

> [English](README.md)

URL을 스크린샷 + 메타데이터로 변환합니다. Claude Vision에 최적화되어 있습니다.

```python
from snapgrab import capture

result = await capture("https://example.com")
print(result.path)           # /tmp/snapgrab/example_com_desktop_20260317_120000.png
print(result.metadata.title) # "Example Domain"
print(result.vision_tokens)  # ~2764
```

## 기능

- **스크린샷 캡처** — PNG, JPEG, PDF 지원, 전체 페이지 캡처 가능
- **페이지 메타데이터** — 제목, 설명, Open Graph 태그, 파비콘, HTTP 상태
- **Claude Vision 최적화** — 1568px 자동 리사이즈, 토큰 비용 추정
- **뷰포트 프리셋** — 데스크톱 (1920x1080), 태블릿 (768x1024), 모바일 (375x812)
- **MCP 서버 내장** — Claude Code / MCP 클라이언트용 3개 도구
- **요소 캡처** — CSS 선택자로 특정 요소만 캡처
- **다크 모드** — 라이트/다크 컬러 스킴 강제 적용

## 설치

```bash
pip install snapgrab
```

최초 실행 시 Playwright 브라우저 설치가 필요합니다:
```bash
playwright install chromium
```

## 사용법

### Python API

```python
import asyncio
from snapgrab import capture

async def main():
    # 기본 스크린샷
    result = await capture("https://example.com")

    # 모바일 뷰포트, 전체 페이지
    result = await capture("https://example.com", viewport="mobile", full_page=True)

    # 다크 모드, JPEG 형식
    result = await capture("https://example.com", dark_mode=True, format="jpeg")

    # 특정 요소 캡처
    result = await capture("https://example.com", selector="#main-content")

    # 커스텀 뷰포트
    result = await capture("https://example.com", viewport=(1440, 900))

asyncio.run(main())
```

### CLI

```bash
snapgrab https://example.com                          # 기본 PNG
snapgrab https://example.com -v mobile -f             # 모바일, 전체 페이지
snapgrab https://example.com --format jpeg -q 90      # JPEG 품질 90
snapgrab https://example.com -s "#hero" --dark-mode   # 요소 + 다크 모드
snapgrab https://example.com -j                       # JSON 출력
snapgrab meta https://example.com                     # 메타데이터만
```

### MCP 서버

```bash
pip install "snapgrab[mcp]"
snapgrab-mcp  # stdio MCP 서버 시작
```

**도구:**
- `capture_screenshot` — URL 캡처 + 메타데이터 + Vision 토큰 추정
- `capture_comparison` — 데스크톱 vs 모바일 (또는 임의 뷰포트) 비교
- `extract_page_metadata` — 메타데이터만 추출 (스크린샷 없음)

## CaptureResult

```python
result.path            # 저장된 파일 경로
result.format          # "png", "jpeg", "pdf"
result.width           # 뷰포트 너비
result.height          # 페이지 높이 (full_page) 또는 뷰포트 높이
result.file_size       # 바이트
result.vision_tokens   # Claude Vision 토큰 비용 추정치
result.vision_path     # Vision 최적화 이미지 경로 (≤1568px)
result.processing_time_ms
result.metadata.title
result.metadata.description
result.metadata.og_title
result.metadata.og_image
result.metadata.favicon_url
result.metadata.status_code
result.metadata.url    # 리다이렉트 후 최종 URL
```

## 라이선스

[MIT](LICENSE)
