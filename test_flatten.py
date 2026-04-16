def flatten_sequence(node):
    if not node:
        return []
    if node.get("type") == "sequence":
        res = []
        for item in node.get("items", []):
            res.extend(flatten_sequence(item))
        return res
    if node.get("type") == "term": # wait, terms are not explicit nodes, they are sequences or other types
        pass
    return [node]

# Let's test flattening
import json
node = {
  "type": "sequence",
  "items": [
    {
      "type": "sequence",
      "items": [
        {
          "type": "variable",
          "name": "n"
        },
        {
          "type": "symbol",
          "value": "\\to"
        }
      ]
    },
    {
      "type": "operator",
      "value": "+"
    },
    {
      "type": "symbol",
      "value": "\\infty"
    }
  ]
}

print(json.dumps(flatten_sequence(node), indent=2))
