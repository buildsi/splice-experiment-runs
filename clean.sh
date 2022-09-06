#!/bin/bash

declare -a paths=("/opt/hostedtoolcache/Java_Adopt_jdk" "/usr/share/dotnet" "/usr/share/dotnet" "/opt/az" "/usr/share/az*" "/opt/microsoft" "/opt/hostedtoolcache/Ruby" "/usr/local/aws-cli" "/opt/R" "/usr/share/R" "/opt/*.zip" "/opt/*.tar.gz" "/usr/share/*.zip" "/usr/share/*.tar.gz" "/opt/*.zip" "/opt/*.tar.gz" "/usr/share/*.zip" "/usr/share/*.tar.gz" "/usr/local/lib/android" "/opt/hhvm" "/opt/hostedtoolcache/CodeQL" "/opt/hostedtoolcache/CodeQL" "/opt/hostedtoolcache/node" "/opt/hostedtoolcache/pipx" "/opt/hostedtoolcache/pipx_bin" "/opt/pipx" "/opt/pipx_bin" "/opt/hostedtoolcache/PyPi" "/var/cache/snapd/" "~/snap")

for path in "${paths[@]}"; do
   printf "rm -rf ${path}\n"
   rm -rf ${path}  
done
