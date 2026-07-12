import asyncio
import httpx
import time
import uuid

async def attempt_allocation(client, asset_id, employee_id):
    payload = {
        "asset_id": str(asset_id),
        "employee_id": str(employee_id),
        "allocated_date": "2026-07-12",
        "expected_return_date": "2026-07-20"
    }
    
    start_time = time.time()
    response = await client.post(
        "http://127.0.0.1:8000/allocations",
        json=payload
    )
    elapsed = time.time() - start_time
    
    return response.status_code, response.json(), elapsed

async def main():
    asset_id = uuid.uuid4() # We would hardcode a real asset ID here
    
    print(f"Testing concurrent allocations for asset: {asset_id}")
    
    async with httpx.AsyncClient() as client:
        # Fire 5 concurrent requests
        tasks = [
            attempt_allocation(client, asset_id, uuid.uuid4())
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        successes = 0
        conflicts = 0
        others = 0
        
        for status_code, data, elapsed in results:
            print(f"[{elapsed:.3f}s] Status: {status_code} | Response: {data}")
            if status_code == 201:
                successes += 1
            elif status_code == 409:
                conflicts += 1
            else:
                others += 1
                
        print(f"\nResults summary:")
        print(f"Successes: {successes} (Expected: 1)")
        print(f"Conflicts (409): {conflicts} (Expected: 4)")
        print(f"Other errors: {others}")

if __name__ == "__main__":
    asyncio.run(main())
