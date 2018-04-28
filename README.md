# blender-photogrammetry

Blender importer/exporter for Bundler file format to allow dense point cloud reconstruction from Blender's camera tracker.

After tracking and solving a clip in Blender, use this addon to export the data to the Bundler file format. This format can be used in a number of photogrammetry tools to rebuild a dense point cloud. After dense point cloud reconstruction (and optional meshing), the resultant model can be reimported into the tracking scene in place.

The current implementation has been tested with PMVS on Windows as follows:

* Track and solve a movie clip
* Export Bundler .out file (exports bundle.out, list.txt and all associated movie clip frames in JPG format up to 3000px on the largest axis; see PMVS documentation)
* If you enabled "Convert to PMVS" or "Execute PMVS", a subfolder named pmvs\ will be created with the Bundler files converted and images undistorted, ready for PMVS
* If you enabled "Execute PMVS" then PMVS will be run against the converted data from the previous step

Precompiled binaries for Bundler and PMVS are provided for Linux x86, and Windows x86 & x86_64 to allow running the reconstruction pipeline. If you're using a different platform or architecture, "Convert to PMVS" and "Execute PMVS" will be unavailable. 
