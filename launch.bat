@echo off

set LAUNCHPATH=%CD%
pushd %~dp0
python src\main.py --launch-path %LAUNCHPATH% %*
popd
