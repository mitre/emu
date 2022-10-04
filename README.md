# CALDERA plugin: Emu

A plugin supplying CALDERA with TTPs from the Center for Threat Informed Defense Adversary Emulation Plans.

Each emulation plan will have an adversary and a set of facts. Please ensure to select the related facts to the 
adversary when starting an operation. Some adversaries may require additional payloads and executables to be 
downloaded. Run the `download_payloads.sh` script to download these binaries to the `payloads` directory.

Because some payloads within the Adversary Emulation Library are encrypted, a Python script is used to automate
the decryption which requires installation of some dependencies. Depending on the host OS, `pyminizip`
can be installed using the following:

- Ubuntu: `apt-get install zlib1g`
- MacOS: `homebrew install zlib`
- All OS's: `pip3 install -r requirements.txt`

See URL for more information regarding `pyminizip`: https://github.com/smihica/pyminizip

## Acknowledgements

- [Adversary Emulation Library](https://github.com/center-for-threat-informed-defense/adversary_emulation_library)
