build_lib_example(
  NAME link-performance
  SOURCE_FILES link-performance.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libmobility}
    ${libnetwork}
    ${libwifi}
    ${libsimplewireless}
)
