# We are not able to bundle some payloads because their licensing
# prohibits redistribution (notably sysinternals).  This script will
# will download non-redistributable payloads.  If you're deploying
# the plugin without interent access, you can copy this script to
# an internet connected host, run it, and then copy the resulting
# payloads back to the emu/payloads directory

curl -o payloads/AdFind.zip http://www.joeware.net/downloads/files/AdFind.zip
unzip payloads/AdFind.zip -d payloads/
cp payloads/AdFind.exe payloads/adfind.exe

curl -o payloads/dnscat2.ps1 https://raw.githubusercontent.com/lukebaggett/dnscat2-powershell/master/dnscat2.ps1

curl -o payloads/NetSess.zip http://www.joeware.net/downloads/files/NetSess.zip
unzip payloads/NetSess.zip -d payloads/
cp payloads/NetSess.exe payloads/netsess.exe

curl -o payloads/nbtscan.exe http://unixwiz.net/tools/nbtscan-1.0.35.exe

curl -o payloads/psexec.exe https://github.com/ropnop/impacket_static_binaries/releases/download/0.9.22.dev-binaries/psexec_windows.exe
cp payloads/psexec.exe payloads/PsExec.exe

curl -o payloads/putty.exe https://the.earth.li/~sgtatham/putty/latest/w64/putty.exe

curl -o payloads/secretsdump.exe https://github.com/ropnop/impacket_static_binaries/releases/download/0.9.22.dev-binaries/secretsdump_windows.exe

curl -o payloads/tcping.exe https://download.elifulkerson.com//files/tcping/0.39/tcping.exe

curl -o payloads/wce_v1_41beta_universal.zip https://www.ampliasecurity.com/research/wce_v1_41beta_universal.zip
unzip payloads/wce_v1_41beta_universal.zip -d payloads/

curl -o payloads/wmiexec.vbs https://raw.githubusercontent.com/Twi1ight/AD-Pentest-Script/master/wmiexec.vbs

curl -o payloads/psexec_sandworm.py https://raw.githubusercontent.com/SecureAuthCorp/impacket/c328de825265df12ced44d14b36c688cd9973f5c/examples/psexec.py
