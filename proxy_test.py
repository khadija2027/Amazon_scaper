import requests

response = requests.get(
url='https://proxy.scrapeops.io/v1/',
params={
    'api_key': '17c499b6-4cfa-4daa-876a-9bd0ff588808',
    'url': 'https://www.amazon.fr/product-reviews/B0CL9CG87N/?pageNumber=1', 
'render_js': 'true', 
},
)

print('Response Body: ', response.content)