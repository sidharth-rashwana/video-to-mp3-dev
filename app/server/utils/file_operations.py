import json
import aiofiles

async def is_valid_json(content):
    try:
        json.loads(content)
        return True
    except ValueError:
        return False
    
async def read_file(file_path):
    """
    To read files as bytes

    Args: 
        file_path (str) : path of the html file
    
    Returns:
        bytes : file bytes
    """
    async with aiofiles.open(file_path, mode='rb') as file:
        content = await file.read()
    return content
