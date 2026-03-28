import asyncio
import aiohttp
import contextvars
import os
import sys
import time
import uuid

if sys.platform == "linux":
    import uvloop

x_token = contextvars.ContextVar('x_token')
userId = contextvars.ContextVar('user_id')
placeId = contextvars.ContextVar('place_id')
jobId = contextvars.ContextVar('job_id')
universeId = contextvars.ContextVar('universe_id')

if os.path.isfile("item.txt"):
    with open("item.txt", "r") as f:
        item = f.read()
        print(f"Due to the presence of item.txt, we will automatically be sniping {item}")
else:
    item = input("Enter the desired item id: ")

#Put your cookie in cookie.txt! Only the value though, not the key
with open("cookie.txt", "r") as f:
    cookie = f.read()

async def get_root_place_id(session, universe_id: int):
    async with session.get(f"https://develop.roblox.com/v1/universes/{universe_id}", cookies={'.ROBLOSECURITY': cookie}) as r:
        try:
            data = await r.json()
            if data:
                if data.get("rootPlaceId"):
                    return data["rootPlaceId"]
            print("Did not find root place id")
            return get_root_place_id(session, universe_id)
        except Exception as e:
            print(f"Failed to get root place: {e}")
            time.sleep(0.06)
            return get_root_place_id(session, universe_id)

async def init_vars(session):
    async with session.get("https://users.roblox.com/v1/users/authenticated", cookies={'.ROBLOSECURITY': cookie}) as check:
        info = await check.json()
        userId.set(info['id'])
        print(f"Hello {info['name']}!")

async def get_x_token(session):
    async with session.post("https://auth.roblox.com/v2/logout", cookies={".ROBLOSECURITY": cookie}) as r:
        print(f"csrf refreshed! {r.headers.get('x-csrf-token')}")
        x_token.set(r.headers.get("x-csrf-token"))

async def get_place_job_ids(session):
    userPresenceRequest = {
        "userIds": [userId.get()]
        }
    async with session.post("https://presence.roblox.com/v1/presence/users", cookies={".ROBLOSECURITY": cookie}, json=userPresenceRequest, headers={"x-csrf-token": x_token.get(), "content-type": "application/json"}) as r:
        try:
            data = await r.json()
            if data.get("userPresences"):
                myPresence = data["userPresences"][0]

                if myPresence.get("placeId"):
                    placeId.set(myPresence["placeId"])
                if myPresence.get("gameId"):
                    jobId.set(myPresence["gameId"])
                if myPresence.get("universeId"):
                    universeId.set(myPresence["universeId"])

                return myPresence.get("placeId"), myPresence.get("gameId"), myPresence.get("universeId")
            else:
                print(print(f"Could not find userPresences: {data}"))
                return False, False, False
        except Exception as e:
            print(f"Presence Exception: {e}")
            return False, False, False

async def check_sale(session, itemId):
    async with session.get(f"https://economy.roblox.com/v2/assets/{itemId}/details", headers={"x-csrf-token": x_token.get()}, cookies={".ROBLOSECURITY": cookie}) as r:
        try:
            data = await r.json()
            if data['CollectibleProductId'] and data['CollectibleItemId']:
                print(f"cid, pid: {data['CollectibleProductId']}, {data['CollectibleItemId']}")
                return data['CollectibleProductId'], data['CollectibleItemId'], data['PriceInRobux'], data['Creator']['CreatorTargetId'], data['Creator']['CreatorType'], data['SaleLocation']['UniverseIds']
            else:
                return False, False, False, False, False, False
        except:
            print(f"Rate limit on check? {r.status} || {await r.text()}")
            return False, False, False, False, False, False

async def buy(session, product, item, price, seller, seller_type):
    data = {"collectibleProductId": product, 
            "idempotencyKey": str(uuid.uuid4()), 
            "expectedPurchaserType": "User", 
            "expectedSellerId": seller, 
            "expectedPrice": price, 
            "expectedPurchaserId": userId.get(), 
            "expectedCurrency": 1, 
            "expectedSellerType": seller_type,
            "placeId": placeId.get(),
            }
    async with session.post(f"https://apis.roblox.com/marketplace-sales/v1/item/{item}/purchase-item", json=data, headers={"x-csrf-token": x_token.get(), "Roblox-Place-Id": str(placeId.get()), "Roblox-Game-Id": str(jobId.get()), "content-type": "application/json"}, cookies={".ROBLOSECURITY": cookie}) as r:
        print(r.headers)
        data = await r.json(content_type=None)
        print(data)
        if data:
            if 'errorMessage' in data and (data['errorMessage'] == "QuantityExhausted" or data['errorMessage'] == "QuantityLimitExceeded"):
                return False
            if 'purchased' in data and data['purchased']:
                print("Copy purchased.")
                return True
            else:
                print(f"Unknown Error: {data}")
                return True

async def main(itemId):
    connector = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(connector=connector) as session:
        await init_vars(session)
        await get_x_token(session)
        while True:
            timeout = time.time() + 300
            while time.time() < timeout:
                time.sleep(0.06) #32ms for me, try other values for yourself. Some people go as low as 25.
                cProductId, cItemId, cPrice, cSellerId, cSellerType, cSaleUniverseList = await check_sale(session, itemId)
                if cProductId:
                    await get_x_token(session)
                    print("Item is a collectible!")

                    if len(cSaleUniverseList) == 0:
                        print("Item is not sold in universes, aborting")
                        return

                    warnedPlaceIds = False
                    while True:
                        cPlaceId, cJobId, cUniverseId = await get_place_job_ids(session)
                        if cUniverseId and (cUniverseId in cSaleUniverseList):
                            print("Found player in correct universe!!")
                            break
                        elif not warnedPlaceIds:
                            print(f"You are not currently in one of the correct universes. The script will resume when you are detected to be in one. Join one of these placeIds:")
                            rootPlaceIds = []
                            for universe_id in cSaleUniverseList:
                                root_place_id = await get_root_place_id(session, universe_id)
                                rootPlaceIds.append(root_place_id)
                            print(f"{rootPlaceIds}")
                            warnedPlaceIds = True
                            
                        time.sleep(0.3)

                    print("PURCHASING!!!")
                    while True:
                        statuses = await asyncio.gather(
                            *[await asyncio.to_thread(buy, session, cProductId, cItemId, cPrice, cSellerId, cSellerType) for _ in range(0,1)]
                        )
                        print(statuses)
                        for status in statuses:
                            if status == False:
                                print("Sold out!")
                                return
                        return
                        #time.sleep(0.3)
            await get_x_token(session)

def init(itemId):
    try:
        if sys.platform == "win32": # Needed to silence event loop closed errors on Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(main(itemId))
        elif sys.version_info >= (3, 11) and sys.platform == "linux" : #If >= 3.11 use other method to initialize uvloop
            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                runner.run(main(itemId))
        elif sys.platform == "linux":
            uvloop.install()
            asyncio.run(main(itemId))
        else:
            print("Potentially unsupported platform, please report any bugs")
            asyncio.run(main(itemId))
    except KeyboardInterrupt: pass
    except Exception as err: 
        print(f"Error {err}")
        init(itemId)

init(item)

print(f"Sniping of {item} complete! Check your inventory.")