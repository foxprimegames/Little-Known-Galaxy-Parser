# unity_yaml_loader.py

import yaml
import re

def unity_constructor(loader, node):
    return loader.construct_mapping(node, deep=True)

def add_unity_yaml_constructors():
    yaml.add_multi_constructor('tag:unity3d.com,2011:', unity_constructor)

def preprocess_yaml_content(content):
    # Remove any problematic tags or characters
    content = re.sub(r'!u!\d+ &\d+', '', content)
    return content
