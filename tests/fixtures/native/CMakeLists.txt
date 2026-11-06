cmake_minimum_required(VERSION 3.20)
project(buffer_example C)
add_library(buffer buffer.c)
target_link_libraries(buffer PRIVATE platform)
