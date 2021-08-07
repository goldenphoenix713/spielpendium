import os
import sys
import zipfile
import json
from typing import Dict
from io import BytesIO

import pandas as pd

__all__ = ['save_spl', 'load_spl']


def save_spl(data: pd.DataFrame, filename: str) -> bool:
    images = extract_images(data)
    data['Images'] = 'images/' + data['BGG Id'] + '.png'
    json_data = json.dumps(json.loads(data.to_json(orient="index")), indent=4)

    with zipfile.ZipFile(filename, 'w') as file:
        file.write('data.json', json_data)


def load_spl(filename: str) -> pd.DataFrame:
    pass


def extract_images(data: pd.DataFrame) -> Dict[str, bytes]:
    images: pd.Series = data.Image
    images.index = data['BGG Id']
    return images.to_dict()
