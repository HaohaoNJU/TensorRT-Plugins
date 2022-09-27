cd build
cmake .. -DTENSORRT_ROOT=${TRT_DIR}
make -j20
export LD_LIBRARY_PATH=$PWD:$LD_LIBRARY_PATH
