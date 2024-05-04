import os
import re
import hou
from collections import defaultdict
from pprint import pprint

def longest_common_prefix(strings):
    """Find the longest common prefix string amongst an array of strings."""
    if not strings:
        return ""
    
    # Start by assuming the whole of the first string is the common prefix
    prefix = strings[0]

    # Compare the assumed prefix with each string in the list
    for string in strings:
        # Reduce the prefix in length until it matches the start of each string
        while not string.startswith(prefix):
            prefix = prefix[:-1]
            if prefix == "":
                return ""
    
    return prefix



def list_textures():    
    # Let the user select a directory
    folder_path = hou.ui.selectFile(title="Select Folder of Textures", collapse_sequences=False, file_type=hou.fileType.Directory)
    if not folder_path:
        hou.ui.displayMessage("No folder selected.")
        return []
    # Read all filenames and find the longest common prefix for base name
    filenames = os.listdir(folder_path)
    prefixes = [filename.split('_', 1)[0] for filename in filenames if '_' in filename]
    common_prefix = longest_common_prefix(prefixes)

    # Dictionary to hold grouped textures
    texture_sets = defaultdict(lambda: defaultdict(list))

    # Regex to parse the filenames using the common prefix
    pattern = re.compile(rf"^{common_prefix}_([^_]+(?:_[^_]+)*)_(\w+)_?(ACES - ACEScg)?\.(\d{4})\.exr$")

    # Traverse the specified folder
    for file_name in filenames:
        match = pattern.match(file_name)
        if match:
            set_name, texture_type, color_space, udim = match.groups()
            normalized_name = f"{set_name}_{texture_type}"
            if color_space:
                normalized_name += f"_{color_space}"
            normalized_name += ".<UDIM>.exr"
            
            # Group by set and texture type
            texture_sets[set_name][texture_type].append(normalized_name)

    # Organizing the data for output
    organized_textures = {}
    for set_name, types in texture_sets.items():
        for type_name, files in types.items():
            base_name = f"{common_prefix}_{set_name}"
            filename = files[0]  # Assuming we want to show one example per type with UDIM normalized
            organized_textures[f"{base_name}_{type_name}"] = {
                "base_name": base_name,
                "filename": filename
            }

    return organized_textures
    

def list_texture_sets():
    # Let the user select a directory
    folder_path = hou.ui.selectFile(title="Select Folder of Textures", collapse_sequences=False, file_type=hou.fileType.Directory)
    if not folder_path:
        hou.ui.displayMessage("No folder selected.")
        return []
        
    # Read all filenames and find the longest common prefix for base name
    filenames = os.listdir(folder_path)
    common_prefix = longest_common_prefix(filenames)
    
    print(f"Common prefix: {common_prefix}\n")
    
    # Dictionary to hold grouped textures
    texture_sets = defaultdict(lambda: defaultdict(set))

    # Regex to parse filenames and group them into sets
    pattern = re.compile(r"^(?i)(" + re.escape(common_prefix) + r")(.*)_(BaseColor|Emissive|Height|Normal|Metallic|Roughness|Glossiness|Gloss|Opacity|Transmission)(.)?(ACES - ACEScg|raw|srgb|rgb)?(.\d{4})?(\.exr|\.png|\.tiff|\.tif|.jpg)*$")
    
    # Traverse the specified folder
    for file_name in os.listdir(folder_path):
        match = pattern.match(file_name)
        if match:
            base_name, texture_name, texture_type, spacer, color_space, udim, ext = match.groups()
            normalized_name = f"{base_name}{texture_name}_{texture_type}{spacer}{color_space}"
            if udim:
                normalized_name += ".<UDIM>"
            normalized_name += ext
            texture_sets[texture_name][texture_type].add(normalized_name)  # Using set to add unique items

    # Convert sets to lists for output
    organized_textures = defaultdict(dict)
    for set_name, types in texture_sets.items():
        for type_name, files in types.items():
            organized_textures[set_name][type_name] = list(files)

    return organized_textures
    
def get_textures_for_set(texture_sets, set_name):
    # Return all textures for a specific set
    return texture_sets.get(set_name, [])

# Example usage

print('\n\nTextures:\n\n')
texture_sets  = list_texture_sets()
pprint(texture_sets)


set_name = "underside"  
print('\n\nTexture Set ' + set_name + '\n')
textures = get_textures_for_set(texture_sets, set_name)
pprint(textures)



