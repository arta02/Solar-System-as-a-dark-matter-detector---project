# Set REBOUND_SRC to the path of the REBOUND source directory with rebound.h
REBOUND_SRC ?= $(HOME)/rebound-c-src/src
CXX ?= g++
CXXFLAGS ?= -O3 -std=c++17 -Wall -Wextra -pedantic

.PHONY: all clean
all: flyby_cpp

flyby_cpp: core_live_flyby_100k.cpp
	$(CXX) $(CXXFLAGS) -I$(REBOUND_SRC) $< -L$(REBOUND_SRC) -Wl,-rpath,$(REBOUND_SRC) -lrebound -lm -o $@

clean:
	rm -f flyby_cpp
