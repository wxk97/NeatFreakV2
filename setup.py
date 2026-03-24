from setuptools import setup

setup(
    app=["NeatFreak.py"],
    name="NeatFreak",
    options={"py2app": {
        "argv_emulation": False,
        "iconfile": "NeatFreak.icns",
        "plist": {
            "CFBundleName": "NeatFreak",
            "CFBundleDisplayName": "Neat Freak",
            "CFBundleIdentifier": "com.neatfreak.app",
            "CFBundleVersion": "1.0.0",
            "CFBundleIconFile": "NeatFreak",
            "NSHighResolutionCapable": True,
        },
    }},
    setup_requires=["py2app"],
)
