from jsonschema import validate, ValidationError
from fastapi import HTTPException
import json

from app.boot.exceptions import APIException

def validate_params_with_schema(params: dict, schema_str: str) -> bool:
    """
    验证参数是否符合给定的 JSON Schema
    """
    try:
        schema = json.loads(schema_str)
        validate(instance=params, schema=schema)
        return True
    except json.JSONDecodeError:
        raise APIException(status_code=400, msg="Invalid JSON schema format")
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Params validation failed: {e.message} at {'.'.join(map(str, e.path))}"
        )
    except Exception as e:
        raise APIException(status_code=500, msg=f"Validation error: {str(e)}")