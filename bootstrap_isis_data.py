from __future__ import annotations

import subprocess
from pathlib import Path

from candidate_backplanes import DEFAULT_DOCKER_IMAGE, DEFAULT_ISIS_DATA, docker_executable, download_file


S3_ROOT = "https://asc-isisdata.s3.us-west-2.amazonaws.com/usgs_data"
DIRECT_FILES = {
    "cassini/calibration/lut/lut.tab": f"{S3_ROOT}/cassini/calibration/lut/lut.tab",
    "base/spiceqldb.hdf": f"{S3_ROOT}/base/spiceqldb.hdf",
}
BASE_PATTERNS = ("kernels/lsk/**", "kernels/pck/**", "kernels/fk/**")


def main() -> None:
    docker = docker_executable()
    if not docker:
        raise RuntimeError("Docker is required. Build the ISIS image with .\\run.ps1 geometry-runtime first.")
    image = subprocess.run(
        [docker, "image", "inspect", DEFAULT_DOCKER_IMAGE],
        check=False,
        capture_output=True,
        text=True,
    )
    if image.returncode:
        raise RuntimeError(f"Docker image {DEFAULT_DOCKER_IMAGE} is missing. Run .\\run.ps1 geometry-runtime first.")

    data_dir = DEFAULT_ISIS_DATA.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, url in DIRECT_FILES.items():
        download_file(url, data_dir / Path(relative_path))

    for pattern in BASE_PATTERNS:
        subprocess.run(
            [
                docker,
                "run",
                "--rm",
                "--mount",
                f"type=bind,source={data_dir},target=/isisdata",
                DEFAULT_DOCKER_IMAGE,
                "downloadIsisData",
                "base",
                "/isisdata",
                f"--include={pattern}",
                "--transfers=4",
                "--checkers=8",
                "--stats-one-line",
            ],
            check=True,
        )
    print(f"ISIS base camera data are ready at {data_dir}")


if __name__ == "__main__":
    main()
