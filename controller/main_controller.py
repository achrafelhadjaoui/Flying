from data_validation import ConfigValidator

def validate_data(data: dict) -> None:
    """validate our entred data after parsing it
    """
    try:
        ConfigValidator(**data)
    except Exception as e:
        errors = []
        for error in e.errors():
            line = data["zones"][error['loc'][1]]["line"]
            message = f"{error['loc'][0]} {error['msg']}"
            errors.append(
                f"Line {line}, {message}"
            )
        raise ValueError("\n".join(errors)) from e