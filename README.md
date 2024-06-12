Git clone this repository<br>
Need unity installed (version 2022.3.12f1 is what I used)<br>
Need python version 3.10.6
Need various python libraries<br>
    - torch<br>
    - diffusers<br>
    - transformers<br>
are the main ones<br>
One you have the project downloaded, open it in unity<br>
Will need to turn of safe mode, due to some external library (can probably fix for release)<br>
Need to import the SteamVR package from the asset store<br>
Maybe VHACD as well<br>
Make sure the VR system you are using has SteamVR enabled as well<br>
Might have cuda issues too so make sure drivers are updated<br>
To run, there are two files you should be aware of<br>
Virtual networks in Config/virtual<br>
    These describe where things will be sent to in the network<br>
    for example microphone -> whisper -> stable diffusion<br>
Physical networks in Config/physical<br>
    These describe where the services are located<br>
    For example, microphone is unity and whisper is python<br>
The network object in unity controls how the network is setup<br>
Additionally a python script, run.py must be run and given the virtual and physical network names<br>
python run.py python -p dual -v full_system<br>
Both must be started for the application to run and the network names should match<br>
May need to manually assign the local and system mic inputs depending on what headset you are using<br>
Local mic being for NPCs and System mic being for system commands.<br>
