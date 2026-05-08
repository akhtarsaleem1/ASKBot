import requests
import json
from askbot.config import get_settings

def test():
    s = get_settings()
    query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        types {
          ...FullType
        }
      }
    }
    fragment FullType on __Type {
      kind
      name
      fields(includeDeprecated: true) {
        name
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
    }
    fragment InputValue on __InputValue {
      name
      type { ...TypeRef }
    }
    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
          }
        }
      }
    }
    """
    res = requests.post(
        'https://api.buffer.com', 
        json={"query": query},
        headers={'Authorization': 'Bearer ' + s.buffer_api_key}
    )
    with open('scratch/schema.json', 'w') as f:
        json.dump(res.json(), f)
    print("Schema downloaded")

if __name__ == '__main__':
    test()
