import os
import yaml
import havesxs
import uuid
import hashlib
import base64
import tempfile
import tkinter as tk
from tkinter import filedialog
import subprocess

# FXEFqZQLNdyPGADgoUdluRUTzVkGUI/H7FOiuNUDjuk=
PUBLIC_KEY_TOKEN = "31bf3856ad364e35"
tempDir = None

# """"update"""", a term microsoft uses to describe literally 50 million things
class Update:
    def __init__(
        self,
        target_component,
        target_arch,
        version,
        copyright,
        registry_keys=None,
        files=None,
        version_scope="nonSxS",
        standalone="yes"
    ):
        self.identifier = hashlib.sha1(str(uuid.uuid4()).encode('ascii')).hexdigest()
        self.target_component = target_component
        self.target_arch = target_arch
        self.version = version
        self.copyright = copyright
        self.registry_keys = registry_keys
        self.files = files
        self.version_scope = version_scope
        self.public_key_token = PUBLIC_KEY_TOKEN
        self.standalone = standalone

    def generate_component_sxs(self):
        return havesxs.generate_sxs_name({
            "name": self.target_component,
            "culture": "none",
            "version": self.version,
            "publicKeyToken": self.public_key_token,
            "processorArchitecture": self.target_arch,
            "versionScope": self.version_scope,
        })

    def generate_component_manifest(self):
        global tempDir

        registry_entries = []
        if self.registry_keys:
            for registry_key in self.registry_keys:
                registry_values = []
                for registry_value in registry_key['values']:
                    registry_values.append(f"""<registryValue name="{registry_value['key']}" valueType="{registry_value['type']}" value="{registry_value['value']}" />""")
                registry_values = '\n'.join(registry_values)
                registry_entries.append(f"""<registryKey keyName="{registry_key['key_name']}" perUserVirtualization="{'Enable' if registry_key['perUserVirtualization'] else 'Disable'}">{registry_values}</registryKey>""")

        files_list = []
        files_entries = []
        if self.files:
            for file in self.files:
                if file.get('operation') == 'replace':
                    if tempDir == None:
                        tempDir = tempfile.mkdtemp()
                    
                    if file.get('text'):
                        text = file['text'].encode('utf-8')  # encode string to bytes using utf-8
                    else:
                        text = b'\x01'  # write 1 bit, needed for makecat to hash it

                    deletedFile = os.path.join(tempDir, file['file'])
                    with open(deletedFile, 'wb') as f:
                        f.write(text)
                    
                    filePath = deletedFile
                else:
                    filePath = file['file']

                try: 
                    with open(filePath, 'rb') as f:
                        dsig = base64.b64encode(hashlib.sha256(f.read()).digest()).decode()

                    files_entries.append(f"""<file name="{os.path.basename(filePath)}" destinationPath="{file['destination']}" importPath="$(build.nttree)\\"><asmv2:hash xmlns:asmv2="urn:schemas-microsoft-com:asm.v2" xmlns:dsig="http://www.w3.org/2000/09/xmldsig#"><dsig:Transforms><dsig:Transform Algorithm="urn:schemas-microsoft-com:HashTransforms.Identity" /></dsig:Transforms><dsig:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha256" /><dsig:DigestValue>{dsig}</dsig:DigestValue></asmv2:hash></file>""")
                    files_list.append(filePath)
                except FileNotFoundError:
                    print(f"{file['file']} specified not found.")

        registry_entries = "<registryKeys>" + "".join(registry_entries) + "</registryKeys>" if registry_entries else ""
        files_entries = "".join(files_entries) if files_entries else ""
        return [
            f"""<?xml version="1.0" encoding="utf-8" standalone="{self.standalone}"?><assembly xmlns="urn:schemas-microsoft-com:asm.v3" manifestVersion="1.0" copyright="{self.copyright}"><assemblyIdentity name="{self.target_component}" version="{self.version}" processorArchitecture="{self.target_arch}" language="neutral" buildType="release" publicKeyToken="{self.public_key_token}" versionScope="{self.version_scope}" />{registry_entries}{files_entries}</assembly>""",
            files_list
        ]

    def generate_update_sxs(self, culture="none"):
        return havesxs.generate_sxs_name({
            "name": self.identifier,
            "culture": culture,
            "version": self.version,
            "publicKeyToken": self.public_key_token,
            "processorArchitecture": self.target_arch,
            "versionScope": self.version_scope,
        })

    def generate_update_manifest(self, discoverable=False):
        return f"""<?xml version="1.0" encoding="utf-8" standalone="{self.standalone}"?><assembly xmlns="urn:schemas-microsoft-com:asm.v3" manifestVersion="1.0" copyright="{self.copyright}"><assemblyIdentity name="{self.identifier}" version="{self.version}" processorArchitecture="{self.target_arch}" language="neutral" buildType="release" publicKeyToken="{self.public_key_token}" versionScope="{self.version_scope}"/><deployment xmlns="urn:schemas-microsoft-com:asm.v3"/><dependency discoverable=\"{"true" if discoverable else "false"}\"><dependentAssembly dependencyType="install"><assemblyIdentity name="{self.target_component}" version="{self.version}" processorArchitecture="{self.target_arch}" language="neutral" buildType="release" publicKeyToken="{self.public_key_token}" versionScope="{self.version_scope}"/></dependentAssembly></dependency></assembly>"""


