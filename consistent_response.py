import openai
import os
import pyaudio
import wave
import tkinter as tk
from tkinter import messagebox

class PageItem:
    def __init__(self, name, position, rotation):
        self.name = name
        self.position = position
        self.rotation = rotation

openai.api_key = "sk-proj-KT0u3nPKXdhIX1axxFtoT3BlbkFJjtB1hW7lceVDFbsh7zRi"


#Send input into chatgpt4o
def generate_text(history):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": 'You are an interior designer working in a 2D Euclidean space with an x and y axis. You have to make decisions about scene descriptions and output the correct translation xy and rotation in degrees of each individual object. Here is an example for a Dinner table formation: "[PageItem("Bar", [0, 0], 0), PageItem("Barstool", [-150, -50], 0), PageItem("Barstool", [-50, -50], 0), PageItem("Barstool", [50, -50], 0), PageItem("Barstool",[150, -50], 0)". Please only respond in python code without code block syntax around it and so each PageItem is in a new line and output the positions and rotation and Item name in string format, together they are wrapped in [] brackets like a python list and only when you are asked to generate a scene. Usually you work in 100 units, so each object is around 100 units, so you need to leave enough space between each object so they don\'t overlap'},
        ] + history,
    )
        
    result = response.choices[0].message.content
    # turn the result into actual usable python code from string
    # item_list = eval(result)
    return result


