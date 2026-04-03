# Copyright 2019-2020, Collabora, Ltd.
# SPDX-License-Identifier: BSL-1.0

set(SOURCES filter_delaunay.cpp)

set(HEADERS filter_delaunay.h)

add_meshlab_plugin(filter_delaunay ${SOURCES} ${HEADERS})
