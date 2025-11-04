#!/usr/bin/env python3
"""
Dify Knowledge Base Document Upload Script

이 스크립트는 텍스트 파일을 Dify Knowledge Base에 업로드하고 자동으로 벡터화합니다.

참고: create_by_file API에 현재 인증 문제가 있어 create_by_text API를 사용합니다.
      텍스트 기반 업로드는 동일한 벡터화 결과를 제공합니다.
"""

import requests
import json
import time
import sys

# Configuration
API_BASE_URL = "http://kca-ai.kro.kr:5001/v1"
DATASET_ID = "abebef8c-0cfc-4911-9f57-4dd1292b2535"
API_KEY = "dataset-tTuWMwOLTw6Lhhmihan6uszE"

def upload_document(file_path, document_name=None):
    """
    텍스트 파일을 Dify Knowledge Base에 업로드하고 벡터화합니다.

    Args:
        file_path: 업로드할 파일 경로
        document_name: 문서 이름 (None이면 파일명 사용)

    Returns:
        dict: 업로드 결과 (document_id, batch_id 포함)
    """
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

    # Set document name
    if document_name is None:
        import os
        document_name = os.path.basename(file_path)

    # Prepare request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": document_name,
        "text": content,
        "indexing_technique": "high_quality",
        "process_rule": {
            "mode": "automatic"  # 또는 "custom"으로 세부 설정 가능
        }
    }

    # Upload document
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create_by_text"
    print(f"📤 Uploading document: {document_name}")
    print(f"   File: {file_path}")
    print(f"   Size: {len(content)} characters")

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            document_id = result['document']['id']
            batch_id = result['batch']
            indexing_status = result['document']['indexing_status']

            print(f"✅ Upload successful!")
            print(f"   Document ID: {document_id}")
            print(f"   Batch ID: {batch_id}")
            print(f"   Initial Status: {indexing_status}")

            return {
                'document_id': document_id,
                'batch_id': batch_id,
                'success': True
            }
        else:
            error = response.json()
            print(f"❌ Upload failed: {error['message']}")
            return {'success': False, 'error': error}

    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return {'success': False, 'error': str(e)}

def check_indexing_status(batch_id, wait=True):
    """
    문서의 벡터화 상태를 확인합니다.

    Args:
        batch_id: 업로드 시 반환된 batch ID
        wait: True면 완료될 때까지 대기

    Returns:
        dict: 벡터화 상태 정보
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{batch_id}/indexing-status"

    print(f"\n🔍 Checking vectorization status...")

    while True:
        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                result = response.json()
                documents = result['data']

                if documents:
                    doc = documents[0]
                    status = doc['indexing_status']
                    completed = doc['completed_segments']
                    total = doc['total_segments']

                    print(f"   Status: {status}")
                    print(f"   Progress: {completed}/{total} segments")

                    if status == 'completed':
                        print(f"✅ Vectorization completed!")
                        print(f"   Completed at: {doc['completed_at']}")
                        return {'success': True, 'status': status, 'data': doc}

                    elif status in ['error', 'paused', 'stopped']:
                        print(f"❌ Vectorization {status}")
                        if doc.get('error'):
                            print(f"   Error: {doc['error']}")
                        return {'success': False, 'status': status, 'data': doc}

                    elif wait:
                        print(f"   Waiting for completion...")
                        time.sleep(2)
                        continue
                    else:
                        return {'success': True, 'status': status, 'data': doc}
                else:
                    print(f"❌ No documents found for batch {batch_id}")
                    return {'success': False, 'error': 'No documents found'}
            else:
                error = response.json()
                print(f"❌ Status check failed: {error}")
                return {'success': False, 'error': error}

        except Exception as e:
            print(f"❌ Exception during status check: {e}")
            return {'success': False, 'error': str(e)}

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 dify_upload_document.py <file_path> [document_name]")
        print("\nExample:")
        print("  python3 dify_upload_document.py /path/to/document.txt")
        print("  python3 dify_upload_document.py /path/to/document.txt 'My Document Name'")
        sys.exit(1)

    file_path = sys.argv[1]
    document_name = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 60)
    print("Dify Knowledge Base - Document Upload & Vectorization")
    print("=" * 60)

    # Upload document
    result = upload_document(file_path, document_name)

    if result and result['success']:
        # Check vectorization status
        status_result = check_indexing_status(result['batch_id'], wait=True)

        if status_result['success']:
            print("\n" + "=" * 60)
            print("✅ Document successfully uploaded and vectorized!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("⚠️  Document uploaded but vectorization incomplete")
            print("=" * 60)
            return 1
    else:
        print("\n" + "=" * 60)
        print("❌ Upload failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())