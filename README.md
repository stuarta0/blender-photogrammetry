# blender-photogrammetry

Blender importer/exporter for Bundler file format to allow dense point cloud reconstruction from Blender's camera tracker.

After tracking and solving a clip in Blender, use this addon to export the data to the Bundler file format. This format can be used in a number of photogrammetry tools to rebuild a dense point cloud. After dense point cloud reconstruction (and optional meshing), the resultant model can be reimported into the tracking scene in place.

The current implementation has been tested with PMVS on 64-bit Windows 10 and 64-bit Ubuntu 17.10 as follows:

* Track and solve a movie clip
* Export Bundler .out file (exports bundle.out, list.txt and all associated movie clip frames in JPG format up to 3000px on the largest axis; see PMVS documentation)
* If you enabled "Convert to PMVS" or "Execute PMVS", a subfolder named pmvs\ will be created with the Bundler files converted and images undistorted, ready for PMVS
* If you enabled "Execute PMVS" then PMVS will be run against the converted data from the previous step

**Note**: If 'Convert to PMVS' or 'Execute PMVS' is enabled, it's recommended you show the system console so you can track the progress of the Bundler and PMVS processes. Blender will become unresponsive during this time.

### 'Convert to PMVS' and 'Execute PMVS' caveats

Precompiled binaries for Bundler and PMVS are provided for Linux 32 & 64, and Windows 32 & 64 to allow running the reconstruction pipeline. If you're using a different platform or architecture, "Convert to PMVS" and "Execute PMVS" will be unavailable via the addon.

### Debugging

To examine the output of a bundler file (to verify the 2D points for each image), run the following from the Python console:

```python
bpy.ops.debug.bundler_svg('INVOKE_DEFAULT')
```

This will open a file select screen where you can choose the bundle.out file. A new directory will be created named ```debug``` with SVGs for each image and it's associated points in 2D space.

## Sources

### Bundler

Project page and precompiled binaries: http://www.cs.cornell.edu/~snavely/bundler/

Source code: https://github.com/snavely/bundler_sfm

#### License

Bundler is distributed under the GNU General Public License. For information on commercial licensing, please contact the authors at the contact address below. If you use Bundler for a publication, please cite the following paper:

Noah Snavely, Steven M. Seitz, and Richard Szeliski. Photo Tourism: Exploring Photo Collections in 3D. SIGGRAPH Conf. Proc., 2006.

### PMVS

Project page: https://www.di.ens.fr/pmvs/

Source code and precompiled binaries: https://github.com/pmoulon/CMVS-PMVS

#### License

In case you use this software, include an acknowledgement that PMVS2 was developped by Yasutaka Furukawa (University of Illinois at Urbana-Champaign, University of Washington) and Jean Ponce (University of Illinois at Urbana-Champaign, Ecole Normale Supérieure).

PMVS is distributed under the GNU General Public License.

For commercial licencing of the software, please contact Yasutaka Furukawa.

# Thanks

Special thanks to Noah Snavely, the author of Bundler, for giving me some pointers on getting the right matrix representations in the bundle.out file.
