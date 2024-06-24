Collection of Parser Items for the Little-Known Galaxy wiki found at: https://lkg.wiki.gg/ <br>
Putting these into output files, so we can do a compare between patches, and only update pages that need it.

# Parser Collections --
dialogue_parser.py -- <br>
  Looks at a file folder: `Input/Assets/TextAsset` (should be replaced with each patch)<br>
  Parses the `English_NPCNAME.txt` files into a format used by the wiki. WIKI: Each region should be a section on the NPC's /Dialogue page. Emotes to text should be associated correctly.<br>
  Puts each file in file folder: Output/Dialogues<br>

email_parser.py -- <br>
  Looks at a email file in folder: `Input/Assets/TextAsset` (should be replaced with each patch)<br>
  Looks at asset files in `Input/Assets/MonoBehavior` to map email attachments.<br>
  Puts results in file folder: Output/Emails<br>

recipe_crafting_parser.py --<br>
  Looks at assets files in `Input/Assets/MonoBehavior` that start with `crafting_` to get a product, quantity, ingredients, quantity<br>
  Looks at the product to get category and assigns a machine based on that category.<br>
  Puts results in file folder: Output/Recipes<br>

recipe_machine_production_parser.py --<br>
  First generates a file of all assets in `Input/Assets/MonoBehavior` with a "machine production" section in their asset file.<br>
  Then uses that list to iterate through the .assets of that list and pulls out recipie information. <br>
  Sorts the results by product, in the correct recipies template. <br>
  Puts results in the file folder: Output/Recipes<br>

item_information_parser.py --<br>
  Looks at assets in `Input/Assets/MonoBehavior`, and creates a mock infobox template of item data.<br>
  Super versions of the same item are included in the base-item template.<br>
  Two results are generated - one with sell price, and one where the items can't be sold. This should make it easier to check for changes to sell price. <br>

shop_catalog_parser.py --<br>
  Looks at assets in `Input/Assets/MonoBehavior`, and creates a list of assets that start with `_StoreCatalog`.<br>
  It pulls out the `storeSets` information, then looks up all of the `storeItemsInSet` in each storeSet, then looks up the `itemForSale` to get the name of the item and buy price.<br>
  Formats everything in the shop template.<br>
  Outputs each shop into a different file in `Output/Shops`<br>

# Getting the Assets --
1. Download an application that allows you to look at the assets. I use [AssetRipper](https://github.com/AssetRipper/AssetRipper) for parsing and [AssetStudio](https://github.com/Perfare/AssetStudio) for sprites, and looking things up on the fly.
2. In the prefered asset manager, load the `Little-Known Galaxy_Data` folder.
  * Windows: `C:/Program Files (x86)/Steam/steamapps/common/Little-Known Galaxy/Little-Known Galaxy_Data`
  * Linux: `${HOME}/.steam/steam/steamapps/common/Little-Known Galaxy/Little-Known Galaxy_Data`
3. Export -> All Files/Assets (depending on your prefered application). Put it into a folder, I prefer to put it in a folder with the patch number, but you do  you.

## Directory Structure
```
├── AuxiliaryFiles
└── ExportedProject
    ├── Assets
    │   ├── AnimationClip
    │   ├── AnimatorController
    │   ├── AnimatorOverrideController
    │   ├── AudioClip
    │   ├── AudioMixerController
    │   ├── Editor
    │   ├── Font
    │   ├── LightingSettings
    │   ├── Material
    │   ├── Mesh
    │   ├── MonoBehaviour     # This is where the character and item data is.
    │   ├── PhysicsMaterial2D
    │   ├── Plugins
    │   ├── PrefabInstance
    │   ├── RenderTexture
    │   ├── Resources
    │   ├── Scenes
    │   ├── Scripts                  
    │   ├── Shader
    │   ├── Sprite
    │   ├── StreamingAssets
    │   ├── TextAsset         # This is where the files for the email and dialogue parser are
    │   └── Texture2D
    ├── Packages
    └── ProjectSettings
```