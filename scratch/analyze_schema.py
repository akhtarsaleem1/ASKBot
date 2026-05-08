import json
with open('scratch/schema.json') as f:
    schema = json.load(f)

types = schema['data']['__schema']['types']
for t in types:
    if t.get('name') == 'Channel':
        print(f"Type: {t['name']}")
        fields = t.get('fields') or []
        for f in fields:
            print("  ", f['name'], '->', f['type']['name'] if f['type'].get('name') else f['type']['kind'])