def record_audio(file_name, duration, sample_rate=44100, channels=2, chunk_size=1024):
    # Create an interface to PortAudio
    audio = pyaudio.PyAudio()

    # Open a stream with the specified parameters
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)

    print("Recording...")

    frames = []

    # Record for the specified duration
    for _ in range(0, int(sample_rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(data)

    print("Recording finished")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    audio.terminate()

    # Save the recorded data as a .wav file
    with wave.open(file_name, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    #messagebox.showinfo("Info", "Recording finished and saved as {}".format(file_name))
def start_recording():
    # Parameters
    file_name = "output.wav"
    duration = 7  # Duration in seconds
    record_audio(file_name, duration)
# Start an empty conversation
 

    # Load audio file and get transcript
    audio_file = open("output.wav", "rb")
    transcript = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    print(transcript.text)
    # Add transcription text to conversation history
    conversation_history.append({"role": "user", "content": transcript.text})

    # Generate a response from ChatGPT considering the conversation history
    response = generate_text(conversation_history)

    # Print and add the AI response to the conversation history
    #print("AI:" + response)
    conversation_history.append({"role": "assistant", "content": response})

    # Convert the response into actual usable python code
    item_list = eval(response)

    # Start building up the USDA file
    usda = """#usda 1.0
    (
        defaultPrim = "World"
        endTimeCode = 100
        metersPerUnit = 0.01
        startTimeCode = 0
        timeCodesPerSecond = 60
        upAxis = "Y"
    )

    def Xform "World"
    {
    """

    # Loop through all the page items in the document
    for i, item in enumerate(item_list):
        # Extract position and rotation
        position = item.position
        rotation = item.rotation

        usda += f'  def "{item.name}_{i}" (\n'
        usda += f'    prepend payload = @./{item.name}.usd@\n'
        usda += '  )\n'
        usda += '  {\n'
        usda += f'    float3 xformOp:rotateXYZ = (0, {rotation}, 0)\n'
        usda += '    float3 xformOp:scale = (1, 1, 1)\n'
        usda += f'    double3 xformOp:translate = ({position[0]}, 1, {-position[1]})\n'
        usda += '    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]\n'
        usda += '  }\n\n'

    # Close out the USDA file. (Copied from an Omniverse created stage.)
    usda += '}\n'
    usda += '\n'
    usda += 'def Xform "Environment"\n'
    usda += '{\n'
    usda += '    int ground:size = 5000\n'
    usda += '    string ground:type = "On"\n'
    usda += '    double3 xformOp:rotateXYZ = (0, 0, 0)\n'
    usda += '    double3 xformOp:scale = (1, 1, 1)\n'
    usda += '    double3 xformOp:translate = (0, 0, 0)\n'
    usda += '    uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]\n'
    usda += '\n'
    usda += '    def DomeLight "Sky" (\n'
    usda += '        prepend apiSchemas = ["ShapingAPI"]\n'
    usda += '    )\n'
    usda += '    {\n'
    usda += '        float inputs:colorTemperature = 6250\n'
    usda += '        bool inputs:enableColorTemperature = 1\n'
    usda += '        float inputs:exposure = 9\n'
    usda += '        float inputs:intensity = 1\n'
    usda += '        float inputs:shaping:cone:angle = 180\n'
    usda += '        float inputs:shaping:cone:softness\n'
    usda += '        float inputs:shaping:focus\n'
    usda += '        color3f inputs:shaping:focusTint\n'
    usda += '        asset inputs:shaping:ies:file\n'
    usda += '        asset inputs:texture:file = @https://omniverse-content-production.s3.us-west-2.amazonaws.com/Environments/2023_1/DomeLights/Indoor/small_hangar_01.hdr@\n'
    usda += '        token inputs:texture:format = "latlong"\n'
    usda += '        token visibility = "inherited"\n'
    usda += '        double3 xformOp:rotateXYZ = (270, 55.60000082850456, 0)\n'
    usda += '        double3 xformOp:scale = (1, 1, 1)\n'
    usda += '        double3 xformOp:translate = (0, 305, 0)\n'
    usda += '        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]\n'
    usda += '    }\n'
    usda += '\n'
    usda += '    def Scope "Looks"\n'
    usda += '    {\n'
    usda += '        def Material "Grid"\n'
    usda += '        {\n'
    usda += '            token outputs:mdl:displacement.connect = </Environment/Looks/Grid/Shader.outputs:out>\n'
    usda += '            token outputs:mdl:surface.connect = </Environment/Looks/Grid/Shader.outputs:out>\n'
    usda += '            token outputs:mdl:volume.connect = </Environment/Looks/Grid/Shader.outputs:out>\n'
    usda += '\n'
    usda += '            def Shader "Shader"\n'
    usda += '            {\n'
    usda += '                uniform token info:implementationSource = "sourceAsset"\n'
    usda += '                uniform asset info:mdl:sourceAsset = @OmniPBR.mdl@\n'
    usda += '                uniform token info:mdl:sourceAsset:subIdentifier = "OmniPBR"\n'
    usda += '                float inputs:albedo_add = 0\n'
    usda += '                float inputs:albedo_brightness = 0.52\n'
    usda += '                float inputs:albedo_desaturation = 1\n'
    usda += '                asset inputs:diffuse_texture = @https://omniverse-content-production.s3.us-west-2.amazonaws.com/Assets/Scenes/Templates/Default/SubUSDs/textures/ov_uv_grids_basecolor_1024.png@ (\n'
    usda += '                    colorSpace = "sRGB"\n'
    usda += '                    customData = {\n'
    usda += '                        asset default = @@\n'
    usda += '                    }\n'
    usda += '                )\n'
    usda += '                bool inputs:project_uvw = 0\n'
    usda += '                float inputs:reflection_roughness_constant = 0.333\n'
    usda += '                float inputs:texture_rotate = 0 (\n'
    usda += '                    customData = {\n'
    usda += '                        float default = 0\n'
    usda += '                    }\n'
    usda += '                )\n'
    usda += '                float2 inputs:texture_scale = (0.5, 0.5) (\n'
    usda += '                    customData = {\n'
    usda += '                        float2 default = (1, 1)\n'
    usda += '                    }\n'
    usda += '                )\n'
    usda += '                float2 inputs:texture_translate = (0, 0) (\n'
    usda += '                    customData = {\n'
    usda += '                        float2 default = (0, 0)\n'
    usda += '                    }\n'
    usda += '                )\n'
    usda += '                bool inputs:world_or_object = 0 (\n'
    usda += '                    customData = {\n'
    usda += '                        bool default = 0\n'
    usda += '                    }\n'
    usda += '                )\n'
    usda += '                token outputs:out (\n'
    usda += '                    renderType = "material"\n'
    usda += '                )\n'
    usda += '            }\n'
    usda += '        }\n'
    usda += '    }\n'
    usda += '\n'
    usda += '    def Mesh "ground" (\n'
    usda += '        prepend apiSchemas = ["MaterialBindingAPI"]\n'
    usda += '    )\n'
    usda += '    {\n'
    usda += '        float3[] extent = [(-1400, -1400, 0), (1400, 1400, 0)]\n'
    usda += '        int[] faceVertexCounts = [4]\n'
    usda += '        int[] faceVertexIndices = [0, 1, 3, 2]\n'
    usda += '        rel material:binding = </Environment/Looks/Grid> (\n'
    usda += '            bindMaterialAs = "weakerThanDescendants"\n'
    usda += '        )\n'
    usda += '        normal3f[] normals = [(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)] (\n'
    usda += '            interpolation = "faceVarying"\n'
    usda += '        )\n'
    usda += '        point3f[] points = [(-700, -700, 0), (700, -700, 0), (-700, 700, 0), (700, 700, 0)]\n'
    usda += '        bool primvars:isMatteObject = 0\n'
    usda += '        texCoord2f[] primvars:st = [(0, 0), (14, 0), (14, 14), (0, 14)] (\n'
    usda += '            interpolation = "faceVarying"\n'
    usda += '        )\n'
    usda += '        uniform token subdivisionScheme = "none"\n'
    usda += '        token visibility = "inherited"\n'
    usda += '        double3 xformOp:rotateXYZ = (0, -90, -90)\n'
    usda += '        double3 xformOp:scale = (1, 1, 1)\n'
    usda += '        double3 xformOp:translate = (0, 0, 0)\n'
    usda += '        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]\n'
    usda += '    }\n'
    usda += '\n'
    usda += '    def Plane "groundCollider" (\n'
    usda += '        prepend apiSchemas = ["PhysicsCollisionAPI"]\n'
    usda += '    )\n'
    usda += '    {\n'
    usda += '        uniform token axis = "Y"\n'
    usda += '        uniform token purpose = "guide"\n'
    usda += '    }\n'
    usda += '}\n'

    # Get the path of the current document

    # Create a new file object for the JSON file in the same directory
    usdaFilePath = f"C:/Users/janaa/Documents/NVIDIA_SIGGRAPHKeynote/scene.usda"

    # Open the file in write mode and write the text content to the file
    with open(usdaFilePath, "w") as usdaFile:
        usdaFile.write(usda)
if __name__ == "__main__":
    conversation_history = []

    # Create the main window
    root = tk.Tk()
    root.title("Audio Recorder and Transcriber")

    # Create and place the record button
    record_button = tk.Button(root, text="Record", command=start_recording)
    record_button.pack(pady=20)

    # Run the GUI event loop
    root.mainloop()
