import os
import setuptools

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, "README.txt"), encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="table_ocr",
    version="0.2.5",
    author="Eric Ihli",
    author_email="eihli@owoga.com",
    description="Extract text from tables in images.",
    long_description=long_description,
    long_description_content_type="text/plain",
    url="https://github.com/eihli/image-table-ocr",
    packages=setuptools.find_packages(),
    package_data={
        "table_ocr": ["tessdata/table-ocr.traineddata", "tessdata/eng.traineddata"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pytesseract~=0.3", "opencv-python~=4.2", "numpy~=1.19", "requests>=2"],
    python_requires=">=3.6",
)
