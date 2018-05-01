######################################################################
#
# The following 2 commands to compile pmvs2.
# > make depend
# > make
#
######################################################################
CXX = g++


# Your INCLUDE path (e.g., -I/usr/include)
YOURINCLUDEPATH =

# Your LDLIBRARY path (e.g., -L/usr/lib)
YOURLDLIBPATH =

CXXFLAGS = -O2 -Wall -Wno-deprecated ${YOURINCLUDEPATH}

LDFLAGS = ${YOURLDLIBPATH} -lXext -lX11 -ljpeg -lm -lpthread \
	-llapack -lgsl -lgslcblas

######################################################################
all: pmvs2

pmvs2: pmvs2.o detectFeatures.o dog.o harris.o point.o detector.o \
	findMatch.o detector.o expand.o filter.o optim.o \
	patchOrganizerS.o seed.o point.o option.o \
	image.o camera.o photoSetS.o patch.o photo.o \
	mylapack.o
	${CXX} ${LDFLAGS} -o $@ $^ ${LDFLAGS}

%.o : ../base/pmvs/%.cc
	$(CXX) -c $(CXXFLAGS) $<

%.o : ../base/image/%.cc
	$(CXX) -c $(CXXFLAGS) $<

%.o : ../base/numeric/%.cc
	$(CXX) -c $(CXXFLAGS) $<

######################################################################
# general commands
clean:
	/bin/rm -f core core.* *.o ${TARGET}

depend:
	rm -f Dependencies
	for SOURCEFILE in `ls *.cc ../base/*/*.cc ../base/*/*.c ../base/*/*.C ../base/*/*.f`; do \
	  echo $$SOURCEFILE; \
	  $(CXX) -MM $(CXXFLAGS) $$SOURCEFILE >> Dependencies; \
	done

-include Dependencies
