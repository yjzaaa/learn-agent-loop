"""
AgentCore API Test Script

测试 AgentCore API 端点
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1/agentcore"


def test_create_session():
    """测试创建会话"""
    print("\n[TEST] Create Session")
    print("-" * 50)
    
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={
            "name": "Test Session",
            "workdir": "./test_workspace"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Session created: {data['session_id']}")
        return data['session_id']
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return None


def test_list_sessions():
    """测试列出会话"""
    print("\n[TEST] List Sessions")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/sessions")
    
    if response.status_code == 200:
        data = response.json()
        sessions = data.get('sessions', [])
        print(f"✓ Found {len(sessions)} sessions")
        for s in sessions:
            print(f"  - {s['name']} ({s['id']})")
        return sessions
    else:
        print(f"✗ Failed: {response.status_code}")
        return []


def test_get_session(session_id: str):
    """测试获取会话详情"""
    print(f"\n[TEST] Get Session: {session_id}")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Session found:")
        print(f"  Name: {data.get('session', {}).get('name')}")
        print(f"  Status: {data.get('session', {}).get('status')}")
        print(f"  Steps: {len(data.get('timeline', []))}")
        return data
    else:
        print(f"✗ Failed: {response.status_code}")
        return None


def test_run_agent(session_id: str):
    """测试运行 Agent"""
    print(f"\n[TEST] Run Agent: {session_id}")
    print("-" * 50)
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/run",
        json={"query": "List all files in current directory"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Agent executed:")
        print(f"  Status: {data.get('status')}")
        print(f"  Steps: {data.get('steps')}")
        return data
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        return None


def test_get_timeline(session_id: str):
    """测试获取执行时间线"""
    print(f"\n[TEST] Get Timeline: {session_id}")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/timeline")
    
    if response.status_code == 200:
        data = response.json()
        timeline = data.get('timeline', [])
        print(f"✓ Timeline retrieved ({len(timeline)} steps)")
        for step in timeline[:5]:  # 只显示前5步
            print(f"  Step {step['step_number']}: {step['type']} - {step['status']}")
        return data
    else:
        print(f"✗ Failed: {response.status_code}")
        return None


def test_get_graph(session_id: str):
    """测试获取执行图谱"""
    print(f"\n[TEST] Get Graph: {session_id}")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/graph")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Graph retrieved:")
        print(f"  Steps: {len(data.get('steps', []))}")
        print(f"  Tool Calls: {len(data.get('tool_calls', []))}")
        return data
    else:
        print(f"✗ Failed: {response.status_code}")
        return None


def main():
    print("=" * 60)
    print("AgentCore API Test")
    print("=" * 60)
    
    # 测试列出会话
    sessions = test_list_sessions()
    
    # 测试创建会话
    session_id = test_create_session()
    if not session_id:
        print("\n✗ Cannot continue without session")
        sys.exit(1)
    
    # 测试获取会话
    test_get_session(session_id)
    
    # 测试运行 Agent
    print("\n[!] Running agent (this may take a while)...")
    result = test_run_agent(session_id)
    
    if result:
        # 测试获取时间线
        test_get_timeline(session_id)
        
        # 测试获取图谱
        test_get_graph(session_id)
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
