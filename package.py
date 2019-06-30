import zipfile
import os
import shutil

packages = [
    {
        "name": "blender-photogrammetry-1.0-linux",
        "platform": "linux",
        "features": ["blender", "bundler", "imagemodeler", "pmvs"],
    },
    {
        "name": "blender-photogrammetry-1.0-windows",
        "platform": "windows",
        "features": ["blender", "bundler", "colmap", "imagemodeler", "pmvs"],
    },
    {
        "name": "blender-photogrammetry-1.0-windows-no-colmap",
        "platform": "windows",
        "features": ["blender", "bundler", "imagemodeler", "pmvs"],
    }
]

for package in packages:
    print(f"Creating {package['name']}...")
    basepath = os.path.join("release", package["name"])
    try:
        if os.path.exists(basepath):
            shutil.rmtree(basepath)
    except Exception as ex:
        print(ex)
    os.makedirs(basepath, exist_ok=True)
    
    for feature in package["features"]:
        os.makedirs(os.path.join(basepath, feature))
        for filename in os.listdir(feature):
            filepath = os.path.join(feature, filename)
            if os.path.isfile(filepath):
                shutil.copy(filepath, os.path.join(basepath, feature))
        try:
            binpath = os.path.join(feature, package["platform"])
            if os.path.exists(binpath):
                shutil.copytree(binpath, os.path.join(basepath, feature, "bin"))
        except Exception as ex:
            print(ex)
    
    shutil.make_archive(os.path.join("release", package["name"]), "zip", basepath)