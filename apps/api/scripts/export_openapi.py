"""Export the API contract without connecting to PostgreSQL or Auth0."""

import json
from pathlib import Path

from lingora.main import create_app


def main() -> None:
    destination = Path(__file__).resolve().parents[3] / "packages/api-client/openapi.json"
    schema = create_app().openapi()
    destination.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Exported {destination.relative_to(destination.parents[2])}")


if __name__ == "__main__":
    main()