# Package Definition
class MicrosoftUpdateManifest:
    def __init__(self, package, copyright, version, target_arch, updates):
        self.package = package
        self.copyright = copyright
        self.version = version
        self.target_arch = target_arch
        self.public_key_token = PUBLIC_KEY_TOKEN
        self.updates = updates

    def generate_mum(self):
        mum = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?><assembly xmlns="urn:schemas-microsoft-com:asm.v3" manifestVersion="1.0" copyright="{self.copyright}"><assemblyIdentity name="{self.package}" version="{self.version}" processorArchitecture="{self.target_arch}" language="neutral" buildType="release" publicKeyToken="{self.public_key_token}"/><package identifier="{self.package}" releaseType="Feature Pack">"""
        mum += "".join(list(map(self.generate_mum_update, self.updates)))
        mum += "</package></assembly>"
        return mum

    def generate_mum_update(self, update):
        return f"""<update name="{update.identifier}"><component><assemblyIdentity name="{update.identifier}" version="{update.version}" processorArchitecture="{update.target_arch}" language="neutral" buildType="release" publicKeyToken="{update.public_key_token}" versionScope="{update.version_scope}"/></component></update>"""

def find_config_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_files = [f for f in os.listdir(script_dir) if f.startswith("cfg") and f.endswith(".yaml")]
    return cfg_files

def select_config_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title="Select Configuration File", filetypes=[("YAML files", "*.yaml")])
    return file_path

config_files = find_config_file()

if len(config_files) > 1:
    print("Multiple configuration files found. Please select one.")
    config_path = select_config_file()
elif len(config_files) == 1:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_files[0])
else:
    print("No configuration file found in the script's directory. Please select the path to your YAML configuration file.")
    config_path = select_config_file()

if config_path:
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: Configuration file not found. Please ensure the file path is correct.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Problem loading YAML file: {e}")
        exit(1)

# Staging Arena
staged_updates = []
staged_ddf = ["update.mum", "update.cat"]
staged_files = ["update.mum", "update.cat"]

for update in config["updates"] or []:
    update = Update(**update, copyright=config["copyright"])
    component_sxs = update.generate_component_sxs()
    update_sxs = update.generate_update_sxs()
    files = [f"{component_sxs}.manifest", f"{update_sxs}.manifest"] 

    with open(f".\\{component_sxs}.manifest", "w+") as f:
        component_manifest = update.generate_component_manifest()

        if component_manifest[1] != []:
            for file in component_manifest[1]:
                staged_ddf.append(f".Set DestinationDir={component_sxs}")
                staged_ddf.append(file)
                staged_files.append(file)

            staged_ddf.append(f".Set DestinationDir=")
        
        f.write(component_manifest[0])
    with open(f".\\{update_sxs}.manifest", "w+") as f:
        f.write(update.generate_update_manifest())
    staged_updates.append(update)
    staged_ddf.extend(files)
    staged_files.extend(files)

with open(".\\update.mum", "w+") as f:
    f.write(
        MicrosoftUpdateManifest(
            config["package"],
            config["copyright"],
            config["version"],
            config["target_arch"],
            staged_updates,
        ).generate_mum()
    )

with open(".\\files.txt", "w+") as f:
    f.write("\n".join(staged_ddf))

with open(".\\update.cdf", "w+") as f:
    f.write("""[CatalogHeader]
Name=update.cat
ResultDir=.\\
CatalogVersion=2
HashAlgorithms=SHA256

[CatalogFiles]
""")
    for (i, filename) in enumerate(filter(lambda f: f != "update.cat", staged_files)):
        f.write(f"<HASH>F{i+1}={filename}\n")

# Generate Thumbprint
print("To create a thumbprint, please run 'make-cert.ps1' as an administrator in PowerShell.")

thumbprint = input("Enter the thumbprint generated: ")

# Create PowerShell script code directly in Python
build_script = f"""param (
    [Parameter(Mandatory = $True)]
    [string]$Thumbprint,
    [string]$CabName
)

# Call build script with thumbprint
Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File .\\build.ps1 -Thumbprint {thumbprint} -CabName "{config['package']}{PUBLIC_KEY_TOKEN}{config['target_arch']}{config['version']}.cab"'
"""

with open("build-script.ps1", "w+") as f:
    f.write(build_script)

# Run PowerShell script in a separate window
subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "build-script.ps1", "-Thumbprint", thumbprint], creationflags=subprocess.CREATE_NEW_CONSOLE)

print("Processing complete. You may close this window.")
