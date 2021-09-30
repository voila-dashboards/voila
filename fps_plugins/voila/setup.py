from setuptools import setup, find_packages  # type: ignore

setup(
    name="fps_voila",
    version="0.0.1",
    packages=find_packages(),
    install_requires=["fps-kernels", "aiofiles"],
    entry_points={
        "fps_router": ["fps-voila = fps_voila.routes"],
        "fps_config": ["fps-voila = fps_voila.config"],
    },
)
