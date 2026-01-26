from pydantic import BaseModel

def pretty_format_model(model_name: str, model: BaseModel):
    """
    Return a pretty formatted string for the data model.
    """
    model_str = f"\nModel: {model_name}\n"
    model_str += "-" * (len(model_name) + 7) + "\n"
    for field_name, field_info in model.model_fields.items():
        model_str += f"{field_name}: {field_info}\n"
    model_str += "-" * (len(model_name) + 7) + "\n"
    return model_str
