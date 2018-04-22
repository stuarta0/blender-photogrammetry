# blundle
Blender + Bundler = Blundle

Blender importer/exporter for Bundler file format to allow dense point cloud reconstruction from Blender's camera tracker.

After tracking and solving a clip in Blender, use this addon to export the data to the Bundler file format. This format can be used in a number of photogrammetry tools to rebuild a dense point cloud. After dense point cloud reconstruction (and optional meshing), the resultant model can be reimported into the tracking scene in place.

The current implementation has been tested with PMVS on Windows as follows:

* Track and solve a movie clip
* Export Bundler .out file (exports bundle.out, list.txt and all associated movie clip frames in JPG format up to 3000px on the largest axis; see PMVS documentation)
* Assuming you exported the file "bundle.out" to the empty directory "C:\export\path\":

```
> cd C:\export\path\
> Bundle2PMVS.exe list.txt bundle.out pmvs\

# copying the process from the auto-generated prep_pmvs.sh script on Windows:
> RadialUndistort.exe list.txt bundle.out pmvs\
> cd pmvs
> mkdir models
> mkdir txt
> mkdir visualize

# overly complicated method for copying only the *.txt files from RadialUndistort (and not list.txt or pmvs_options.txt)
> for /f "delims=" %x in ('dir /B *.txt ^| findstr "^[0-9]*\.txt$"') do move %x txt

# *.jpg need to be moved with rename (TBA; in the meantime see prep_pmvs.sh that was generated when running Bundle2PMVS.exe)
> ...
```

* Edit list.rd.txt and update *.jpg the same as the move with rename command
* Edit pmvs_options.txt and change useVisData to 0
* Finally, run:

```
C:\export\path\pmvs\> pmvs2.exe .\ pmvs_options.txt
```

If all goes well, you'll have a dense point cloud in the models folder.

