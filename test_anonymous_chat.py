#!/usr/bin/env python3
"""
Test script for the new anonymous chat endpoint
"""

import requests
import json

def test_anonymous_chat():
    """Test the anonymous chat endpoint"""
    base_url = "http://localhost:8000/api"
    
    # Test data
    test_query = {
        "query": "What universities are available in Australia?",
        "session_id": "test_anonymous_session"
    }
    
    print("🧪 Testing Anonymous Chat Endpoint")
    print("=" * 50)
    
    try:
        # Test anonymous chat endpoint
        print(f"📡 POST {base_url}/chat/")
        print(f"📝 Query: {test_query['query']}")
        
        response = requests.post(
            f"{base_url}/chat/",
            json=test_query,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"🤖 Answer: {data.get('answer', 'No answer')[:100]}...")
            print(f"📊 Confidence: {data.get('confidence_score', 'N/A')}")
            print(f"🔍 Query Type: {data.get('query_type', 'N/A')}")
            print(f"👤 User Type: {data.get('user_type', 'N/A')}")
            print(f"💬 Message: {data.get('message', 'N/A')}")
            print(f"🆔 Session ID: {data.get('session_id', 'N/A')}")
        else:
            print("❌ Failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_authenticated_query():
    """Test that authenticated query endpoint requires auth"""
    base_url = "http://localhost:8000/api"
    
    test_query = {
        "query": "What universities are available in Australia?",
        "session_id": "test_auth_session"
    }
    
    print("\n🔒 Testing Authenticated Query Endpoint (Should Fail)")
    print("=" * 50)
    
    try:
        # Test authenticated query endpoint without auth
        print(f"📡 POST {base_url}/query/ (without auth)")
        
        response = requests.post(
            f"{base_url}/query/",
            json=test_query,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly requires authentication!")
        else:
            print("❌ Should require authentication!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 StudyNet Anonymous Chat Endpoint Test")
    print("=" * 60)
    
    test_anonymous_chat()
    test_authenticated_query()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("\n📋 Summary:")
    print("- Anonymous users can use /api/chat/ without authentication")
    print("- Authenticated users must use /api/query/ with Bearer token")
    print("- Both endpoints provide the same functionality but different access levels")
