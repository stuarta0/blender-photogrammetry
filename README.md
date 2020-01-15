# blender-photogrammetry

A photogrammetry addon for Blender 2.79 and 2.80 that allows conversion and processing between a number of photogrammetry formats, in addition to providing dense reconstruction straight from Blender's camera tracker. 

In the interests of remaining user friendly, this addon comes with all precompiled binaries required to process data.

Once enabled, the photogrammetry settings can be found in the Properties panel > Scene tab.

## Supported Formats

### Inputs:

* **Blender's motion tracker**: Allows reading of the tracker and reconstruction data from a tracked movie clip. Good for generating a dense point cloud of a tracked movie clip for reference, rendering or simulation.
* **Bundler**: Reads the bundler format consisting of a bundle.out and list.txt file.
* **COLMAP**: Reads a COLMAP model folder containing cameras, images and points3D files.
* **ImageModeler**: Reads an Autodesk ImageModeler .rzi file.
* **Meshroom**: Reads a Meshroom cameras.sfm file.
* **VisualSfM**: Reads the NVM file format.

### Outputs:

* **Blender**: From the given input, create cameras and mesh with vertices representing the point cloud from the input.
* **Bundler**: Output a bundle.out, list.txt and associated images to use with other photogrammetry tools.
* **PMVS**: Output the bundler file format, then run PMVS2 dense reconstruction on the dataset, resulting in a .ply point cloud.
* **COLMAP**: Output to a COLMAP workspace with sparse model, then run COLMAP dense reconstruction, resulting in a .ply point cloud, poisson mesh and delaunay triangular mesh. *Only available with CUDA GPUs on Windows*
* **VisualSfM**: Output to an NVM file with associated images to use with other photogrammetry tools.

**Note:** Since inputs are outputs can be mixed and matched, this addon can be used as a convertor between different photogrammetry formats (with the added benefit of having Blender integration).

## Usage

After processing a dense reconstruction in the format of choice, you can import the resulting .ply file back into Blender. Alternatively, use another tool like Meshlab to further process the data.

In the case where Blender's motion tracking data is processed, the resulting .ply mesh can be imported back into the tracking scene in Blender with the correct alignment to the original camera. When importing the .ply file, ensure you use ```+Z up```, ```+Y forward```.

**Note:** It's recommended you show the system console so you can track the progress of a reconstruction. Blender will become unresponsive whilst processing.

### Caveats

Precompiled binaries are provided for Linux and Windows on x86_64 hardware only. If you're using a different platform or architecture, you won't be able to process most formats.

If you'd like more platform support (like Mac), please compile the supporting binaries (Bundler, PMVS, COLMAP) and send through a pull request so others may benefit.

If you run into issues on linux, you may need to install ```libjpeg62``` and ```libgfortran3```.

## Roadmap

* Enable UI updates during processing if Blender 2.8 supports it (not feasible with Blender 2.79b)

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

In case you use this software, include an acknowledgement that PMVS2 was developed by Yasutaka Furukawa (University of Illinois at Urbana-Champaign, University of Washington) and Jean Ponce (University of Illinois at Urbana-Champaign, Ecole Normale Supérieure).

PMVS is distributed under the GNU General Public License.

For commercial licencing of the software, please contact Yasutaka Furukawa.

# Thanks

Special thanks to [Noah Snavely](https://github.com/snavely), the author of Bundler, for giving me some pointers on getting the right matrix representations in the bundle.out file. Also thanks to [Sebastian König](https://www.blendernetwork.org/sebastian-koenig) for help in testing the addon under Linux and with various datasets.

# License

Blender Photogrammetry Addon Copyright (C) 2019 Stuart Attenborrow

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
