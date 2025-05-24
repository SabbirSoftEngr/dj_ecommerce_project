import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shop.models import Product

class Command(BaseCommand):
    help = "Import products from external API"

    def handle(self, *args, **kwargs):
        url = 'https://api.example.com/products'  # Replace with your API URL
        response = requests.get(url)
        if response.status_code == 200:
            products = response.json()
            for item in products:
                product, created = Product.objects.update_or_create(
                    slug=slugify(item['name']),
                    defaults={
                        'name': item['name'],
                        'price': item['price'],
                        'stock': item.get('stock', 0),
                        'short_desc': item.get('short_desc', ''),
                        'long_desc': item.get('long_desc', ''),
                        # Add other fields if needed
                    }
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} product: {product.name}")
        else:
            self.stderr.write(f"Failed to fetch products. Status code: {response.status_code}")
