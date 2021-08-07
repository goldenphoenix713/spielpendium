import zipfile
import json
from typing import Dict
from io import BytesIO

import pandas as pd
from PIL import Image

__all__ = ['save_spl', 'load_spl']


def save_spl(data: pd.DataFrame, filename: str) -> bool:
    images = extract_images(data)
    data['Image'] = 'images/' + data['BGG Id'] + '.png'
    json_data = json.dumps(json.loads(data.to_json(orient="index")), indent=4)

    with zipfile.ZipFile(filename, 'w') as file:
        file.writestr('data.json', json_data)
        
        for file, image in images.items():
            image_bytes = BytesIO()
            image.save(image_bytes, "PNG")
            file.writestr(data.loc[data['BGG Id'] == file, 'Image'], image_bytes.get_value())
            
    return True

def load_spl(filename: str) -> pd.DataFrame:
    pass


def extract_images(data: pd.DataFrame) -> Dict[str, Image.Image]:
    images: pd.Series = data['Image']
    images.index = data['BGG Id']
    return images.to_dict()
