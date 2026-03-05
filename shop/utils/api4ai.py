import requests
import base64
import os
from django.conf import settings
from datetime import datetime
import uuid
from django.contrib.auth.models import User
from shop.models import Product

API_URL = "https://api4ai.cloud/virtual-try-on/v1/results"
API_KEY = "a4a-2S8g7fpJb41F2ewahzzSQ5SLj5q6rZYS"


def call_tryon_api(person_path, cloth_path, product_id, user):
    try:
        print("USER IMAGE PATH:", person_path)
        print("CLOTH IMAGE PATH:", cloth_path)
        print(f"Product ID: {product_id}, User: {user.username}")
        with open(person_path, "rb") as person_file, open(cloth_path, "rb") as cloth_file:
            print("Files opened successfully")
            print("FINAL URL =", API_URL)
            response = requests.post(
                API_URL,
                headers={
                    "X-API-KEY": API_KEY
                },
                files={
                    "image": person_file,
                    "image-apparel": cloth_file
                },
                timeout=180
            )
        print("API STATUS CODE:", response.status_code)
        print("API RAW RESPONSE:", response.text[:500])
        if response.status_code != 200:
            print("API4AI HTTP ERROR - Status code:", response.status_code)
            return None
        data = response.json()
        print("👉 API JSON RESPONSE:", data)
        results = data.get("results", [])
        if not results:
            print("NO RESULTS FROM API")
            return None
        status = results[0].get("status", {})
        status_code = status.get("code", "").lower()
        print("API STATUS OBJECT:", status)
        if status_code not in ["success", "ok", "completed"]:
            print("API4AI PROCESSING FAILED:", status.get("message"))
            return None
        entities = results[0].get("entities", [])
        print("ENTITIES FROM API:", entities)
        if not entities:
            print("API RETURNED SUCCESS BUT NO IMAGE")
            return None
        entity = entities[0]
        img_base64 = entity["image"]
        img_format = entity.get("format", "png")
        result_dir = os.path.join(settings.MEDIA_ROOT, "tryon_results")
        os.makedirs(result_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        result_filename = f"tryon_result_{timestamp}_{unique_id}.{img_format}"
        result_full_path = os.path.join(result_dir, result_filename)
        with open(result_full_path, "wb") as f:
            f.write(base64.b64decode(img_base64))
        result_url = settings.MEDIA_URL + "tryon_results/" + result_filename
        print("RESULT SAVED AT:", result_url)
        from carts.models import TryOnResult
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            print(f"Product with ID {product_id} not found")
            return None
        # tryon_result = TryOnResult.objects.create(
        #     user=user,
        #     product=product,
        #     result_image_url=result_url
        # )
        # print(f"TryOn Result saved to database with ID: {tryon_result.id}")
        # return tryon_result
        if user and user.is_authenticated:
            tryon_result = TryOnResult.objects.create(
                user=user,
                product=product,
                result_image_url=result_url
            )
            print(f"TryOn Result saved to database with ID: {tryon_result.id}")
            return tryon_result
        else:
            print("ℹ️ Anonymous user — skipping DB save")

            class TempResult:
                result_image_url = result_url

            return TempResult()



    # Anonymous user — skip DB save, just return the URL as a simple object

    except Exception as e:
        print("GENERAL ERROR IN API4AI:", e)
        import traceback
        traceback.print_exc()
        return None


def get_latest_tryon_for_product(user, product_id):
    from carts.models import TryOnResult
    try:
        return TryOnResult.objects.filter(
            user=user,
            product_id=product_id
        ).latest('created_at')
    except TryOnResult.DoesNotExist:
        print(f"No try-on found for user {user.username} and product {product_id}")
        return None
    except Exception as e:
        print(f"Error getting latest tryon: {e}")
        return None