def class_validator(object, request):
    for key, value in request.items():
        if value == getattr(object, key):
            print(f"Objeto {object} has value {value}")
        else:
            raise Exception(f"{key} is not in the created object")
    return True
