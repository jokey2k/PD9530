from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name="pd9530",
    py_modules=["pd9530"],
    version="1.0.0",
    description="Library to interact with a PD9530 handheld scanner",
    author="Markus Ullmann",
    author_email="mail@markus-ullmann.de",
    url="http://github.com/jokey2k/PD9530",
    keywords=["scanner", "windows", "usb", "handheld"],
    license='BSD-3',
    install_requires=[
       'pyserial'
    ],
    platform="any",
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Handhelds/PDA's",
        "Environment :: Other Environment",
        "Environment :: Plugins",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: Customer Service",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Operating System :: Microsoft :: Windows :: Windows Server 2003",
        "Operating System :: Microsoft :: Windows :: Windows Server 2008",
        "Operating System :: Microsoft :: Windows :: Windows XP",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Terminals :: Serial",
        "Topic :: Utilities",
    ],
    long_description=readme(),
)
