cd %~dp0
cd win-tools
mkdir java-python
cd java-python
del %~dp0\win-tools\java-python\* /S /F /Q
rmdir %~dp0\win-tools\java-python\jdk /S /Q
rmdir %~dp0\win-tools\java-python\python /S /Q
..\wget.exe --no-check-certificate https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip
..\unzip.exe openjdk-11.0.2_windows-x64_bin.zip
timeout 5
move jdk-11.0.2 jdk
del *.zip
..\wget.exe --no-check-certificate https://www.python.org/ftp/python/3.7.2/python-3.7.2.post1-embed-amd64.zip
..\unzip.exe python-3.7.2.post1-embed-amd64.zip -d python
del *.zip
..\wget.exe --no-check-certificate https://www.python.org/ftp/python/3.7.2/python-3.7.2-amd64.exe
python-3.7.2-amd64.exe
cd %~dp0
SET mypath=%~dp0
SET mypathescaped=%mypath:\=/%
echo {"javapath": "%mypathescaped%win-tools/java-python/jdk/bin/java.exe", "tintpath": "%mypathescaped%tint/lib", "tintaddr": "localhost", "tintport": "8012", "sessions": []} > %USERPROFILE%\.brancfg
REM In futuro aggiungeremo anche git per fare il pull