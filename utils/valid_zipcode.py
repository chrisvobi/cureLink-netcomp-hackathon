def is_valid_zip(zip_code):
    return zip_code.isdigit() and len(zip_code) in [5, 6]