import asyncio
import httpx
import time


async def send_request(client, user_id):
    url = "http://127.0.0.1:8000/v1/npc/chat"
    payload = {"player_query": "play?",
                "session_id": f"test_session_{user_id}",
                "context_data": {}
    }  # 故意問同一個問題

    start_time = time.time()
    try:
        response = await client.post(url, json=payload, timeout=20.0)
        duration = time.time() - start_time
        print(f"User {user_id}: Status {response.status_code}, Time: {duration:.2f}s")
        return response.json()
    except Exception as e:
        # 💡 必須印出 e 的型別與內容，不要只印 Failed
        print(f"User {user_id} Failed: {type(e).__name__} -> {str(e)}")


async def main():
    # 💡 同時模擬 20 個併發請求
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(2)]
        print(f"🚀 開始發送 20 個併發請求...")
        results = await asyncio.gather(*tasks)
        print(f"✅ 測試完成！")


if __name__ == "__main__":
    asyncio.run(main())